# RazorShield AI — Architectural Decision Record (ADR) Index

## Registered Architectural Decision Records

| ADR ID | Title | Status | Date | Decision Summary |
| :--- | :--- | :--- | :--- | :--- |
| **[ADR-001](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/decisions/ADR-001.md)** | Modular Monolith vs Microservices Architecture | Accepted | 2026-08-23 | Selected FastAPI + Next.js modular monolith to eliminate network serialization latency and maximize engineering signal. |
| **[ADR-002](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/decisions/ADR-002.md)** | NetworkX In-Memory Graph Processing | Accepted | 2026-08-23 | Selected NetworkX over Neo4j/TigerGraph for sub-25ms cluster analysis without operational external database overhead. |
| **[ADR-003](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/decisions/ADR-003.md)** | Hybrid Risk Matrix (Rules + ML + Graph) vs LLM-Only | Accepted | 2026-08-23 | Enforced deterministic rules + ML anomaly detection as primary scoring engine; reserved LLM exclusively for out-of-band investigation. |
| **[ADR-004](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/decisions/ADR-004.md)** | State Machine Agent Framework (LangGraph) | Accepted | 2026-08-23 | Selected explicit state transitions over unconstrained autonomous loops to guarantee inspectability and evidence grounding. |
| **[ADR-005](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/decisions/ADR-005.md)** | Policy Engine & Action Gateway Isolation | Accepted | 2026-08-23 | Stripped LLM of direct action execution privileges; all actions require signed Policy authorization tokens. |
| **[ADR-006](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/decisions/ADR-006.md)** | Least-Privilege Agent Tool Contracts | Accepted | 2026-08-23 | Defined strict read-only vs high-impact request tool boundaries with schema validation on all inputs/outputs. |
