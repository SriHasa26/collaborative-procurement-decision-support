# Phase 6A — Core Foundation and Mathematical Engine

**Date:** 2026-09-14
**Scope:** First implementation phase. Builds only the deterministic, already-audited mathematical/demand logic from Phase 5D/5E/5G, with tests. No frontend, no API, no database, no NetworkX/group-generation, no external retrieval, no ML.

---

## 1. Files Created

**Implementation (`backend/`):**
- `backend/__init__.py`, `backend/core/__init__.py`, `backend/models/__init__.py`, `backend/services/__init__.py` (empty package markers)
- `backend/models/enums.py` — `DecisionState`, `EstimationProvenance`, `PriceGeographicLevel`, `VendorLocationStatus`, `OutcomeKind`
- `backend/models/contracts.py` — `TaggedLocation`, `TaggedPrice`, `VendorInput`, `CommodityParams`, `TransportTier`, `ConfigParams`, `ProcurementContext`, `CandidateGroup`, `PerVendorAllocation`, `GroupDecisionResult`
- `backend/core/geo_math.py` — `haversine_distance`, `centroid`, `max_distance_from_centroid`, `is_within_radius`
- `backend/core/decision_math.py` — `effective_price`, `aggregate_quantity`, `individual_cost_total`, `transport_cost_for_quantity`, `collaborative_cost`, `savings`, `per_vendor_share`, `individual_savings`, `consumption_time_days`, `break_even_quantity`, `feasible_k_range`, `moq_applicable_and_met`
- `backend/services/demand_estimation.py` — `cold_start_estimate`, `limited_history_estimate`, `estimate_demand`, `ValidationError`
- `backend/services/decision_engine.py` — `evaluate_group` (the single-group, four-state Decision Engine)

**Tests (`tests/`):**
- `tests/__init__.py`, `tests/fixtures/__init__.py`, `tests/unit/__init__.py`
- `tests/fixtures/demand_fixtures.py` — D1–D4 fixture data
- `tests/fixtures/geo_fixtures.py` — G1–G4 fixture data
- `tests/unit/test_demand_estimation.py` — D1–D4 tests
- `tests/unit/test_geo_status.py` — G1–G4 tests
- `tests/unit/test_decision_math.py` — Phase 5D Scenario 1 regression (pure cost/savings math)
- `tests/unit/test_decision_engine_regression.py` — Phase 5E Section 15 regression (full single-group decision engine)

**Report:** this document.

Total implementation + test code: ~1,170 lines across 12 Python files.

## 2. Files Modified

**None.** No file under `data/`, `research/`, `reports/` (other than this new report), or `scripts/` was opened for writing. The closed Potato ML experiment was not touched.

## 3. Core Folder Structure

```
backend/
    __init__.py
    core/            # pure math -- no I/O, no validation, no group formation
        geo_math.py
        decision_math.py
    models/          # data contracts (dataclasses) and enums -- no logic
        contracts.py
        enums.py
    services/        # orchestration of core/ functions into stateful outcomes
        demand_estimation.py
        decision_engine.py
tests/
    fixtures/        # Phase 5G's D1-D4, G1-G4 fixture data
    unit/            # tests, including Phase 5D/5E worked-example regressions
```

No frontend, API, or database folder was created, per this phase's strict scope. Existing `data/`, `research/`, `reports/`, `scripts/` are untouched.

## 4. Data Contracts Implemented

Directly from Phase 5F Module Interfaces, Section 1, restricted to fields Phase 6A actually needs (no unnecessary fields, no personal information — Step 3): `TaggedLocation` and `TaggedPrice` carry their precision/granularity tag inseparably from their value; `VendorInput` holds only `vendor_id`, location, `q_i` + provenance, individual price, and practical horizon; `CommodityParams`/`ConfigParams`/`ProcurementContext` hold only the parameters Phase 5D's formulas actually consume. `CandidateGroup` represents an **already-formed** group as a plain input — it does not itself perform or imply group formation. **No database schema was designed** — these are plain Python `dataclasses`, no ORM, no persistence.

## 5. Demand Estimation Logic

Implements Phase 5C/5D/5G's hierarchy exactly, with one deterministic tie-break (moving-average-3 for ≥3 records, else last-observed-value) that Phase 5G Section 3 fixed as a named constant (`MOVING_AVERAGE_WINDOW = 3`), not a hardcoded literal (Step 11 item 5). `ValidationError` (an exception) is structurally distinct from an `ABSTAIN` `EstimationResult` (a normal return value) — Step 4's explicit requirement. No ML path is implemented; `EstimationProvenance.ESTIMATE_ML` exists as a defined enum value that no function in this codebase ever produces.

## 6. Mathematical Functions Implemented

Every function in `backend/core/decision_math.py` and `backend/core/geo_math.py` is pure (no file/network access, no validation, no group logic — verified by inspection: none imports `open`, no I/O module, no vendor-validation call). Each is a direct, named translation of one Phase 5D formula, cited by section in its docstring:

| Function | Phase 5D formula |
|---|---|
| `effective_price` | $p^{eff}_{c,t} = p^{wh}_{c,t}(1+m)$ |
| `aggregate_quantity` | $Q_G(k) = k\sum q_i$ |
| `individual_cost_total` | $C^{ind}_{total,G}(k)$ |
| `transport_cost_for_quantity` | $TC_G(k) = TC(\text{tier}(Q_G(k)))$ |
| `collaborative_cost` | $C^{collab}_{G,c}(k)$ |
| `savings` | $Savings_G(k)$ |
| `per_vendor_share` / `individual_savings` | quantity-proportional allocation |
| `consumption_time_days` | $=k$ exactly (Phase 5D Section 6) |
| `break_even_quantity` | $BE_c(t)$, explanatory only |
| `feasible_k_range` | $k \in \{1,\dots,\lfloor\min(F_c,\min H_{i,c})\rfloor\}$ |
| `moq_applicable_and_met` | conditional MOQ check |

**No formula was invented from a function name** — each was located in Phase 5D first, then implemented (Step 5/Step 1). `backend/services/decision_engine.py`'s `evaluate_group` composes these into the fixed four-state routing order from Phase 5D Section 9.

**One ambiguity was found and resolved by deferral, not invention (Step 1's instruction):** Phase 5D Section 9 defines `WAIT_OR_EXPAND_GROUP` purely from a single group's own numbers; Phase 5E Section 12 adds a further pool-superset-search refinement that can *downgrade* a `WAIT_OR_EXPAND_GROUP` to `DO_NOT_BUY_TOGETHER` if no expansion resolves it. Since that refinement requires a pool of candidate groups (Phase 6C's group-formation scope, explicitly excluded from Phase 6A), `evaluate_group` implements **only** Phase 5D's base definition, and its docstring states this boundary explicitly rather than silently doing a partial version of Phase 5E's refinement.

## 7. Geographic Status Handling

`PriceGeographicLevel` (`MANDI_LEVEL` / `DISTRICT_LEVEL_PROXY` / `UNKNOWN_GRANULARITY`) and `VendorLocationStatus` (`VENDOR_SPECIFIC_APPROXIMATE` / `LOCALITY_CENTROID_PROXY` / `MISSING`) are implemented as two **separate** enums (Step 7) — no function anywhere converts one to the other, and `TaggedLocation.is_usable()` is the only logic gate on `VendorLocationStatus`, returning `False` exactly for `MISSING`. The compatibility **graph** (NetworkX, connected components, pairwise edges across a whole vendor pool) is explicitly **not** implemented — only the pairwise `haversine_distance` and group-level `centroid`/`max_distance_from_centroid` functions, which Phase 5D's Stage-2 geographic feasibility check needs for an *already-formed* group. This distinction is stated in `geo_math.py`'s module docstring.

## 8. Fixtures Implemented

All 8 fixtures from `reports/phase5g_implementation_fixtures.md` are implemented in `tests/fixtures/`, each labeled `SIMULATED ILLUSTRATIVE FIXTURE DATA` in its source comment. G3 does not load, read, or reference any file under `data/raw/ceda/` — it constructs two fresh `TaggedPrice` records in-memory, exactly as Phase 5G's binding rule required.

## 9. Test Results

```
20 passed in 0.86s
0 failed, 0 skipped
```

| Suite | Tests | Result |
|---|---|---|
| `test_demand_estimation.py` (D1–D4) | 5 | ✅ all pass |
| `test_geo_status.py` (G1–G4) | 4 | ✅ all pass |
| `test_decision_math.py` (Phase 5D Scenario 1 regression) | 6 | ✅ all pass |
| `test_decision_engine_regression.py` (Phase 5E Section 15 regression) | 5 | ✅ all pass |
| **Total** | **20** | **20 passed, 0 failed, 0 skipped** |

**A real bug was found and fixed during this phase, reported honestly rather than hidden (Step 12):** Phase 5E's Section 15 worked example described vendor positions as small (x, y) kilometer-offsets on an informal flat plane and computed distances with plain Euclidean geometry — valid at sub-2km scale. The first test run fed those same raw numbers directly into the real Haversine formula as if they were latitude/longitude *degrees* (where 1° ≈ 111 km), which placed vendors ~50+ km apart and caused every regression test to fail on the geographic check. **This was a test-authoring error, not a defect in `geo_math.py` or `decision_math.py`.** It was diagnosed by an independent standalone computation (converting the original km-offsets to real lat/lon around an illustrative Hyderabad-area base point, then verifying the resulting Haversine distances reproduced Phase 5E's original stated values — G1≈0.93km, G2≈0.57km, G3≈0.35km, G4≈0.51km, G_all≈1.05km, all matched to within 0.001km), fixed in the test file with the corrected coordinates, and documented in that file's own header comment. A second, smaller error (an eyeballed "~0.43km" expected distance in a G1 test assertion, versus the actual computed 0.4835km) was found and corrected the same way. **Neither Phase 5D's nor Phase 5E's underlying mathematics or reported numbers were changed** — only this phase's own test coordinates and one test's expected-value comment.

## 10. Mathematical Regression Tests

| Source | What was tested | Deferred? |
|---|---|---|
| Phase 5D Section 12, Scenario 1 (5-vendor onion) | Pure cost/savings math table (k=1,2,3,5) | No — fully tested (no coordinates needed) |
| Phase 5E Section 15, candidates G1, G2, G3 | Single-group evaluation → `WAIT_OR_EXPAND_GROUP` (base definition) | Partially — the *trigger* is tested; Phase 5E's superset-search *resolution/downgrade* is **deferred to Phase 6C** (requires group formation) |
| Phase 5E Section 15, candidate G4 | Single-group evaluation → `DO_NOT_BUY_TOGETHER` | No — fully tested |
| Phase 5E Section 15, candidate G_all | Single-group evaluation → `BUY_TOGETHER`, $k^*=5$, savings=₹1,840, per-vendor allocation summing exactly to ₹1,840 | No — fully tested |
| Phase 5E Section 15, **overlap resolution** (G1/G2 overlap, subsumed by G_all) | Which candidate is finally **selected** among overlapping options | **Deferred to Phase 6C** — requires the weighted set-packing final-selection step (Phase 2B Parts 11–12), which requires a pool of candidates that Phase 6A does not generate |
| Phase 5E Section 15, vendor V5 (isolated) / V6 (missing location) | Pool-level isolation ("no compatible pool-mate") | **Partially deferred** — V6's `ABSTAIN` (missing location) is covered by fixture G4's isolation test; V5's "isolated, no pool-mate" outcome specifically requires the compatibility *graph* across the full vendor set, deferred to Phase 6C |

**No worked example was forced into this phase's scope.** Every deferral above is because the underlying capability (group generation, pool-based superset search, overlap resolution) belongs to Phase 6C, not because the test was inconvenient to write.

## 11. Deferred Functionality

| Item | Why deferred | Owning phase |
|---|---|---|
| Compatibility graph construction (NetworkX, connected components) | Explicitly out of Phase 6A scope (Step 1/7) | Phase 6C |
| Within-pool candidate/subset enumeration | Group generation, not group evaluation | Phase 6C |
| Overlap resolution / weighted set packing (final selection) | Needs a pool of already-evaluated candidates | Phase 6C |
| Phase 5E's `WAIT_OR_EXPAND_GROUP` superset-search refinement (downgrade to `DO_NOT_BUY_TOGETHER` if no expansion resolves it) | Needs the same pool | Phase 6C |
| API endpoints, database persistence, frontend, external price retrieval | Explicitly excluded (Phase 6A "DO NOT IMPLEMENT" list) | Phase 6B and beyond |

## 12. Known Limitations

- The Decision Engine's `WAIT_OR_EXPAND_GROUP` output is Phase 5D's *base* definition only — a caller must not treat it as final until Phase 6C's refinement runs on top of it (stated in the module docstring, and in this report).
- `transport_cost_for_quantity` raises `ValueError` if no configured tier covers a group's quantity, rather than guessing — callers must configure a sufficiently large final tier or handle this exception; this is a deliberate "fail loud, don't fabricate" choice (Step 11 item 8), not an oversight.
- Test coordinates use an illustrative Hyderabad-area base point purely to make Phase 5E's original flat-plane km-offsets convertible into valid degrees for the real Haversine function — this base point is not itself a claim about any real location.
- No performance/scalability testing was done — pure functions on ≤7-vendor fixtures run in milliseconds, and Phase 6A makes no claim beyond that.

## 13. Consistency Audit

| # | Check | Result |
|---|---|---|
| 1 | Phase 5D formulas preserved exactly | ✅ every function docstring cites its exact source section; no formula altered |
| 2 | No Phase 5E group-generation logic prematurely implemented | ✅ no graph, no connected components, no subset enumeration anywhere in `backend/` |
| 3 | No ML introduced | ✅ `EstimationProvenance.ESTIMATE_ML` defined, never produced |
| 4 | No external data dependency exists | ✅ no network/file I/O in any core or service module |
| 5 | D1–D4 tests pass | ✅ `test_demand_estimation.py`, 5/5 |
| 6 | G1–G4 tests pass | ✅ `test_geo_status.py`, 4/4 |
| 7 | `ABSTAIN` ≠ `VALIDATION ERROR` | ✅ distinct types (`EstimationResult` vs. raised `ValidationError`); tested explicitly (`test_d3_and_d4_are_distinguishable_outcomes`) |
| 8 | Geographic proxy ≠ precise location | ✅ `VendorLocationStatus`/`PriceGeographicLevel` kept as two separate enums; no conversion function exists |
| 9 | Mathematical functions independently testable | ✅ every `decision_math`/`geo_math` function takes plain values, no fixtures/mocks required |
| 10 | Existing research files remain untouched | ✅ confirmed — none opened for writing this phase |
| 11 | Closed Potato ML experiment remains untouched | ✅ confirmed — `data/raw/ceda/` never read or written this phase; G3 fixture constructs fresh in-memory data only |
| 12 | No frontend/API/database created | ✅ confirmed — only `backend/{core,models,services}` and `tests/` exist |

**No inconsistency found.** The one real defect discovered (Section 9's coordinate-unit mismatch) was in test authoring, not in the audited mathematics, and is fully documented rather than silently patched over.

## 14. Recommendation for Phase 6B

**Phase 6A is complete and stops here, per its own final rule.** Phase 6B should extend the validation/eligibility pipeline (Phase 5E Section 4) around the demand-estimation and decision-engine foundation now in place — specifically, wiring `estimate_demand`'s `ABSTAIN`/`ValidationError` outcomes and `TaggedLocation.is_usable()` into a batch-level eligibility filter that processes multiple vendors at once (extending, not duplicating, the isolation behavior already unit-tested in fixture G4). Phase 6B should **not** yet build the compatibility graph or group generation (still Phase 6C) or any API/frontend layer. Every function built in this phase is ready to be called by that eligibility pipeline without modification.

---

**Files read for this phase:** `reports/phase5d_mathematical_decision_model.md`, `reports/phase5e_group_formation_design.md`, `reports/phase5f_system_architecture.md`, `reports/phase5f_module_interfaces.md`, `reports/phase5f_traceability_and_implementation_plan.md`, `reports/phase5g_implementation_fixtures.md`, `reports/phase5g_fixture_test_mapping.md`.
**Files modified:** none outside `backend/`, `tests/`, and this new report.
