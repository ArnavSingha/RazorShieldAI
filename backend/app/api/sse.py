"""
RazorShield AI — Real-Time Event Notification Stream (SSE)
Exposes GET /api/v1/events/stream for broadcasting lightweight event notifications to the frontend.
Events carry metadata (event_id, event_type, resource_type, resource_id, timestamp, correlation_id).
The frontend uses SSE events to invalidate local state and refetch authoritative REST endpoints.
"""

import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Any, List
from fastapi import APIRouter, Header, Request
from starlette.responses import StreamingResponse

sse_router = APIRouter(tags=["Real-Time Operations"])

# Shared in-memory event bus
_EVENT_LISTENERS: List[asyncio.Queue] = []
_EVENT_HISTORY: List[Dict[str, Any]] = []
_MAX_EVENT_HISTORY = 100


def publish_system_event(
    event_type: str,
    resource_type: str,
    resource_id: str,
    correlation_id: str = "",
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Publishes a lightweight event notification to all active SSE listeners."""
    evt = {
        "event_id": f"evt_{int(time.time()*1000)}_{len(_EVENT_HISTORY)+1}",
        "event_type": event_type,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
        "sequence": len(_EVENT_HISTORY) + 1,
        "details": details or {},
    }
    _EVENT_HISTORY.append(evt)
    if len(_EVENT_HISTORY) > _MAX_EVENT_HISTORY:
        _EVENT_HISTORY.pop(0)

    for q in list(_EVENT_LISTENERS):
        try:
            q.put_nowait(evt)
        except asyncio.QueueFull:
            pass

    return evt


@sse_router.get("/api/v1/events/stream")
async def sse_event_stream(
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    """Streams Server-Sent Events (SSE) to connected clients with heartbeat and reconnection support."""

    async def event_generator() -> AsyncGenerator[str, None]:
        q: asyncio.Queue = asyncio.Queue(maxsize=50)
        _EVENT_LISTENERS.append(q)

        try:
            # Yield initial connection confirmation
            conn_evt = {
                "event_id": f"evt_init_{int(time.time())}",
                "event_type": "CONNECTED",
                "resource_type": "SYSTEM",
                "resource_id": "sse_stream",
                "timestamp": time.time(),
                "correlation_id": "",
                "sequence": 0,
            }
            yield f"id: {conn_evt['event_id']}\nevent: CONNECTED\ndata: {json.dumps(conn_evt)}\n\n"

            while True:
                if await request.is_disconnected():
                    break

                try:
                    # Wait for next event or heartbeat timeout (10s)
                    evt = await asyncio.wait_for(q.get(), timeout=10.0)
                    yield f"id: {evt['event_id']}\nevent: {evt['event_type']}\ndata: {json.dumps(evt)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat keeping connection alive
                    yield f": heartbeat {time.time()}\n\n"

        finally:
            if q in _EVENT_LISTENERS:
                _EVENT_LISTENERS.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
