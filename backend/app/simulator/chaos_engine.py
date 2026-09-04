"""
RazorShield AI — Chaos Engineering Controller
Thread-safe dependency failure injection engine supporting 7 fault types, TTL fault expiration,
mode selection (PRODUCTION_SIMULATION vs LOCAL_STANDALONE), RBAC protections, and audit logging.
"""

import threading
import time
from typing import Any, Dict, List, Optional

from backend.app.config import settings
from backend.app.domain.policy_contracts import UserRole
from backend.app.domain.simulator_contracts import (
    ChaosFaultType,
    ChaosStatus,
    SimulatorMode,
)
from backend.app.exceptions import RazorShieldError
from backend.app.policy.rbac import TrustedPrincipal, UnauthorizedRoleError


class ChaosDisabledError(RazorShieldError):
    """Raised when chaos toggles are attempted while CHAOS_MODE_ENABLED is False."""

    def __init__(self):
        super().__init__(
            message="Chaos Engineering API is disabled in production settings (CHAOS_MODE_ENABLED=False).",
            status_code=403,
            error_code="CHAOS_MODE_DISABLED",
            details={},
        )


class ChaosController:
    """Thread-Safe Chaos Controller for injecting dependency outages."""

    _lock = threading.Lock()
    _enabled: bool = getattr(settings, "chaos_mode_enabled", True)
    _mode: SimulatorMode = SimulatorMode.PRODUCTION_SIMULATION
    _active_faults: Dict[
        ChaosFaultType, float
    ] = {}  # fault -> expires_at (0 for no exp)
    _activated_by: str = "system"
    _activated_at: Optional[float] = None

    @classmethod
    def set_chaos_mode(cls, mode: SimulatorMode) -> None:
        with cls._lock:
            cls._mode = mode

    @classmethod
    def get_status(cls) -> ChaosStatus:
        """Returns active chaos status, filtering out expired faults."""
        with cls._lock:
            now = time.time()
            active: List[ChaosFaultType] = []
            for fault, exp in list(cls._active_faults.items()):
                if exp > 0 and now > exp:
                    del cls._active_faults[fault]
                else:
                    active.append(fault)

            return ChaosStatus(
                enabled=cls._enabled,
                mode=cls._mode,
                active_faults=active,
                activated_by=cls._activated_by,
                activated_at=cls._activated_at,
                expires_at=max(
                    [e for e in cls._active_faults.values() if e > 0], default=None
                ),
            )

    @classmethod
    def toggle_fault(
        cls,
        fault: ChaosFaultType,
        enable: bool,
        principal: TrustedPrincipal,
        ttl_seconds: Optional[float] = 60.0,
        audit_logger: Optional[Any] = None,
    ) -> ChaosStatus:
        """
        Protected chaos toggle API.
        Requires CHAOS_MODE_ENABLED=True and ADMIN/RISK_ANALYST role.
        Appends toggle event to cryptographic audit ledger.
        """
        if not cls._enabled:
            raise ChaosDisabledError()

        if principal.role not in (UserRole.ADMIN, UserRole.RISK_ANALYST):
            raise UnauthorizedRoleError(
                principal_id=principal.principal_id,
                role=principal.role.value,
                action=f"TOGGLE_CHAOS_{fault.value}",
            )

        with cls._lock:
            now = time.time()
            cls._activated_by = principal.principal_id
            cls._activated_at = now

            if enable:
                exp = (now + ttl_seconds) if ttl_seconds else 0.0
                cls._active_faults[fault] = exp
            else:
                cls._active_faults.pop(fault, None)

        status = cls.get_status()

        if audit_logger and hasattr(audit_logger, "append_event"):
            audit_logger.append_event(
                decision_id=f"CHAOS-{fault.value}",
                transaction_id="CHAOS_SYSTEM",
                payload_dict={
                    "fault": fault.value,
                    "action": "ENABLE" if enable else "DISABLE",
                    "principal_id": principal.principal_id,
                    "ttl_seconds": ttl_seconds,
                    "timestamp": now,
                },
            )

        return status

    @classmethod
    def is_fault_active(cls, fault: ChaosFaultType) -> bool:
        """Checks if a fault is currently active and not expired."""
        with cls._lock:
            if fault not in cls._active_faults:
                return False
            exp = cls._active_faults[fault]
            if exp > 0 and time.time() > exp:
                del cls._active_faults[fault]
                return False
            return True

    @classmethod
    def reset_all_faults(cls) -> None:
        """Clears all active faults for test isolation."""
        with cls._lock:
            cls._active_faults.clear()
            cls._activated_at = None
