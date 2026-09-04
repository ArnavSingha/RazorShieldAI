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
- Product Spec: [PRODUCT_SPEC.md](product/PRODUCT_SPEC.md)
- Architecture: [ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- Failure Recovery: [FAILURE_RECOVERY.md](architecture/FAILURE_RECOVERY.md)
- Security Model: [SECURITY_MODEL.md](security/SECURITY_MODEL.md)
- Threat Model: [THREAT_MODEL.md](threat-model/THREAT_MODEL.md)
- AI Safety: [AI_SAFETY.md](ai-safety/AI_SAFETY.md)
- Data Model: [DATA_MODEL.md](data-model/DATA_MODEL.md)
- API Contract: [API_CONTRACT.md](api/API_CONTRACT.md)
- Test Strategy: [TEST_STRATEGY.md](testing/TEST_STRATEGY.md)
- Evaluation Plan: [EVALUATION_PLAN.md](evaluation/EVALUATION_PLAN.md)
- UX Spec: [UX_SPEC.md](product/UX_SPEC.md)
- Review Checklist: [REVIEW_CHECKLIST.md](review/REVIEW_CHECKLIST.md)

