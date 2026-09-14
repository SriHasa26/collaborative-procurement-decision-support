# Phase 5G — Implementation Fixtures (Demand Estimation & Geographic Granularity)

**Date:** 2026-09-14
**Scope:** Close the two testability gaps Phase 5F named (`reports/phase5f_traceability_and_implementation_plan.md`, Section 6) with small, deterministic, clearly-labeled fixtures — nothing else. No new demand model, no new geographic policy, no code, no ML, no reopening of the closed Potato experiment.

---

## 1. Purpose of Phase 5G

Phase 5F's own traceability audit named two rows in its map with no dedicated worked example: (1) the Demand Estimation Module's cold-start/baseline hierarchy, and (2) geographic-granularity tagging. This phase closes exactly those two gaps with minimal fixtures reproducible later as automated unit tests. Nothing about the demand hierarchy, the eligibility filter, or the geographic-granularity vocabulary is changed — every rule used below is quoted or directly reused from an already-approved phase.

## 2. Authoritative Sources Used

| Topic | Source |
|---|---|
| Demand-estimation hierarchy (cold-start / baseline / deferred ML / ABSTAIN) | Phase 5C, Sections 6–7; Phase 5D, Section 3; Phase 1C's original three-layer architecture |
| Eligibility filter and `ABSTAIN` triggers | Phase 5E, Sections 4, 13 |
| Vendor location collection method | `research/phase1c_data_feasibility_audit.md`, Section 3 (C4) — Option A (approximate stall coordinate, recommended) vs. Option B (locality centroid, fallback only) |
| Price-side geographic tagging (`geographic_level`) | Phase 5A's Data Granularity Rule; Phase 5D, Section 4a |
| Validation-error vs. missing-critical-data distinction | Phase 5F Module Interfaces, Section 4 |

## 3. Existing Demand-Estimation Hierarchy (Confirmed, Not Re-Derived)

Restated exactly, not modified:

1. **No usable vendor history →** cold-start estimation using same-category peer information, if available (Phase 5C, Section 6; Phase 5D, Section 3).
2. **Limited usable history →** a simple baseline — last-observed value or a short moving average (Phase 5C, Section 7; Phase 5D, Section 3 lists both as the candidate pool without locking one as universal).
3. **Sufficient, validated history →** ML is a defined-but-currently-unimplemented future slot (`PREDICTION — ML (validated)`) — not used, not assumed, in this project (Phase 5C, Section 12 verdict; Phase 5D, Section 3).
4. **Insufficient information to satisfy any of the above →** `ABSTAIN` (Phase 5E, Section 4/13).

**One deterministic tie-break is fixed here, for the first time, to make Case D2 reproducible — not a new algorithm, only a choice between two already-listed candidate methods that Phase 5C/5D deliberately left as an open menu:** when at least 3 usable diary records exist, apply the short moving average (window = 3); with fewer than 3, apply the last-observed value. This mirrors the window size Phase 5D/5E already used elsewhere (rolling/consumption windows of 3) purely for consistency of vocabulary — it is not imported from the closed Potato price experiment, and no price-forecasting result is reused here.

## 4. Demand Fixtures

**Format used for every fixture below, per this phase's Step 5 requirement.**

---

**Fixture ID:** D1
**Purpose:** Cold-start estimation with valid same-category peers.
**Status:** `ESTIMATE — cold-start`
**Data Label:** SIMULATED ILLUSTRATIVE FIXTURE DATA — not real vendor data.

**Input:**
- New vendor `VX`, category = `tea_stall` (illustrative), commodity = Potato, no own history.
- Same-category peers with valid $q_i$: peer1 = 8 kg/day, peer2 = 10 kg/day, peer3 = 9 kg/day.

**Processing Rule:** same-category peer average (Phase 5C, Section 6) — $q_{VX} = \frac{8+10+9}{3}$.

**Expected Output:** $q_{VX} = 9$ kg/day, provenance = `ESTIMATE — cold-start`.

**Reason:** No own history exists, but 3 valid same-category peer values do — the cold-start tier applies exactly as Phase 5C/5D specify, with no invented value.

---

**Fixture ID:** D2
**Purpose:** Limited-history baseline estimation.
**Status:** `ESTIMATE — baseline`
**Data Label:** SIMULATED ILLUSTRATIVE FIXTURE DATA.

**Input:**
- Vendor `VY`, commodity = Potato, diary records (chronological): 6, 9, 8 kg.

**Processing Rule:** 3 usable records exist → per Section 3's tie-break, apply the short moving average (window = 3), **not** last-observed-value.

**Expected Output:** $q_{VY} = \frac{6+9+8}{3} = 7.67$ kg/day (rounded to 2 d.p.), provenance = `ESTIMATE — baseline`.

**Reason:** Explicitly contrasted with last-observed-value (which would have given 8 kg/day) — this fixture exists specifically to test that the *correct* baseline method is applied, not merely that *some* baseline is applied. If only 1–2 records existed, last-observed-value would apply instead (a separate, smaller fixture a future test suite may add, not required here).

---

**Fixture ID:** D3
**Purpose:** Insufficient evidence — no history, no peers.
**Status:** `ABSTAIN`
**Data Label:** SIMULATED ILLUSTRATIVE FIXTURE DATA.

**Input:**
- New vendor `VZ`, category = `street_juice_cart` (illustrative, deliberately a category with zero other registered vendors), commodity = Potato, no own history.

**Processing Rule:** cold-start requires at least one same-category peer with a valid value — none exists; no history exists either.

**Expected Output:** `ABSTAIN`, reason: "no demand estimate available — no own history and no same-category peers exist." **No numeric $q_i$ is produced.**

**Reason:** This is the exact situation Phase 5E Section 4/13 names as a valid, evidence-based `ABSTAIN` — not an error, not a fabricated zero or category-wide default.

---

**Fixture ID:** D4
**Purpose:** Invalid submitted value — distinguished explicitly from D3's `ABSTAIN`.
**Status:** `VALIDATION ERROR`
**Data Label:** SIMULATED ILLUSTRATIVE FIXTURE DATA.

**Input:**
- Vendor `VW` submits $q_i = -5$ kg/day for Potato (a well-formed but out-of-range numeric value).

**Processing Rule:** Input/Data Module's validation check (Phase 5F Module Interfaces, Section 4, Category 1) — a negative demand quantity is invalid on its face, independent of whether history or peers exist.

**Expected Output:** `VALIDATION ERROR` — the submission is rejected **before** it ever reaches the Eligibility or Demand Estimation Module. No `ABSTAIN` is recorded for this vendor at this stage, because `ABSTAIN` means "the system lacks evidence," not "the system received bad evidence."

**Reason — the distinction this fixture exists to test:** D3's vendor submitted nothing (an absence); D4's vendor submitted something malformed (a presence of invalid data). These reach different modules and produce different outcomes, and a future test suite must assert they are *not* interchangeable.

## 5. Existing Geographic Granularity / Status Policy (Confirmed, Not Re-Derived)

**Two distinct axes exist in this project already, and this phase does not merge them:**

**Axis 1 — price/market-data granularity**, formally named and tagged since Phase 5A: `MANDI_LEVEL` / `DISTRICT_LEVEL_PROXY` / `UNKNOWN_GRANULARITY` (Phase 5A's Data Granularity Rule; Phase 5D, Section 4a). This tag describes *where a price figure actually comes from* — e.g., the closed Potato experiment's CEDA data was confirmed `DISTRICT_LEVEL_PROXY` for Hyderabad, never Bowenpally-specific.

**Axis 2 — vendor location precision**, never formally tagged before this phase, but already narratively distinguished in Phase 1C, Section 3 (C4):
- **Option A (recommended, the current V1 default):** an approximate coordinate specific to *that individual vendor's stall*, entered manually or via device permission at onboarding.
- **Option B (fallback only, less accurate):** a shared locality/area centroid, used when even an individual approximate coordinate feels too sensitive or is unavailable.
- **Missing:** no coordinate recorded at all.

**This phase formalizes Axis 2 with a small, directly-derived tag — not a new precision claim, only a name for a distinction Phase 1C already made in prose:**

$$\texttt{location\_status} \in \{\texttt{VENDOR-SPECIFIC (approximate)},\ \texttt{LOCALITY-CENTROID (proxy)},\ \texttt{MISSING}\}$$

**No tier claims survey-grade or GPS-exact precision.** Even the best case (`VENDOR-SPECIFIC (approximate)`) is, by this project's own design (Phase 1C, Phase 2A Part 17), an approximate stall coordinate used for straight-line Haversine distance — not a claim of exact precision. This is stated here explicitly because this phase's own instruction warns against creating unsupported precision, and the fixtures below must not imply otherwise.

## 6. Geographic Fixtures

---

**Fixture ID:** G1
**Purpose:** A usable, vendor-specific location correctly feeds geographic compatibility calculations.
**Status:** `location_status = VENDOR-SPECIFIC (approximate)`
**Data Label:** SIMULATED ILLUSTRATIVE FIXTURE DATA — coordinates are invented, not a real vendor's location.

**Input:**
- Vendor `VA`, $L_{VA} = (17.4520, 78.4867)$ (illustrative lat/lon), $D_{max} = 2$ km.
- Vendor `VB`, $L_{VB} = (17.4550, 78.4900)$, same $D_{max}$.

**Processing Rule:** Haversine$(L_{VA}, L_{VB})$, compared against $2D_{max}$ for compatibility-graph construction (Phase 2B, Part 6B).

**Expected Output:** distance ≈ 0.43 km $\le 2D_{max}=4$ km → `Compatible(VA, VB) = true`; both vendors' `location_status` remains `VENDOR-SPECIFIC (approximate)` in the output.

**Reason:** Confirms a normally-populated, approximate-but-usable coordinate flows into the existing Phase 2B/5E compatibility check unchanged — no new geographic logic is introduced.

---

**Fixture ID:** G2
**Purpose:** The system must not claim more precision than the input actually carries.
**Status:** `location_status = VENDOR-SPECIFIC (approximate)`
**Data Label:** SIMULATED ILLUSTRATIVE FIXTURE DATA.

**Input:** Same vendor `VA` as G1, with the identical coordinate and status.

**Processing Rule:** none beyond what G1 already computed — this fixture targets the **output/explanation layer**, not the math.

**Expected Output:** any explanation or structured result referencing `VA`'s location must display it as `"approximate stall location"` or equivalent — it must **never** be rendered or described as an exact address, a verified GPS fix, or any wording implying higher confidence than `VENDOR-SPECIFIC (approximate)` warrants.

**Reason:** This is a labeling-integrity test, not a calculation test — it exists specifically because Phase 5F Section 12 requires the frontend/output layer to never assert more than the backend actually computed or knows.

---

**Fixture ID:** G3
**Purpose:** A geographic *proxy* must never be presented as a *precise/direct* figure — illustrated conceptually via the already-closed Potato experiment, reused as a reference point only.
**Status:** `geographic_level = DISTRICT_LEVEL_PROXY` (Axis 1 — price data, not vendor location)
**Data Label:** This fixture reuses **no new numbers**. It references an already-published finding (Phase 3A.5/3A.6, Phase 5D Section 4a) purely as a conceptual anchor — **no procurement calculation is performed with it here, and none of the closed Potato experiment's data, model, or test set is reopened.**

**Input (conceptual, not recomputed):** the Potato price series acquired via CEDA was confirmed to be Hyderabad **district-level** data — an aggregate proxy, never Bowenpally- or Gaddiannaram-specific — a fact independently re-verified in Phases 3A.5, 3A.6, and 5D.

**Processing Rule:** Phase 5D Section 4a's binding rule — any price/comparator figure tagged `DISTRICT_LEVEL_PROXY` must carry that tag through to any output that uses it, and must never be silently upgraded to `MANDI_LEVEL`.

**Expected Output:** if a future system ever displayed a price sourced this way, its output would show `geographic_level: DISTRICT_LEVEL_PROXY`, and any accompanying text would say "Hyderabad district-level (proxy)" — never "Bowenpally market price."

**Reason:** `geographic_level = DISTRICT_LEVEL_PROXY` does **not** mean `geographic_level = MANDI_LEVEL` (precise market location) — this is the exact distinction this fixture exists to keep testable, using a real, already-verified project finding as its anchor rather than an invented scenario. **Note, kept brief and not expanded into a separate fixture per this phase's scope limit:** Axis 2's `LOCALITY-CENTROID (proxy)` tier (Section 5, Phase 1C's Option B) is the direct vendor-location analog of this same "proxy ≠ precise" principle, applied to location instead of price.

---

**Fixture ID:** G4
**Purpose:** Missing critical location data excludes only the affected vendor.
**Status:** `location_status = MISSING` → `ABSTAIN`
**Data Label:** SIMULATED ILLUSTRATIVE FIXTURE DATA.

**Input:**
- Vendor `VA`, $L_{VA}=(17.4520, 78.4867)$ (valid, as in G1).
- Vendor `VB`, $L_{VB}=(17.4550, 78.4900)$ (valid, as in G1).
- Vendor `VC`, location = **not recorded**.

**Processing Rule:** Eligibility filter (Phase 5E, Section 4) — a vendor with no usable location fails eligibility before compatibility or generation runs.

**Expected Output:** `VC` → `ABSTAIN`, reason: "location unavailable — cannot evaluate geographic compatibility." `VA` and `VB` proceed to compatibility determination exactly as in G1, **unaffected by `VC`'s exclusion.**

**Reason:** Directly re-confirms Phase 5F Module Interfaces Section 4's binding isolation rule ("one vendor's missing information does not unnecessarily invalidate unrelated vendors") with a minimal, standalone 3-vendor fixture, rather than relying only on Phase 5E's larger 7-vendor worked example for this specific assertion.

## 7. Validation Error vs. ABSTAIN — Summary Distinction

| | `VALIDATION ERROR` | `ABSTAIN` |
|---|---|---|
| What triggers it | A submitted value that is malformed or out of range (e.g., negative quantity) | A required value that is genuinely absent, with no fallback available |
| Which module catches it | Input/Data Module, before Eligibility | Eligibility Module or Procurement Decision Engine |
| What it means | "The system received bad input" | "The system lacks the evidence to decide" |
| Fixture demonstrating it | D4 | D3 (demand), G4 (location) |
| Can it be confused with the other? | No — a malformed value is never silently treated as "missing," and a missing value is never treated as "wrong" | — |

## 8. Fixture → Future Module → Test Mapping

**Full detail in the companion document, `reports/phase5g_fixture_test_mapping.md`.**

## 9. Simulated-Data Labeling Policy

**Every fixture in Sections 4 and 6 is labeled `SIMULATED ILLUSTRATIVE FIXTURE DATA`, without exception.** None of the vendor IDs, coordinates, categories, or quantities above represents a real vendor, a real location, or real collected data — consistent with this project's standing rule since Phase 1C/3A.2. Fixture G3 is the one exception worth naming precisely: it references a **real, already-published finding** (the Potato experiment's confirmed district-level-proxy status) as a conceptual anchor, but performs **no new calculation** and reuses **no actual data values** from that closed experiment — it is not itself simulated, but it is also not a new use of real data; it is a citation.

## 10. Final Consistency Audit

| # | Check | Result |
|---|---|---|
| 1 | No new demand estimation algorithm invented | ✅ D1–D3 reuse Phase 5C/5D's existing hierarchy exactly; D2's window-size tie-break selects between two already-listed candidates, invents no third method |
| 2 | No ML introduced | ✅ No fixture reaches the `PREDICTION — ML` tier; it remains unused, per Phase 5C's verdict |
| 3 | No simulated data presented as real | ✅ Every fixture in Sections 4/6 is labeled; G3 explicitly distinguishes citation from simulation |
| 4 | `ABSTAIN` never confused with validation error | ✅ Section 7's table, and D3/D4's paired contrast |
| 5 | Geographic precision never fabricated | ✅ Section 5 explicitly states no tier claims survey-grade precision |
| 6 | Proxy data never treated as direct location/price data | ✅ G3's binding rule (`DISTRICT_LEVEL_PROXY` ≠ `MANDI_LEVEL`), restated from Phase 5D §4a, not weakened |
| 7 | Missing location for one vendor doesn't stop unrelated vendors | ✅ G4 |
| 8 | Fixtures are deterministic | ✅ Every fixture has fixed inputs and one computed expected output — no randomness anywhere |
| 9 | Expected outputs can become unit-test assertions | ✅ Every fixture's "Expected Output" line is already assertion-shaped (Section 8/companion document) |
| 10 | No Phase 5D/5E/5F rule modified | ✅ Every processing rule cites its exact source section; none is redefined |

**No inconsistency found requiring a change to any prior phase.**

## 11. Recommendation for Phase 6A

**Phase 6A may now begin implementation of the Demand Estimation Module and the Eligibility/Geographic-tagging logic with both testability gaps closed.** Convert Sections 4 and 6's eight fixtures directly into automated unit/isolation tests (per the companion mapping document) as the very first tests written, before any other module — they are the smallest, most self-contained, and now fully specified. The window-size tie-break fixed in Section 3 (moving-average-3 for ≥3 records) should be implemented as a named, documented constant, not a hardcoded literal, so a future phase can revisit it deliberately rather than by accident. No frontend, backend, API, or database work should begin until these fixtures pass as real, executable tests.

---

**Files produced by this phase:**
- This report.
- `reports/phase5g_fixture_test_mapping.md`.

**Files read but not modified:** `research/phase1c_data_feasibility_audit.md`, `research/phase2a_mathematical_model.md`, `research/phase2b_algorithm_selection.md`, `reports/phase5a_research_findings_and_system_policy.md`, `reports/phase5c_demand_data_and_ml_feasibility.md`, `reports/phase5d_mathematical_decision_model.md`, `reports/phase5e_group_formation_design.md`, `reports/phase5f_module_interfaces.md`, `reports/phase5f_traceability_and_implementation_plan.md`. No dataset was modified. No model was trained. No external data was retrieved. The Potato experiment was referenced conceptually only (Fixture G3) and was not reopened, recomputed, or modified.
