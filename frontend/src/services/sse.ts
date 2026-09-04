export type ConnectionState = 'CONNECTED' | 'DEGRADED' | 'RECONNECTING' | 'OFFLINE' | 'RECOVERED';

export interface SystemEventPayload {
  event_id: string;
  event_type: string;
  resource_type: string;
  resource_id: string;
  timestamp: number;
  correlation_id: string;
  sequence: number;
  details?: Record<string, any>;
}

type EventListener = (event: SystemEventPayload) => void;
type StateChangeListener = (state: ConnectionState, latencyMs?: number) => void;

class RealtimeEventStreamService {
  private eventSource: EventSource | null = null;
  private connectionState: ConnectionState = 'OFFLINE';
  private lastEventId: string | null = null;
  private reconnectAttempts = 0;
  private eventListeners: Set<EventListener> = new Set();
  private stateListeners: Set<StateChangeListener> = new Set();
  private reconnectTimer: any = null;
  private lastPingTimestamp: number = Date.now();

  constructor() {
    // Auto-connect on load
    this.connect();
  }

  public connect() {
    if (this.eventSource) {
      this.eventSource.close();
    }

    this.updateState('RECONNECTING');
    const startTime = Date.now();

    try {
      this.eventSource = new EventSource('/api/v1/events/stream');

      this.eventSource.onopen = () => {
        const latency = Date.now() - startTime;
        this.reconnectAttempts = 0;
        this.lastPingTimestamp = Date.now();
        this.updateState(this.connectionState === 'RECONNECTING' ? 'RECOVERED' : 'CONNECTED', latency);
        setTimeout(() => {
          if (this.connectionState === 'RECOVERED') {
            this.updateState('CONNECTED', latency);
          }
        }, 3000);
      };

      this.eventSource.onmessage = (evt) => {
        this.lastPingTimestamp = Date.now();
        try {
          const payload: SystemEventPayload = JSON.parse(evt.data);
          if (evt.lastEventId) {
            this.lastEventId = evt.lastEventId;
          }
          this.notifyListeners(payload);
        } catch {
          // Heartbeat or ping
        }
      };

      this.eventSource.addEventListener('CONNECTED', (evt: any) => {
        this.lastPingTimestamp = Date.now();
      });

      this.eventSource.onerror = () => {
        this.eventSource?.close();
        this.eventSource = null;
        this.handleReconnect();
      };
    } catch {
      this.handleReconnect();
    }
  }

  private handleReconnect() {
    this.reconnectAttempts++;
    if (this.reconnectAttempts > 5) {
      this.updateState('OFFLINE');
    } else {
      this.updateState('RECONNECTING');
    }

    const backoffDelay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 15000);
    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, backoffDelay);
  }

  private updateState(newState: ConnectionState, latencyMs?: number) {
    this.connectionState = newState;
    this.stateListeners.forEach((fn) => fn(newState, latencyMs));
  }

  private notifyListeners(evt: SystemEventPayload) {
    this.eventListeners.forEach((fn) => fn(evt));
  }

  public subscribeEvents(listener: EventListener): () => void {
    this.eventListeners.add(listener);
    return () => this.eventListeners.delete(listener);
  }

  public subscribeState(listener: StateChangeListener): () => void {
    this.stateListeners.add(listener);
    listener(this.connectionState);
    return () => this.stateListeners.delete(listener);
  }

  public getConnectionState(): ConnectionState {
    return this.connectionState;
  }
}

export const realtimeStream = new RealtimeEventStreamService();
