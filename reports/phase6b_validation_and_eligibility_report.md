# Phase 6B — Validation and Eligibility Pipeline

**Date:** 2026-09-14
**Scope:** Batch-level input validation, demand-estimation integration, and vendor eligibility determination — the layer between raw vendor submissions and Phase 6C's (not-yet-built) group formation. No compatibility graph, group generation, overlap resolution, API, database, or frontend. Phase 6A's working logic is reused unchanged except for one justified, additive, documented extension.

---

## 1. Phase 6B Objective

Take a procurement context containing multiple raw vendor submissions and determine, per vendor, independently: is there enough valid, non-fabricated evidence to proceed to Phase 6C? Every non-eligible outcome must carry a named, machine-readable reason, and one vendor's failure must never affect another's result.

## 2. Existing Phase 6A Components Reused

Inspected directly (`backend/models/enums.py`, `backend/models/contracts.py`, `backend/services/demand_estimation.py`, `backend/services/decision_engine.py`) before writing any new code, per this phase's Step 1:

| Component | Reused as-is | Notes |
|---|---|---|
| `DecisionState`, `PriceGeographicLevel`, `VendorLocationStatus`, `OutcomeKind` | ✅ Unchanged | No duplicate enum created |
| `TaggedLocation`, `TaggedPrice`, `VendorInput`, `CommodityParams`, `ConfigParams`, `ProcurementContext` | ✅ Unchanged | Phase 6B's `VendorInput` output is exactly this Phase 6A type, not a new one |
| `estimate_demand`, `cold_start_estimate`, `limited_history_estimate`, `ValidationError`, `MOVING_AVERAGE_WINDOW` | ✅ Unchanged, called directly | Not reimplemented anywhere in Phase 6B |
| `evaluate_group`'s critical-field check list (q_i, location, horizon, individual price, context price) | ✅ Read and matched against | Confirmed Phase 6B's eligibility checks are consistent with, not divergent from, what `evaluate_group` independently re-checks |

**One additive, documented exception:** `EstimationProvenance` gained a new member, `USER_PROVIDED` — see Section 7.

## 3. Files Created

- `backend/models/reasons.py` — `ValidationErrorReason`, `AbstentionReason`, `ContextValidationReason` (new vocabulary, no duplication of existing enums)
- `backend/models/batch_contracts.py` — `VendorSubmission`, `VendorEligibilityResult`, `ContextValidationResult`, `BatchEligibilityResult`
- `backend/services/validation.py` — `validate_context`, `validate_vendor_structure`
- `backend/services/eligibility.py` — `evaluate_vendor`
- `backend/services/pipeline.py` — `evaluate_procurement_context`
- `tests/fixtures/batch_fixtures.py` — Phase 6B fixture data
- `tests/unit/test_eligibility.py`, `tests/unit/test_pipeline.py`
- This report

## 4. Files Modified

**One file:** `backend/models/enums.py` — a single additive line (`USER_PROVIDED = "USER_PROVIDED"`) plus an explanatory docstring addition. No existing enum value was changed, removed, or renamed. **Nothing else** under `backend/` was modified. No file under `data/`, `research/`, `scripts/`, or any prior `reports/` file was touched.

## 5. Procurement-Context Validation

Implemented in `validate_context()`, checking only what the existing `ProcurementContext` contract and this phase's own named examples require: `commodity_id` present, `date` present, vendor collection non-empty and well-formed (every item is a `VendorSubmission` with a non-empty `vendor_id`). **Two deliberate non-additions, documented in the code itself, not silently decided:**
- **"Invalid procurement horizon"** (named as a possible context check in this phase's brief) does not apply — `ProcurementContext` has no horizon field; the order horizon $k$ is a per-group *decision variable* computed in Stage 2 (Phase 5D Section 6), never a context input. Inventing one here would violate this phase's own "do not invent additional mandatory fields" rule.
- **Missing wholesale price** is *not* treated as a context validation failure — it is an evidentiary gap Phase 6A's `evaluate_group` already handles at the group-evaluation stage, and it is not named among Phase 5E Section 4's or this phase's own Step 5 eligibility fields. Full reasoning in `validation.py`'s docstring and Section 16 below.

A structurally invalid context stops the entire batch immediately — no vendor list is populated, per Step 2's explicit instruction.

## 6. Vendor Validation Rules

`validate_vendor_structure()` checks fields Phase 6A's `demand_estimation.py` never needed to check (location coordinate validity, a directly-submitted `user_provided_q_i`, individual price, horizon positivity), returning a named `ValidationErrorReason` or `None`. **Diary/peer-list numeric validation is not duplicated** — it is delegated entirely to Phase 6A's own `_validate_numeric_records` (via `estimate_demand`, caught in `eligibility.py`), exactly per Step 1's "do not duplicate existing demand logic."

## 7. Demand Estimation Integration

`eligibility.py` calls Phase 6A's `estimate_demand` unchanged for diary/peer-based resolution. **One genuine gap against the authoritative design was found and closed, not invented:** Phase 5D Section 2's own notation table lists $q_i$'s possible status as *"Real (diary) / User-provided (survey) / Estimated (cold-start)"* — three named categories — but Phase 6A's `EstimationProvenance` enum only formalized two (`ESTIMATE_COLD_START`, `ESTIMATE_BASELINE`), because Phase 6A never received a raw, pre-estimation vendor submission that could carry a directly-stated survey figure. **`USER_PROVIDED` was added, additively, to close this gap** — verified not to break any of Phase 6A's 20 existing tests (re-run immediately after the edit, Section 14).

**Documented precedence ambiguity, not silently decided:** Phase 5C/5D's hierarchy discusses "history" (diary) versus "peers" (cold-start) but never explicitly ranks a one-time, directly-stated survey quantity against diary-derived estimates. This implementation gives a directly user-provided value precedence over diary/peer estimation, reasoned from Phase 1C's original design (the survey-stated "typical quantity" was the Priority-1 primary economic baseline; diary and cold-start were supplementary/fallback instruments) — stated in `eligibility.py`'s module docstring as an interpretation, not an asserted authoritative rule.

**No estimate is ever labeled AI/ML/prediction** — `ESTIMATE_ML` remains unused; `USER_PROVIDED`, `ESTIMATE_COLD_START`, and `ESTIMATE_BASELINE` are the only values any code path produces.

## 8. Eligibility Logic

`evaluate_vendor()` implements the exact order this phase's Step 6 recommends: structural validation → resolve demand → validate demand result → location check → horizon check → eligibility determination. **One documented scope boundary:** individual price (`individual_price_rs_per_kg`) is required by Phase 6A's `VendorInput`/`evaluate_group` but is **not** named among Phase 5E Section 4's or this phase's own Step 5 "authoritative fields" (`q_i`, `L_i`, `H_{i,c}`). Phase 6B therefore does **not** treat a missing individual price as an eligibility failure — an eligible vendor may carry `individual_price_rs_per_kg=None`, and Phase 6A's `evaluate_group` will correctly `ABSTAIN` on it later if that vendor ever enters a candidate group. This is a deliberate, documented decision, not an oversight (see the docstring in `eligibility.py`).

## 9. ABSTAIN vs. VALIDATION_ERROR Distinction

Enforced structurally, not just by convention: `ValidationError` is a Python exception (raised by structural checks or by Phase 6A's `_validate_numeric_records`), while `ABSTAIN` is a normal `VendorEligibilityResult` with `status="ABSTAIN"`. `evaluate_vendor` never converts one into the other. Tested explicitly (`test_negative_diary_value_raises_phase6a_validation_error_internally`, and the D3/D4-style contrast already established in Phase 6A, re-confirmed at the batch level in `test_9`/`test_10`).

## 10. Batch Processing Behavior

`evaluate_procurement_context()` evaluates every vendor independently, wrapping each call in its own `try/except` as defense-in-depth beyond `eligibility.py`'s own internal exception handling. Results are partitioned into exactly three collections (`eligible_vendors`, `abstained_vendors`, `validation_error_vendors`) — every submitted vendor appears in **exactly one**, verified directly by a disjointness assertion in `test_9` and a total-count assertion in `test_10`/`test_large_mixed_batch_all_vendors_accounted_for`.

## 11. Reason/Status Taxonomy

| Category | Values | Enum |
|---|---|---|
| Validation errors | `NEGATIVE_QUANTITY`, `INVALID_NUMERIC_VALUE`, `MALFORMED_LOCATION` | `ValidationErrorReason` |
| Abstention reasons | `INSUFFICIENT_DEMAND_EVIDENCE`, `MISSING_LOCATION`, `MISSING_HORIZON` | `AbstentionReason` |
| Context-level reasons | `MISSING_COMMODITY`, `EMPTY_VENDOR_COLLECTION`, `MALFORMED_VENDOR_COLLECTION`, `MALFORMED_CONTEXT_METADATA` | `ContextValidationReason` |

Every non-eligible `VendorEligibilityResult` carries one of these named codes plus a human-readable `reason_detail` string — no vague message appears anywhere in the codebase.

## 12. Geographic Metadata Handling

`VendorLocationStatus` and `PriceGeographicLevel` remain two separate enums (Axis 1 vs. Axis 2, per Phase 5G Section 5); no function anywhere converts one status into another. `evaluate_vendor` calls only `TaggedLocation.is_usable()` (returns `False` exactly for `MISSING`) — it never inspects or compares `LOCALITY_CENTROID_PROXY` against `VENDOR_SPECIFIC_APPROXIMATE` as if one were "close enough" to the other. **Phase 6B explicitly does not calculate compatibility** — it only determines whether location information is *present enough to proceed*, exactly per Step 9. Verified in `test_12`.

## 13. Test Fixtures

`tests/fixtures/batch_fixtures.py` reuses Phase 5G's actual **numeric data** (D1's peer values `[8,10,9]→9.0`; D2's diary `[6,9,8]→7.67`) rather than re-deriving new numbers for the same cases, per Step 11's "do not duplicate fixture data unnecessarily." New fixtures were added only for cases Phase 5G's single-vendor fixtures did not need to cover: batch-shaped `VendorSubmission` objects, a locality-proxy-location vendor, and several edge cases (malformed coordinates, diary/peer lists containing an invalid value, explicitly-empty tuples). Every new value is labeled `SIMULATED ILLUSTRATIVE FIXTURE DATA` in the file's own docstring and per-fixture comments.

## 14. Test Results

```
41 passed, 0 failed, 0 skipped
```

| Suite | Tests | Result |
|---|---|---|
| Phase 6A (all 4 existing files, unchanged) | 20 | ✅ all still pass — re-run immediately after the `enums.py` edit and again at the end |
| `test_eligibility.py` (TEST 1–8, 11, 12 + 4 edge cases + 1 internal check) | 15 | ✅ all pass |
| `test_pipeline.py` (TEST 9, 10 + 1 larger mixed batch + 3 context edge cases) | 6 | ✅ all pass |
| **Total** | **41** | **41 passed, 0 failed, 0 skipped** |

**No failure was hidden.** No test was skipped or marked `xfail`.

## 15. Edge Cases Tested

Beyond the 12 required test cases: empty vendor list, missing commodity, malformed vendor collection (empty `vendor_id`), malformed location coordinates (out-of-range lat), a diary/peer list containing one invalid value alongside valid ones, and explicitly-empty (not `None`) diary/peer tuples — confirmed to behave identically to `None` (routes to `ABSTAIN`, not a different code path). Every edge case's expected behavior was checked against the authoritative documents/existing contracts first (per Step 13), not decided by convenience.

## 16. Known Ambiguities

Two genuine ambiguities were found in the authoritative documents and resolved by **explicit, documented interpretation** rather than silent invention — both are also stated in the relevant source file's docstring, not just here:

1. **Precedence between a directly user-provided $q_i$ and diary/peer estimation** (Section 7) — no prior phase explicitly ranked these; this implementation gives the direct value precedence, reasoned from Phase 1C, and states this as an interpretation.
2. **Whether individual price is an eligibility-blocking field** (Section 8) — Phase 5E Section 4's own list names only three fields; this implementation follows that list exactly rather than adding a fourth, and documents the consequence (an eligible vendor may still carry `individual_price_rs_per_kg=None`, caught later by Phase 6A's existing defensive check).

Neither ambiguity was resolved by picking whichever answer was easiest to implement — both are traceable to a specific authoritative passage and a stated reason.

## 17. Deferred Functionality

Unchanged from Phase 6A's own deferral list, restated because Phase 6B does not touch any of it: compatibility graph construction, connected components, within-pool candidate/subset enumeration, overlap resolution / weighted set packing, Phase 5E's `WAIT_OR_EXPAND_GROUP` superset-search refinement — all remain Phase 6C's scope. No API, database, frontend, external retrieval, or ML was introduced in Phase 6B either.

## 18. Final Consistency Audit

| # | Check | Result |
|---|---|---|
| 1 | Existing Phase 6A demand logic reused | ✅ `estimate_demand` called directly, unmodified |
| 2 | No demand logic duplicated | ✅ diary/peer validation delegated entirely to Phase 6A |
| 3 | No mathematical formulas modified | ✅ `decision_math.py`/`geo_math.py` untouched |
| 4 | `ABSTAIN` ≠ `VALIDATION ERROR` | ✅ exception vs. normal result, tested explicitly |
| 5 | Missing evidence never fabricated | ✅ every `ABSTAIN`/error path leaves `vendor_input=None` |
| 6 | One failing vendor does not block others | ✅ `test_9`, `test_10`, `test_large_mixed_batch...` |
| 7 | Demand provenance preserved | ✅ `test_11` |
| 8 | Geographic proxy metadata preserved | ✅ `test_12` |
| 9 | Eligibility happens before compatibility | ✅ no compatibility/graph code exists anywhere in Phase 6B |
| 10 | No NetworkX introduced | ✅ confirmed by inspection — no such import anywhere |
| 11 | No group generation introduced | ✅ confirmed |
| 12 | No overlap resolution introduced | ✅ confirmed |
| 13 | No ML introduced | ✅ `ESTIMATE_ML` remains unused |
| 14 | No external API calls introduced | ✅ no network/file I/O in any Phase 6B module |
| 15 | No database introduced | ✅ confirmed |
| 16 | No frontend/API introduced | ✅ confirmed — only `backend/{models,services}` and `tests/` exist |
| 17 | Phase 6A tests still pass | ✅ 20/20, both immediately after the enum edit and in the final full run |
| 18 | Existing research files untouched | ✅ confirmed |
| 19 | Closed Potato ML experiment untouched | ✅ confirmed — no file under `data/raw/ceda/` was read or written this phase |

**No inconsistency found.**

## 19. Recommendation for Phase 6C

Phase 6C should implement group formation exactly as Phase 2B/Phase 5E specify (compatibility graph via `geo_math.haversine_distance`/the $2D_{max}$ pruning rule, connected components, within-pool subset enumeration), consuming the `eligible_vendors` list `evaluate_procurement_context` now produces — each already a ready-made `VendorInput` — and feeding candidate groups into Phase 6A's unmodified `evaluate_group`. Phase 6C should also implement Phase 5E Section 12's pool-superset-search refinement (confirming or downgrading a `WAIT_OR_EXPAND_GROUP` result), which Phase 6A's `evaluate_group` docstring already explicitly defers to it. No API, database, or frontend work should begin before Phase 6C's group-formation logic is implemented and tested against Phase 5E's own worked example (already available as `tests/unit/test_decision_engine_regression.py`'s per-candidate fixtures, ready to be composed into a full pool-level test once generation exists).

---

**Files read for this phase:** `backend/models/enums.py`, `backend/models/contracts.py`, `backend/services/demand_estimation.py`, `backend/services/decision_engine.py`, `reports/phase5d_mathematical_decision_model.md`, `reports/phase5e_group_formation_design.md`, `reports/phase5f_system_architecture.md`, `reports/phase5f_module_interfaces.md`, `reports/phase5f_traceability_and_implementation_plan.md`, `reports/phase5g_implementation_fixtures.md`, `reports/phase5g_fixture_test_mapping.md`, `reports/phase6a_core_foundation_report.md`.
**Files modified:** `backend/models/enums.py` (one additive enum value). No other existing file was modified.
