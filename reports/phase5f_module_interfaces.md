# Phase 5F — Module Interfaces and Data Contracts

**Date:** 2026-09-14
**Scope:** Companion to `reports/phase5f_system_architecture.md`. Defines the input contract, output contract, module-to-module interfaces, validation/error routing, and decision-state routing referenced there (Section 5–9). No implementation code — interface definitions and structured pseudocode only.

---

## 1. Input Data Contract

### A. Vendor Inputs

| Field | Type | Required/Optional | Unit | Status |
|---|---|---|---|---|
| `vendor_id` | string (anonymous) | Required | — | Real (assigned at registration) |
| `location` (lat, lon) | float pair | Required for group formation; a vendor without it is `ABSTAIN` for any commodity | decimal degrees | User-provided |
| `commodity_requirements` | list of (commodity, $q_i$-source-data) | Required — at least one entry | — | See "Commodity Inputs" below for $q_i$'s own status |
| `practical_procurement_horizon` ($H_{i,c}$, or the raw purchase-frequency field used as its proxy) | integer (days), per commodity | Required — directly or via proxy | days | User-provided (direct) / Estimated (proxy derivation) |

### B. Commodity Inputs

| Field | Type | Required/Optional | Unit | Status |
|---|---|---|---|---|
| `commodity_id` | string, one of the fixed V1 set | Required | — | Real (fixed catalog) |
| `freshness_window` ($F_c$) | integer (days) | Required | days | Real (scientific component) / Estimated (trader-triangulated component) — labeled per component, never merged |
| `moq` ($MOQ_c$) | integer (kg) or **absent** | Optional — absent is a valid, meaningful state | kg | User-provided (trader-confirmed) **only if it exists; never defaulted** |

### C. Procurement Context Inputs

| Field | Type | Required/Optional | Unit | Status |
|---|---|---|---|---|
| `commodity_id` | string | Required | — | — |
| `date` ($t$) | date | Required | — | — |
| `candidate_vendor_pool` | list of `vendor_id` | Required (system-derived from B/A, not separately entered) | — | Derived |

### D. Price Inputs

| Field | Type | Required/Optional | Unit | Status |
|---|---|---|---|---|
| `wholesale_price` ($p^{wh}_{c,t}$) | float | Required for evaluation to proceed — absence → `ABSTAIN` for the whole context (Phase 5F system architecture §11) | ₹/kg | Real (data.gov.in daily snapshot) — **must carry `geographic_level` tag** |
| `individual_price` ($p^{ind}_{i,c}$) | float, per vendor | Required per vendor | ₹/kg | User-provided |
| `trader_margin` ($m$) | float, one of $\{0, 0.10, 0.15\}$ | Required (system default 0, others as labeled sensitivity runs) | ratio | Configurable prototype parameter |

### E. Configurable Prototype Parameters

| Field | Type | Required/Optional | Unit | Status |
|---|---|---|---|---|
| `d_max` ($D_{max}$) | float | Required (system configuration) | km | Configurable prototype parameter |
| `transport_cost_tiers` ($TC(\text{tier})$) | list of (capacity, cost) | Required | kg, ₹ | Real (rate bands) / Configurable (exact cutoffs) |

**This is an interface/data contract, not a database schema** — no storage engine, indexing, or normalization decision is made here, per this phase's explicit instruction.

## 2. Output Contract

**One structured result per (candidate group **or** vendor, procurement context) pair.** Directly extends Phase 5A's conceptual `ForecastResult` (Section 6 there) with Phase 5D/5E's group-level fields:

```
StructuredResult {
    procurement_context: { commodity, date },
    eligible_vendors: [vendor_id, ...],
    abstained_vendors: [ { vendor_id, reason }, ... ],
    candidate_groups: [ { group_id, members: [vendor_id, ...] }, ... ],   // generated, may overlap
    selected_groups: [ group_id, ... ],                                   // post overlap-resolution
    ungrouped_vendors: [ { vendor_id, reason }, ... ],
    per_group_result: [
        {
            group_id,
            decision_state: BUY_TOGETHER | WAIT_OR_EXPAND_GROUP | DO_NOT_BUY_TOGETHER | ABSTAIN,
            k_star: int | null,
            aggregate_quantity: float | null,          // Q_G(k*)
            moq_result: { applicable: bool, required: float|null, met: bool|null },
            freshness_result: { bound_days: int, k_used: int|null },
            logistics_result: { centroid_distance_km: float, within_d_max: bool },
            individual_cost_total: float | null,       // C_ind_total,G(k*)
            collaborative_cost: float | null,           // C_collab_G,c(k*)
            savings: float | null,
            per_vendor_allocation: [ { vendor_id, share, individual_savings }, ... ] | null,
            explanation: string
        }, ...
    ]
}
```

**Internal calculations not exposed unnecessarily:** the compatibility graph's edge list, the full within-pool candidate enumeration (only surviving/relevant candidates appear), and the raw scaler/intermediate arithmetic of any calculation are not part of this output — only the values a vendor or researcher needs to trust and audit the result (per this phase's explicit "do not expose internal calculations unnecessarily" instruction). **All four decision states are representable** — `ABSTAIN` populates `abstained_vendors` (vendor-level) or a `per_group_result` entry with `decision_state: ABSTAIN` and null numeric fields (context-level, e.g. missing $p^{wh}_{c,t}$); the other three states always populate the full numeric trace.

## 3. Module Interfaces

**Format: INPUT → PROCESS → OUTPUT, per this phase's instruction — structured pseudocode only, no implementation.**

### Demand Estimation Module
```
INPUT:   vendor_id, commodity_id, vendor's own reported data (if any), peer-category records
PROCESS: apply Phase 5C's hierarchy —
           IF sufficient own history: use last-observed-value or short moving average (baseline)
           ELIF category peers exist: same-category peer average (cold-start)
           ELSE: cannot estimate
OUTPUT:  { q_i: float, provenance: "ESTIMATE-cold-start" | "ESTIMATE-baseline" } 
         | ABSTAIN("no demand estimate available")
```

### Eligibility Module
```
INPUT:   vendor record (location, q_i + provenance, H_i,c or proxy) for one (commodity, date)
PROCESS: check q_i defined and >= 0; check location present; check H_i,c present (direct or proxy)
OUTPUT:  ELIGIBLE(vendor_id) | ABSTAIN(vendor_id, "<specific missing field>")
```

### Group Formation Engine
```
INPUT:   V_c_elig (eligible, commodity-relevant vendors), their locations, D_max
PROCESS: build compatibility graph (edge iff Haversine(L_i, L_j) <= 2*D_max)
         -> connected components (independent pools)
         -> within-pool subset enumeration (size >= 2)
OUTPUT:  candidate_groups: [ { group_id, members }, ... ]   // may overlap
```

### Procurement Decision Engine
```
INPUT:   one candidate_group, commodity/date parameters (p_wh, p_ind per member, m, F_c,
         H_i,c per member, MOQ_c if known, TC tiers, D_max)
PROCESS: Phase 5D §4-9, exactly:
           1. geographic check d(G) <= D_max -- fail -> DO_NOT_BUY_TOGETHER
           2. for k in {1..min(F_c, min H_i,c)}: compute Q_G(k), costs, savings
           3. MOQ check (if MOQ_c known) -- if fails for all k but savings would be
              positive once met -> flag for WAIT_OR_EXPAND_GROUP (Engine defers to
              §12 superset check, see below)
           4. among surviving k: if any Savings_G(k) > 0 -> BUY_TOGETHER, k* = argmax
           5. else -> DO_NOT_BUY_TOGETHER
OUTPUT:  { decision_state, k_star, Q_G, moq_result, freshness_result, logistics_result,
           cost_individual, cost_collab, savings, per_vendor_allocation }
```

### WAIT_OR_EXPAND_GROUP Resolver (a sub-routine of the Decision Engine, not a separate module — Phase 5E §12)
```
INPUT:   a candidate group G flagged as an MOQ-shortfall-but-promising case, plus the
         FULL set of already-generated/evaluated candidates from the same pool
PROCESS: search already-computed results (no new search) for any G' superset of G
         with decision_state == BUY_TOGETHER
OUTPUT:  IF found: WAIT_OR_EXPAND_GROUP(G, points_to=G'.group_id, shortfall=MOQ_c - Q_G(k_best))
         ELSE:      DO_NOT_BUY_TOGETHER(G, reason="no viable expansion within compatible pool")
```

### Overlap Resolution / Final Selector
```
INPUT:   all candidates with decision_state == BUY_TOGETHER for one (commodity, date)
PROCESS: exact weighted set packing -- maximize sum(savings) subject to
         sum(x_G for G containing vendor i) <= 1 for every vendor i;
         tie-break: maximize distinct vendor coverage
OUTPUT:  selected_groups: [group_id, ...]  (pairwise vendor-disjoint)
```

### Explanation Generator
```
INPUT:   decision_state + full numeric trace for one group or vendor
PROCESS: select the template matching decision_state and (for DO_NOT_BUY_TOGETHER) the
         specific first-failed constraint, per the fixed check order (§5 below);
         fill template placeholders with already-computed values only
OUTPUT:  explanation: string
```

## 4. Validation and Error Routing

**Four categories, distinguished exactly as this phase's Step 8 requires:**

| Category | Example | Routing |
|---|---|---|
| **1. Invalid data** | $q_i$ submitted as negative; a coordinate outside valid lat/lon range | **Validation error** — rejected at the Input/Data Module before it ever reaches Eligibility; the specific vendor/field is flagged, not silently corrected |
| **2. Missing non-critical data** | $MOQ_c$ absent for a commodity; the ambient (vs. scientific) component of $F_c$ not yet triangulated | **Configurable fallback / constraint simply not applied** — e.g., no $MOQ_c$ means the MOQ constraint is skipped for that commodity (Phase 2A Part 18), not an error and not an `ABSTAIN` |
| **3. Missing critical data (per-vendor)** | $q_i$ undefined for a vendor with no cold-start peers; $L_i$ missing | **Exclusion from this run + `ABSTAIN`** — that specific vendor is routed to `ABSTAIN` for this $(c,t)$ context; per the binding rule below, this does **not** invalidate the run for any other vendor |
| **4. Missing critical data (context-level)** | $p^{wh}_{c,t}$ unavailable for date $t$ | **`ABSTAIN` for the entire procurement context** — every vendor's evaluation for this $(c,t)$ is abstained, because the shared price input this affects every candidate group, not one vendor |

**Binding rule, restated because this phase's Step 8 marks it "IMPORTANT": one vendor's missing information must never unnecessarily invalidate unrelated vendors or the entire run — unless the missing input is itself context-level (category 4), not vendor-level (category 3).** Concretely: if vendor V6 (Phase 5E's worked example) has no location, only V6 is abstained; V1–V5 and V7 proceed through compatibility, generation, and evaluation exactly as if V6 were never in $V$. This is already how Phase 5E's worked example behaves — this section makes the underlying rule explicit as a module-level contract, not merely a property of one example.

**No missing critical value is ever silently replaced** — categories 3 and 4 both terminate in an explicit `ABSTAIN` with a named reason, never a substituted number, per this project's standing rule since Phase 2A.

## 5. Decision-State Routing

| State | Originates in | Applies to | Evaluation order | Required explanation |
|---|---|---|---|---|
| `ABSTAIN` | Eligibility Module (vendor-level, before generation) **or** Procurement Decision Engine (context-level, e.g. missing $p^{wh}_{c,t}$) | Vendor **or** procurement context | **First** — checked before anything else can run for the affected scope | Named missing field/input |
| `DO_NOT_BUY_TOGETHER` | Procurement Decision Engine | Candidate group | After geography check (immediate) or after economics are found unrecoverable even with MOQ met (Phase 5E §12) | The specific constraint(s) failed, at every tested $k$; $BE_c(t)$ for context |
| `WAIT_OR_EXPAND_GROUP` | Procurement Decision Engine, via the WAIT/EXPAND Resolver sub-routine | Candidate group | After MOQ check, only if a pool superset resolves it | The MOQ shortfall amount, and which superset would resolve it |
| `BUY_TOGETHER` | Procurement Decision Engine, confirmed by the Overlap Resolution / Final Selector | Candidate group (provisional) → selected group (final) | Last — a group is only *finally* `BUY_TOGETHER` after surviving Section 3's Overlap Resolution step, even though the Decision Engine may tentatively reach it earlier | $k^*$, $Q_G(k^*)$, per-vendor allocation, $Savings_G(k^*)$ |

**No state logic is duplicated across modules** — the Eligibility Module owns vendor-level `ABSTAIN` triggers exclusively (Section 1 of the companion architecture document's module table); the Procurement Decision Engine owns all four states' *group-level* determination exclusively; the Overlap Resolution module never re-evaluates feasibility, only resolves conflicts among already-`BUY_TOGETHER` candidates. This one-owner-per-rule structure is what Section 2 of the companion document's dependency map already establishes at the architecture level — this section confirms it holds at the state-routing level specifically.

---

**Files read for this phase:** `reports/phase5d_mathematical_decision_model.md`, `reports/phase5e_group_formation_design.md`, `reports/phase5a_research_findings_and_system_policy.md`.
**Files modified:** none.
