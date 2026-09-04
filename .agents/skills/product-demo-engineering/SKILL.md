---
name: product-demo-engineering
description: Guidelines and best practices for building an unforgettable 5-minute judge demo experience for RazorShield AI Command Center.
---

# Product Demo Engineering Skill

## Core Objective
Ensure the final application interface and demo walkthrough can be understood by a hackathon judge in **under 60 seconds**, while demonstrating deep technical excellence and 0% fake metrics.

## Guidelines & Principles

1. **Visual Impact & Information Hierarchy:**
   - Dark-mode, high-contrast, premium enterprise aesthetic.
   - High-level KPIs at top (Transactions/sec, Risk Decisions, Active Investigations, Critical Incidents, Protected Exposure, **Unsafe Actions: 0**).
   - Real-time visual indicators for 7 system components (`Risk Engine`, `Graph Engine`, `Gemini`, `Redis`, `PostgreSQL`, `Audit`, `Gateway`).

2. **Core 5-Minute Demo Flow:**
   - **Step 1:** Open Command Center.
   - **Step 2:** Trigger `MULE_RING-003` attack scenario.
   - **Step 3:** Observe live risk spike on stream.
   - **Step 4:** Open Investigation Workspace.
   - **Step 5:** Interact with React Flow Graph cluster.
   - **Step 6:** Inspect grounded evidence (`E-1001`, `E-1003`, `E-1004`).
   - **Step 7:** View Gemini Agentic LLM reasoning & recommendation (`BLOCK`).
   - **Step 8:** View Deterministic Policy Engine override (`STEP_UP` due to customer history).
   - **Step 9:** Execute action and verify cryptographic ActionToken & state transition.
   - **Step 10:** Inspect SHA-256 chained audit lineage.
   - **Step 11:** Toggle `AUDIT_OFFLINE` in Chaos Lab.
   - **Step 12:** Run attack scenario under chaos mode $\rightarrow$ observe fail-closed `REJECTED` state and `unsafe_actions == 0`.

3. **No Fake Metrics & Transparent Provenance:**
   - All charts, tables, graph nodes, and audit logs are driven by real backend API endpoints.
   - Explicitly display provider modes (`GEMINI` vs `DETERMINISTIC_FALLBACK`).

4. **Product Navigation:**
   - `COMMAND CENTER`
   - `INVESTIGATIONS`
   - `SIMULATOR`
   - `AUDIT`
   - `POLICIES`
