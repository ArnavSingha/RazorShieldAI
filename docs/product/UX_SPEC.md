# RazorShield AI — UX & Design System Specification

## Design Philosophy & Aesthetics
- **Theme:** Slate / Dark Mode (`bg-zinc-950`, `text-zinc-100`, `border-zinc-800`).
- **Typography:** Inter / Geist Mono for high legibility numerical data.
- **Vibe:** Tier-1 Risk Intelligence Console (Razorpay / Stripe Radar level density & polish).
- **Zero Decorative Noise:** Clean micro-badges, clear status accents:
  - `ALLOW` / Low Risk: Emerald (`#10B981`)
  - `MONITOR` / Medium Risk: Cyan (`#06B6D4`)
  - `STEP-UP` / Elevated Risk: Amber (`#F59E0B`)
  - `HOLD` / High Risk: Orange (`#EA580C`)
  - `BLOCK` / Critical Risk: Crimson (`#EF4444`)

---

## Workspace Layout Hierarchy

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ HEADER: RazorShield AI | System Health: GREEN | Stream: RUNNING (120 tx/m) | Role: ADMIN│
├───────────────────┬─────────────────────────────────────────────┬───────────────────────┤
│ NAVIGATION        │ MAIN WORKSPACE PANEL                        │ SIDEBAR / TRACE       │
│                   │                                             │                       │
│ 📊 Command Center │ [Tab: Live Stream | Investigation | Graph]  │ 🤖 Agent Trace        │
│ ⚡ Live Stream    │                                             │                       │
│ 🔎 Investigation  │  ┌───────────────────────────────────────┐  │ - Triage: PASSED      │
│ 🕸️ Entity Graph   │  │ Transaction Stream Table /            │  │ - Tools Executed: 3   │
│ ⚖️ Policy Center  │  │ Active Incident Graph Visualization   │  │ - Confidence: 94%     │
│ 🛡️ Security Audit │  │                                       │  │ - Evidence Links: 4   │
│ 🧪 Simulator Mode │  └───────────────────────────────────────┘  │                       │
│ 💥 Chaos Mode     │                                             │ [Action: STEP-UP]     │
└───────────────────┴─────────────────────────────────────────────┴───────────────────────┘
```

---

## Key Screen Designs

### 1. Command Center
- KPI Grid (Transactions/min, Active Incidents, Total Prevented Loss, False Positive Rate, Latency p95).
- Real-time incident alert feed.

### 2. Live Transaction Stream
- Dense, auto-scrolling streaming table with live risk score indicators, contributing signal pills, decision column, and instant "Investigate" action button.

### 3. Investigation Workspace
- Splittable layout: Left panel showing transaction metadata & customer baseline; center panel showing graph node clusters; right panel displaying AI agent trace step-by-step reasoning & evidence citations.

### 4. Interactive Transaction & Entity Graph
- Rendered with React Flow. Node types: Customer (Blue), Account (Indigo), Device (Purple), Card Token (Amber), IP (Teal), Merchant (Emerald). Node links show relationship weight and shared account count.
