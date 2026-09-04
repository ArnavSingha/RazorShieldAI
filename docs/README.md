# RazorShield AI — Canonical System Documentation Directory

> **AUTHORITATIVE NOTICE:** The nested domain documentation tree below is the single source of truth for all RazorShield AI product, architectural, security, and testing specifications.

---

## Canonical Documentation Map

```text
docs/
├── README.md                          # Documentation Root Index (This File)
├── PROJECT_ROADMAP.md                 # Development Timeline & Slice Milestones
├── ADR_INDEX.md                       # Index of Architectural Decision Records
│
├── product/                           # Product Management & UX
│   ├── PRODUCT_SPEC.md                # Primary Product Positioning & SLAs
│   ├── UX_SPEC.md                     # Dark Mode Design System & Screen Layouts
│   └── DEMO_SCRIPT.md                 # 12-Scene 5-Minute Demonstration Script
│
├── architecture/                      # Technical Architecture & Systems Design
│   ├── ARCHITECTURE.md                # System Architecture, Storage Stack & Latency Targets
│   ├── AGENT_DESIGN.md                # LangGraph Agent State Machine & Tool Contracts
│   └── FAILURE_RECOVERY.md            # Dependency Failure Fallbacks & Resilience Circuit Breakers
│
├── security/                          # Security Model & RBAC
│   └── SECURITY_MODEL.md              # Role-Based Access Control & Action Gateway Authorization
│
├── threat-model/                      # Threat Modeling
│   └── THREAT_MODEL.md                # STRIDE Matrix & Trust Boundary Specifications
│
├── ai-safety/                         # AI Safety & Guardrails
│   └── AI_SAFETY.md                   # Prompt Injection Defense & Evidence Grounding Schema
│
├── data-model/                        # Data Engineering & Schemas
│   └── DATA_MODEL.md                  # Entity Schemas, Risk Formula & Reason Codes
│
├── api/                               # API Contracts
│   └── API_CONTRACT.md                # REST & SSE Event Streaming API Contracts
│
├── testing/                           # Quality Assurance Strategy
│   └── TEST_STRATEGY.md               # Unit, Integration, Security, and Resilience Test Framework
│
├── evaluation/                        # System Benchmarking
│   └── EVALUATION_PLAN.md             # Benchmark Suite & Accuracy Metrics
│
├── review/                            # Engineering Review & Quality Assurance
│   └── REVIEW_CHECKLIST.md            # Comprehensive Senior Engineering Review Checklist
│
└── decisions/                         # Architectural Decision Records (ADRs)
    ├── ADR-001.md                     # Modular Monolith vs Microservices
    ├── ADR-002.md                     # NetworkX In-Memory Graph Processing
    ├── ADR-003.md                     # Hybrid Risk Matrix vs LLM-Only Scoring
    ├── ADR-004.md                     # State Machine Agent Framework
    ├── ADR-005.md                     # Policy Engine & Action Gateway Isolation
    └── ADR-006.md                     # Least-Privilege Agent Tool Contracts
```

---

## Document Cross-Link Index
- Product Spec: [docs/product/PRODUCT_SPEC.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/product/PRODUCT_SPEC.md)
- Architecture: [docs/architecture/ARCHITECTURE.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/architecture/ARCHITECTURE.md)
- Failure Recovery: [docs/architecture/FAILURE_RECOVERY.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/architecture/FAILURE_RECOVERY.md)
- Security Model: [docs/security/SECURITY_MODEL.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/security/SECURITY_MODEL.md)
- Threat Model: [docs/threat-model/THREAT_MODEL.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/threat-model/THREAT_MODEL.md)
- AI Safety: [docs/ai-safety/AI_SAFETY.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/ai-safety/AI_SAFETY.md)
- Data Model: [docs/data-model/DATA_MODEL.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/data-model/DATA_MODEL.md)
- API Contract: [docs/api/API_CONTRACT.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/api/API_CONTRACT.md)
- Test Strategy: [docs/testing/TEST_STRATEGY.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/testing/TEST_STRATEGY.md)
- Evaluation Plan: [docs/evaluation/EVALUATION_PLAN.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/evaluation/EVALUATION_PLAN.md)
- UX Spec: [docs/product/UX_SPEC.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/product/UX_SPEC.md)
- Review Checklist: [docs/review/REVIEW_CHECKLIST.md](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/review/REVIEW_CHECKLIST.md)
