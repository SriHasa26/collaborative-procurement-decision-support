# Phase 5G — Fixture → Test Mapping

**Date:** 2026-09-14
**Scope:** Companion to `reports/phase5g_implementation_fixtures.md`. Maps every fixture (D1–D4, G1–G4) to its future module, test type, and expected assertion. No test code is written here — this is a specification for Phase 6A's test authors to implement against.

---

## Mapping Table

| Fixture | Future Module | Test Type | Expected Assertion |
|---|---|---|---|
| **D1** | Demand Estimation Module | Unit test | Given `VX` with no history and peers `[8, 10, 9]` in category `tea_stall`, the module returns $q_i = 9$ with provenance `ESTIMATE — cold-start` |
| **D2** | Demand Estimation Module | Unit test | Given `VY` with diary `[6, 9, 8]` (≥3 records), the module returns $q_i = 7.67$ (moving average) with provenance `ESTIMATE — baseline` — **and** a negative-case assertion that the result is *not* $8$ (which would indicate last-observed-value was wrongly applied instead) |
| **D3** | Demand Estimation Module | Abstention test | Given `VZ` with no history and zero peers in category `street_juice_cart`, the module returns `ABSTAIN` with reason containing "no same-category peers"; **no** `q_i` field is populated (null/absent, not zero) |
| **D4** | Input/Data Module (validation layer) | Validation test | Given a submission of $q_i = -5$ for `VW`, the module raises/returns `VALIDATION ERROR` **before** the Demand Estimation Module is ever invoked — assert the Demand Estimation Module's function is not called at all for this input (a call-count or mock-invocation assertion, not just an output check) |
| **G1** | Group Formation Engine (compatibility graph construction) | Unit test | Given `VA=(17.4520,78.4867)` and `VB=(17.4550,78.4900)` with $D_{max}=2$, `Compatible(VA,VB)` returns `true` and the computed Haversine distance is $\approx 0.43$ km (assert within a small tolerance, e.g. ±0.01 km, not exact floating-point equality) |
| **G2** | Explanation Generator / Results Interface | Output-labeling test | Given `VA`'s stored `location_status = VENDOR-SPECIFIC (approximate)`, any generated explanation string referencing `VA`'s location contains an approximate/non-exact qualifier (e.g., matches a pattern like `"approximate"` or equivalent) and does **not** contain wording implying exact/verified precision (e.g., assert absence of strings like `"exact address"`, `"verified GPS"`) |
| **G3** | Explanation Generator / Input-Data Module (price ingestion) | Labeling-integrity test | Given a price record tagged `geographic_level = DISTRICT_LEVEL_PROXY`, assert that no code path re-tags or displays it as `MANDI_LEVEL`, and that any rendered text referencing it includes "district-level" or "proxy" wording — **this test must not pull data from, or re-invoke, the closed Potato experiment's pipeline**; it should use a fresh, independently-labeled fixture record asserting the same rule |
| **G4** | Validation & Eligibility Module | Isolation test | Given `VA`, `VB` (valid locations) and `VC` (missing location) submitted together in one batch, assert: `VC`'s result is `ABSTAIN` with reason containing "location unavailable"; `VA` and `VB`'s results are unaffected (i.e., `Compatible(VA,VB)` is still evaluated and still returns `true`, exactly as in G1) — this specifically must be a **batch-level** test, not three isolated single-vendor tests, since its purpose is proving non-interference between vendors in the *same* run |

## Notes for Phase 6A's Test Authors

- **D2 and G1 include a negative assertion deliberately** (D2: result ≠ 8; G1: distance tolerance rather than exact equality) — these guard against a specific, plausible implementation mistake (wrong baseline method; floating-point Haversine drift), not generic "does it run" checks.
- **D4's assertion is about call isolation, not just output** — a naive implementation might compute an `ABSTAIN`-like result for a negative value rather than a distinct `VALIDATION ERROR`, which would silently blur Section 7's distinction from `reports/phase5g_implementation_fixtures.md`. The test must catch that specific failure mode, not just check that *something* non-numeric came back.
- **G3's test must not touch `data/raw/ceda/` or any Phase 3A/4 script.** It should construct its own minimal, freshly-labeled fixture record (e.g., a small in-memory or fixture-file price record tagged `DISTRICT_LEVEL_PROXY`) rather than loading the real, already-closed Potato dataset — keeping this test fully decoupled from the closed experiment, per this phase's binding rule.
- **None of these eight tests requires a database, an API, or a frontend to exist** — every one operates on a module's direct function-level input/output, consistent with Phase 5F's recommendation to write unit tests incrementally alongside core-logic implementation (Steps 2–9 of `reports/phase5f_traceability_and_implementation_plan.md`, Section 4), not deferred until the full pipeline is assembled.

---

**Files read for this phase:** `reports/phase5g_implementation_fixtures.md`, `reports/phase5f_module_interfaces.md`, `reports/phase5f_traceability_and_implementation_plan.md`.
**Files modified:** none.
