# Phase 5F — Final System Architecture

**Date:** 2026-09-14
**Scope:** Translate the approved Phase 5D (mathematical decision model) and Phase 5E (group formation) specifications into an implementable software blueprint. No code is written. Phase 2A/2B/5D/5E mathematics is not redesigned. This document builds directly on the module list and technology analysis already produced in `research/phase3_system_architecture.md`, refining it where Phases 5A–5E have since made it more precise — it does not discard that earlier work.

---

## 1. System Scope and Boundaries

**What the system does**, stated as one question, per this phase's own framing: *given vendors, a commodity, demand estimates, prices, and procurement constraints, should compatible vendors procure collaboratively — and if not now, why, and could that change?*

**What the system explicitly does NOT do:**

| Non-goal | Why (traced to a specific prior finding) |
|---|---|
| Real-time demand forecasting | No trained demand model exists or is justified (Phase 5C, Section 12 verdict: ML not justified for current data) |
| Automatic ML training or retraining | The one ML experiment this project ran (Potato price forecasting) is closed; it must not be reopened, and no other ML training is introduced (Phase 4C, Phase 5A) |
| Guaranteeing market prices | Any price used is a realized, observed figure, never a promise about the future (Phase 5D, Section 1) |
| Vehicle-routing optimization | Explicitly rejected as disproportionate to a single-collection-point design (Phase 2A Part 28, Phase 2B Part 4/Row on VRP) |
| Fabricating missing information | Missing critical data routes to `ABSTAIN`, never a substituted value (Phase 5D Section 9, Phase 5E Sections 4/13) |
| Autonomous order placement | The system is decision support only — it recommends, a human (anchor vendor or trader) acts (Phase 2A, Part 4) |
| Multi-commodity bundled transport, MOQ negotiation, real-time re-optimization | All explicitly out of V1 scope already (Phase 2A Part 30) — not revisited here |

## 2. Authoritative Dependency Map

**One rule per concern, one authoritative source — nothing below is defined twice.**

```
INPUTS (vendor data, commodity params, prices)
        |  [Phase 5E §2-3: vendor universe, procurement context]
        v
DATA VALIDATION & ELIGIBILITY
        |  [Phase 5E §4: eligibility filter -- owns ABSTAIN trigger conditions]
        v
DEMAND ESTIMATION
        |  [Phase 5C §6-7 + Phase 5D §3: q_i hierarchy -- cold-start / baseline / (unused) ML slot]
        v
GROUP FORMATION (Stage 1)
        |  [Phase 2B (preserved) + Phase 5E §5-7: compatibility graph, connected components,
        |   within-pool candidate enumeration]
        v
DECISION MODEL (Stage 2)
        |  [Phase 5D §4-9: Q_G, MOQ, geography, freshness, costs, savings, objective --
        |   the SOLE authority for every mathematical constraint and formula]
        v
DECISION STATES
        |  [Phase 5D §9 + Phase 5E §12-13: BUY_TOGETHER / WAIT_OR_EXPAND_GROUP /
        |   DO_NOT_BUY_TOGETHER / ABSTAIN -- fixed evaluation order, mutually exclusive]
        v
OVERLAP RESOLUTION / FINAL SELECTION
        |  [Phase 2B Part 11-12 (preserved) + Phase 5E §9-11: lexicographic objective,
        |   weighted set packing]
        v
EXPLANATION / OUTPUT
        [research/phase3_system_architecture.md §16 (template-based explanation, preserved) +
         Phase 5F §6-7 below: structured output contract]
```

**Authoritative-source table**, so no future implementer has to guess which document to consult:

| Rule category | Authoritative source | Nothing else may redefine it |
|---|---|---|
| Vendor/commodity/context definitions | Phase 5E, Sections 2–3 | — |
| Eligibility / ABSTAIN triggers | Phase 5E, Sections 4, 13 | — |
| Demand estimate ($q_i$) provenance hierarchy | Phase 5C, Sections 6–7; formalized in Phase 5D, Section 3 | — |
| Pairwise compatibility | Phase 2B, Part 6B (unchanged); restated in Phase 5E, Section 5 | — |
| Candidate generation algorithm | Phase 2B, Part 15 Steps 0–3 (unchanged); restated in Phase 5E, Section 6 | — |
| Cost, MOQ, freshness, geography, savings formulas | Phase 5D, Sections 4–8 | — |
| Decision-state definitions and ordering | Phase 5D, Section 9; extended at group-formation level in Phase 5E, Sections 12–13 | — |
| Objective function / overlap resolution | Phase 2B, Parts 11–12 (unchanged); restated in Phase 5E, Sections 9–10 | — |
| Explanation template style | `research/phase3_system_architecture.md`, Section 16 (preserved, extended to four states in Phase 5F §6 below) | — |

## 3. Final Module Architecture

**Starting point: Phase 3's original 12-module list.** Formalized here into the minimal set actually needed, merging or renaming where Phases 5A–5E's added precision requires it — nothing is kept merely because it was proposed earlier, and nothing is added merely because it sounds complete.

| # | Final module | Merged/renamed from | Responsibility |
|---|---|---|---|
| 1 | **Input/Data Module** | Phase 3 Modules 1–4 (Vendor Registration, Commodity/Demand Mgmt, Location Mgmt, Price Data) merged — these are all "get data in," not decision logic | Accept and store vendor, commodity, and price records exactly as submitted |
| 2 | **Data Validation & Eligibility Module** | New name for Phase 3's implicit validation step, now formalized per Phase 5E §4 | Check every required field exists and is usable; route failures to `ABSTAIN` |
| 3 | **Demand Estimation Module** | Phase 3 Module 5 ("Cold-Start Demand Estimation"), renamed and widened | Produce $q_i$ via Phase 5C/5D's full hierarchy (cold-start / baseline — never ML for the current project), tagged with its provenance |
| 4 | **Group Formation Engine** | Phase 3 Module 6 | Build the compatibility graph, decompose into pools, enumerate within-pool candidates (Phase 2B, unchanged) |
| 5 | **Procurement Decision Engine** | Phase 3 Modules 7 & 8 (already merged there), now updated to Phase 5D's four-state output | Evaluate one candidate group against every Phase 5D constraint and formula; return one of the four decision states |
| 6 | **Overlap Resolution / Final Selector** | Phase 3 Module 9 | Exact weighted set packing over `BUY_TOGETHER`-eligible candidates (Phase 2B Parts 11–12) |
| 7 | **Abstention Handler** | New — did not exist as a named module in Phase 3, because `ABSTAIN` did not exist yet | Collect every `ABSTAIN` event (from Module 2 or Module 5) with its specific reason; ensure no downstream module ever receives or fabricates a value for an abstained vendor |
| 8 | **Explanation Generator** | Phase 3 Module 10 ("Recommendation Engine"), renamed for clarity, absorbing Phase 3 Section 16's template design | Assemble the structured, human-readable explanation for any of the four states, using only already-computed values (template-based, never generative) |
| 9 | **Results Interface** | Phase 3 Module 11 ("Vendor Dashboard") | Present the Explanation Generator's output — a presentation concern, not a decision concern (Section 12 below) |
| 10 | **Run Logging / Feedback Module** | Phase 3 Module 12 | Persist every run's inputs, decisions, and (if collected) vendor feedback, for reproducibility |

**Not kept as a separate module:** a standalone "Decision/Method Selector" (this phase's own suggested list) — its one real job, choosing `BASELINE` vs. `ML_MODEL` vs. `NO_FORECAST` for a *forecasting* signal (Phase 5A, Section 4), is not part of the procurement decision pipeline at all (Phase 5D, Section 1 reconciliation: the decision model never consumed a forecast). If a future, separate decision-insight display layer is ever built (Phase 3A.1's deferred concept), it would be its own small module outside this pipeline, not folded in here to avoid implying the core decision depends on it.

**Per-module specification:**

| Module | Inputs | Outputs | Depends on | Owns | Must NOT own |
|---|---|---|---|---|---|
| 1. Input/Data | Raw vendor/commodity/price submissions | Stored records | — (leaf) | Storage of raw submitted values, unmodified | Any validation logic, any decision logic |
| 2. Validation & Eligibility | Stored records for one $(c,t)$ context | $V_c^{elig}$, or `ABSTAIN` events for excluded vendors | Module 1 | The exact eligibility checks of Phase 5E §4 | Compatibility, cost math, or decision-state logic beyond `ABSTAIN` itself |
| 3. Demand Estimation | Vendor's own data + peer records | $q_i$ + provenance tag | Module 1, 2 | The cold-start/baseline hierarchy (Phase 5C §6–7) | Any trained model; any claim of "prediction" |
| 4. Group Formation | $V_c^{elig}$ + locations | Candidate groups (possibly overlapping) | Module 2, 3 | Compatibility graph, connected components, subset enumeration (Phase 2B) | Cost/savings math, decision states |
| 5. Procurement Decision | One candidate group + parameters | One of 4 decision states + full numeric trace | Module 4 | Every Phase 5D formula and constraint | Group generation, final selection |
| 6. Overlap Resolution | All `BUY_TOGETHER`-eligible candidates for one $(c,t)$ | Selected, disjoint groups | Module 5 | The lexicographic objective and set-packing solve (Phase 2B) | Re-evaluating any candidate's feasibility |
| 7. Abstention Handler | `ABSTAIN` events from Modules 2 & 5 | Consolidated abstention records with reasons | Module 2, 5 | Ensuring `ABSTAIN` is never silently dropped or converted into a guess | Any numeric estimation |
| 8. Explanation Generator | Decision states + numeric traces (Modules 5–7) | Structured explanation text per Section 6 | Module 5, 6, 7 | Template selection and filling (Phase 3 §16, preserved) | Any new calculation |
| 9. Results Interface | Explanation Generator output | Rendered display | Module 8 | Presentation only | Any authoritative decision (Section 12) |
| 10. Run Logging | Every run's inputs and outputs | Persisted audit trail | All | Immutable record-keeping | Any decision logic |

## 4. End-to-End Data Flow

**Verified against Phase 5D/5E — one correction made, explained below.**

```
User/Data Input
      |
      v
Input Validation & Eligibility  --[missing critical field]--> ABSTAIN (per-vendor, Phase 5E §4)
      |  (vendor passes)
      v
Demand Estimation (q_i, tagged provenance)
      |
      v
Commodity Partitioning (V_c, one commodity at a time -- Phase 5D §3)
      |
      v
Geographic Compatibility Graph (2*D_max threshold -- Phase 2B Part 6B)
      |
      v
Candidate Group Generation (connected components -> within-pool subsets -- Phase 2B Part 15)
      |
      v
Phase 5D Decision Evaluation  (per candidate: MOQ, geography, freshness, cost, savings)
      |
      v
Decision State  (BUY_TOGETHER / WAIT_OR_EXPAND_GROUP / DO_NOT_BUY_TOGETHER / ABSTAIN)
      |
      v
Overlap Resolution  (ONLY among BUY_TOGETHER-eligible candidates -- Phase 2B Parts 11-12)
      |
      v
Explanation
      |
      v
Structured Result
```

**One correction to this phase's suggested sequence, required by the authoritative specifications:** the brief's example puts "Overlap Resolution" *before* "Phase 5D Decision Evaluation." **This order is reversed here, and must be**, because Phase 2B's own design (Part 2, restated in Phase 5E §10) requires every candidate to be independently evaluated *first*; overlap is resolved only *among the results* of that evaluation (specifically, only among candidates that reached `BUY_TOGETHER`). Resolving overlap before evaluation would force a choice between conflicting candidates before either candidate's value is even known — exactly the mistake Phase 2B Part 2 explicitly warns against. This is the one point at which this phase's own sketch needed correcting to match the authoritative source, per this phase's own Step 4 instruction.

## 5. Input Contract, 6. Output Contract, 7. Module Interfaces, 8. Validation/Error Routing, 9. Decision-State Routing

**Specified in full in the companion document `reports/phase5f_module_interfaces.md`** — kept there rather than duplicated here, so this document stays focused on architecture and that one stays focused on contracts, per this phase's own instruction not to duplicate conflicting (or, here, simply redundant) definitions across documents.

## 10. Parameter Management

| Parameter | Classification | Enters system at | Consumed by | Validation requirement |
|---|---|---|---|---|
| $D_{max}$ | D. Configurable prototype parameter | System configuration | Group Formation Engine, Procurement Decision Engine | Must be a positive number; no substitute if absent — the system cannot run without it, so it is a startup requirement, not a per-request one |
| $MOQ_c$ | B. User-provided (if a trader confirms it), otherwise **not present at all** | Commodity configuration, per commodity | Procurement Decision Engine | If absent for a commodity, the MOQ constraint is simply not applied for that commodity (Phase 2A Part 18) — never defaulted to zero or any other value |
| $F_c$ | C. Real external data (scientific component) / D. Configurable (trader-triangulated component) | Commodity configuration | Procurement Decision Engine | Must be present and positive for any commodity the system evaluates; sourced and labeled per Phase 5D §6 |
| $H_{i,c}$ | B. User-provided (vendor-declared) / A. Dynamic input (purchase-frequency proxy, computed from other user-provided data) | Vendor registration/demand entry | Demand Estimation, Procurement Decision Engine | If neither the direct value nor the proxy exists, the vendor fails eligibility (Phase 5E §4) — not defaulted |
| $p^{ind}_{i,c}$ | B. User-provided | Vendor demand entry | Procurement Decision Engine | Must be a positive ₹/kg figure |
| $p^{wh}_{c,t}$ | C. Real external data (data.gov.in current-daily-price snapshot, Phase 5D §1/B1) | Daily price ingestion | Procurement Decision Engine | Must be dated $t$ and tagged with its `geographic_level` (Phase 5D §4a); if unavailable for date $t$, the run for that $(c,t)$ context `ABSTAIN`s rather than reusing a stale price |
| $m$ (trader margin) | D. Configurable prototype parameter (sensitivity range $\{0, 0.10, 0.15\}$) | System configuration | Procurement Decision Engine | Must be reported as a labeled sensitivity variant, never presented as a single asserted fact (Phase 2A Part 7) |
| $TC(\text{tier})$ | C. Real external data (rate bands) / D. Configurable (exact tier cutoffs) | System configuration | Procurement Decision Engine | Rate bands sourced from Phase 1B's commercial-listing research; cutoffs flagged as provisional |
| $q_i$ | A. Dynamic input (derived per-request from B/C below) — never itself hardcoded | Demand Estimation Module | Group Formation Engine, Procurement Decision Engine | Must carry a provenance tag (`ESTIMATE — cold-start` / `ESTIMATE — baseline`); `PREDICTION — ML` is a defined but currently **unused** slot (Phase 5C §12) |
| $L_i$ | B. User-provided | Vendor registration | Group Formation Engine | Must be a valid coordinate pair; no geocoding is performed (Phase 3 §14, preserved) |

**No parameter above is hardcoded as an unsupported real-world constant.** Every provisional value ($D_{max}$, $m$, tier cutoffs) is explicitly labeled configurable, per this phase's own instruction, and every value with no confirmed source (a given vendor's $H_{i,c}$, a given commodity's $MOQ_c$) has a defined "absent" behavior that is never a fabricated substitute.

## 11. External Data Boundary

**Only one genuinely external data source exists in this architecture: the daily wholesale price $p^{wh}_{c,t}$** (via the data.gov.in current-daily-price snapshot, per Phase 5D's reconciliation). Everything else (vendor data, commodity configuration, parameters) is user-provided or system-configured, not pulled from an external live source.

**If $p^{wh}_{c,t}$ is unavailable for date $t$:** the system does **not** fabricate a price, does **not** silently reuse yesterday's price as if it were today's, and does **not** ask the vendor to supply a wholesale price (that is not information a street vendor would have). **It abstains for that $(c,t)$ context entirely** — every candidate group evaluation for that commodity/date returns `ABSTAIN`, with the explicit reason "current wholesale price unavailable for this date." **Retrieval itself is not implemented in this phase** — this section defines the required *behavior on failure*, not the retrieval mechanism (Phase 5D §14 already flags automated retrieval as unverified, a Phase 5E/5F-and-beyond item, not assumed working).

**User-entered demand ($q_i$'s survey/diary-sourced component)** is not "external data" in the same sense — it is a direct user input, validated by Module 2, never silently substituted if missing (Section 8, companion document).

## 12. Frontend/Backend Responsibility Boundary

| Belongs to Backend/Core Logic | Belongs to Frontend |
|---|---|
| Validation (Module 2) | Input collection (forms) |
| Demand estimation (Module 3) | Visualization (charts, dashboards) |
| Eligibility determination | Displaying explanations/results (Module 9's rendering only) |
| Graph construction, candidate generation (Module 4) | — |
| Every mathematical calculation (Phase 5D formulas) | — |
| Optimization / overlap resolution (Module 6) | — |
| Decision-state determination (Module 5) | — |

**Binding rule, restated because it is the one this phase most needs to guarantee: no authoritative mathematical decision is ever made only in the frontend.** The frontend receives a fully-computed `ForecastResult`/decision payload (Section 6, companion document) and renders it — it never re-derives, re-checks, or overrides a decision state, a savings figure, or an eligibility outcome. This directly enforces Phase 5A's own decision-support principle at the software-architecture level.

## 13. Recommended Implementation Architecture

**Reused from `research/phase3_system_architecture.md`, Section 18 — not reinvented, because nothing in Phases 5A–5E gives a reason to change it:**

```
Frontend (React, or plain HTML/JS if tooling overhead doesn't fit the timeline)
      |  HTTP
      v
API Layer (FastAPI)
      |
      v
Service / Core Logic Layer (Modules 2-8, Section 3 above -- plain Python)
      |
      v
Data / Configuration Layer (SQLite for vendor/run data; a config file or table for D_max, MOQ_c, F_c, m, TC tiers)
```

**Why this still fits, re-verified against this phase's own criteria:**
- **Reproducibility:** SQLite is file-based and trivially versioned; every run is logged (Module 10).
- **Unit testing:** the Service/Core Logic layer is plain Python functions with no framework dependency, directly testable (Section 14, companion document).
- **Separation of concerns:** the four-layer structure directly mirrors Section 12's frontend/backend boundary — nothing in the Service layer depends on how the API or frontend is built.
- **Mathematical transparency:** every formula in the Service layer is a direct, traceable implementation of a named Phase 5D/2A equation — no black box, no framework magic performing a calculation implicitly.

**Libraries, also reused from Phase 3 §18 without change:** NetworkX (compatibility graph, connected components) + Python `itertools` (subset enumeration, brute-force set packing) + a plain Haversine implementation — no ML library, no solver dependency, matching this phase's explicit "no unnecessary complexity" instruction.

## 16. Recommended Project Folder Structure

**Existing folders and files are preserved exactly as they are — nothing below proposes moving, renaming, or deleting `data/`, `research/`, `reports/`, or `scripts/`.**

```
mini project/
├── data/                    (existing -- untouched)
│   ├── raw/
│   ├── processed/
│   └── documentation/
├── research/                (existing -- untouched)
├── reports/                 (existing -- untouched; this phase's outputs added alongside)
├── scripts/                 (existing -- untouched; Phase 3A/4 data-acquisition scripts remain here)
├── app/                     (NEW -- not created in this phase; where implementation would go)
│   ├── core/                (Modules 2-8: validation, estimation, group formation,
│   │                         decision engine, overlap resolution, abstention, explanation)
│   ├── api/                 (FastAPI route definitions -- Module orchestration only,
│   │                         no math)
│   ├── config/              (D_max, MOQ_c, F_c, m, TC tiers -- configurable parameters,
│   │                         Section 10, kept separate from code)
│   └── db/                  (SQLite models/schema -- not designed in this phase)
├── frontend/                (NEW -- not created in this phase)
├── tests/                   (NEW -- not created in this phase; see companion
│   │                         traceability document for the test plan)
│   ├── unit/
│   └── integration/
└── docs/                    (NEW, optional -- a place for a final paper/writeup,
                              distinct from research/ and reports/ which remain the
                              phase-by-phase audit trail)
```

**Nothing under `app/`, `frontend/`, `tests/`, or `docs/` is created in this phase** — these are proposed locations only, per this phase's explicit "do not create application code" rule.

---

**Continued in:** `reports/phase5f_module_interfaces.md` (Sections 5–9's full contracts and interfaces) and `reports/phase5f_traceability_and_implementation_plan.md` (testing architecture, traceability map, implementation order, final audit, Phase 6 recommendation).

**Files read for this phase:** `research/phase3_system_architecture.md`, `research/phase2a_mathematical_model.md`, `research/phase2b_algorithm_selection.md`, `reports/phase5a_research_findings_and_system_policy.md`, `reports/phase5c_demand_data_and_ml_feasibility.md`, `reports/phase5d_mathematical_decision_model.md`, `reports/phase5e_group_formation_design.md`.
**Files modified:** none.
