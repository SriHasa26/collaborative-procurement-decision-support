# Phase 6C — Group Formation Engine

**Date:** 2026-09-14
**Scope:** Implement Phase 2B's graph-based candidate-group generation exactly as specified — compatibility graph, connected components, within-pool subset enumeration. Structural candidates only; no cost/savings/MOQ/freshness decision, no overlap resolution, no final selection.

---

## 1. Phase Objective

Take the eligible-vendor output of Phase 6B and generate every structurally-possible collaborative candidate group for one commodity/context, using the exact algorithm Phase 2B already designed and Phase 5E already restated — not a redesign, not a substitute algorithm.

## 2. Authoritative Rules Implemented

| Rule | Source |
|---|---|
| Pairwise geographic compatibility, $\text{dist}(i,j) \le 2D_{max}$ (exact factor of 2, proven via the triangle inequality) | Phase 2B Part 6B |
| Connected components as candidate pools; component membership is *necessary*, not *sufficient*, for group feasibility (the "chain caveat") | Phase 2B Part 6B; Phase 5E Section 5 |
| Full subset enumeration (size ≥ 2) within each pool, V1 default — not maximal cliques, not greedy, not clustering | Phase 2B Part 15 Step 3 |
| Minimum group size = 2 (a singleton is not a collaboration) | Phase 2B Part 2 |
| One commodity/context per optimization run | Phase 5E Section 3 |
| No group-level economic/feasibility decision at this stage | Phase 5F's implementation order (`reports/phase5f_traceability_and_implementation_plan.md`, Section 4) places candidate generation strictly before the Decision Engine |

## 3. Existing Phase 6A/6B Components Reused

Inspected directly before writing any code (`backend/core/geo_math.py`, `backend/services/decision_engine.py`, `backend/models/contracts.py`, `backend/models/batch_contracts.py`) per this phase's Step 1:

| Component | Reused as-is |
|---|---|
| `geo_math.haversine_distance`, `geo_math.is_within_radius` | ✅ Called directly by `compatibility.py` — **no second Haversine implementation exists anywhere in this codebase** |
| `VendorInput`, `TaggedLocation`, `VendorLocationStatus` | ✅ Unchanged |
| `CandidateGroup` (`group_id` + `members`) | ✅ Reused exactly as Phase 6A's `evaluate_group` already consumes it — Phase 6C wraps it with metadata (`CandidateGroupRecord`) rather than inventing a competing shape |
| Phase 6B's eligibility boundary | ✅ Phase 6C's entry point takes an already-eligible `Sequence[VendorInput]`; no validation or demand estimation is re-run |

Confirmed by inspection: `geo_math.centroid`/`geo_math.max_distance_from_centroid` (the **group-level** feasibility check used inside `evaluate_group`) are never called from `compatibility.py` or `group_formation.py` — this phase strictly uses only the **pairwise** functions, preserving the distinction Phase 2B's own audit already established (Section 8 below elaborates).

## 4. Files Created

- `backend/models/group_formation_contracts.py` — `CandidateGroupRecord`, `PoolDiagnostic`, `GroupFormationResult`
- `backend/services/compatibility.py` — `are_geographically_compatible`, `build_compatibility_graph`, `VendorContractViolation`
- `backend/services/group_formation.py` — `find_compatible_pools`, `enumerate_candidate_groups`, `form_candidate_groups`
- `tests/fixtures/group_formation_fixtures.py`
- `tests/unit/test_compatibility.py`, `tests/unit/test_group_formation.py`
- `requirements.txt` (new — see Section 6)
- This report

## 5. Files Modified

**None** under `backend/`, `tests/`, `data/`, `research/`, or any prior `reports/` file. Phase 6A and Phase 6B's own files were read but not written to.

## 6. NetworkX Dependency Status

**NetworkX was not previously installed or recorded anywhere in the project.** Checked directly (`import networkx` failed; no `requirements.txt`/`pyproject.toml` existed) before installing. Installed via `pip install networkx` (version 3.6.1) and recorded in a new `requirements.txt` at the project root, with a comment explaining exactly why it was added (Phase 6C's compatibility graph) and noting that `pytest` — already an implicit dependency since Phase 6A — was formalized in the same file for completeness, not as a new, unrelated addition. **No other package was added.**

## 7. Commodity/Context Isolation

**No new isolation logic was written — the invariant is inherited by construction, not re-implemented.** Phase 6B's `evaluate_procurement_context(context: ProcurementContext, ...)` already scopes every batch call to exactly one `(commodity_id, date)` pair; its `eligible_vendors` output is therefore already commodity-pure. `form_candidate_groups` takes `commodity_id`/`context_date` as explicit parameters (not re-derived from vendor data) and has no code path that could merge two calls' vendor lists — verified directly in `test_6_commodity_isolation_tomato_and_potato_never_mixed`, which runs two independent calls and confirms their vendor-ID sets are disjoint.

## 8. Geographic Compatibility Rule

Implemented in `are_geographically_compatible(a, b, d_max_km)`: **pairwise and geographic only** — no social, reputation, purchase-history, demand-similarity, price-similarity, or ML-based factor is considered anywhere (verified by inspection: the function's only inputs are two `VendorInput` locations and `d_max_km`). This directly matches Phase 6C's Step 4 instruction and Phase 2B/5E's own scope.

## 9. Exact 2 × D_max Implementation

```python
distance_km = geo_math.haversine_distance(...)
return geo_math.is_within_radius(distance_km, 2.0 * d_max_km)
```

**The factor of 2 is explicit and tested directly** (`test_2x_dmax_factor_is_exact_not_dmax_alone`), using a pair deliberately placed between $D_{max}$ (2.0 km) and $2D_{max}$ (4.0 km) — a pair that would be *incompatible* under a (wrong) plain-$D_{max}$ rule but is correctly *compatible* under the authoritative $2D_{max}$ rule. **No bounding box, nearest-neighbor limit, or alternative threshold was introduced.**

## 10. Haversine Reuse

`compatibility.py` imports `backend.core.geo_math` and calls `haversine_distance`/`is_within_radius` directly — the exact same functions Phase 6A's `evaluate_group` already uses for its (different) group-level centroid check. **Confirmed by code inspection: zero duplicate distance-calculation logic exists in this codebase.**

**Lesson from Phase 6A applied deliberately (per this phase's own Step 6 instruction):** every test coordinate in `tests/fixtures/group_formation_fixtures.py` is a real `(lat, lon)` pair, converted from an intended kilometer offset using the same flat-plane method Phase 6A's regression test already verified accurate at this scale — and every resulting distance was independently computed in Python *before* being written into the fixture file (not estimated afterward), avoiding the exact mistake Phase 6A made and documented.

## 11. Compatibility Graph Design

`build_compatibility_graph` builds an `nx.Graph` with vendor IDs as nodes (the full `VendorInput` object attached as node data for traceability) and an edge only where `are_geographically_compatible` is true. **It is a compatibility graph only** — no edge weight, no routing information, no savings figure, no social relationship is attached (Step 7's explicit list of what this is *not*). A defensive guard (`VendorContractViolation`) rejects, rather than silently mishandling, a duplicate `vendor_id` (which would otherwise collide into one graph node) or an unusable/out-of-range location (which would otherwise produce a numerically meaningless distance) — this is a fail-clearly contract check for direct misuse, **not** a re-implementation of Phase 6B's eligibility pipeline (no reason codes, no `ABSTAIN` routing occur here).

## 12. Connected-Component Logic

`find_compatible_pools` calls `nx.connected_components` and returns pools sorted deterministically. **The distinction this phase's Step 8 requires is preserved explicitly, in both code and tests:** a connected component is a candidate *pool* — a necessary-condition search-space reduction — never a claim of group-level feasibility, and never a `BUY_TOGETHER` decision. `test_4` proves this concretely: a 3-vendor chain (A–B, B–C connected; A–C *not*) forms **one** connected component, yet A and C are explicitly asserted to have **no direct edge** — the pool and the pairwise relation are checked and asserted separately, not conflated.

## 13. Candidate Enumeration Method

`enumerate_candidate_groups` performs **full subset enumeration** of size ≥ 2 over the pool — Phase 2B's V1 default, not maximal cliques. **This is verified, not assumed**, by `test_8`: using the same 3-vendor chain (where A–C is *not* a direct edge), the enumeration is confirmed to still produce **both** `{A,C}` and `{A,B,C}` — subsets that a clique-based method would have excluded. This is the sharpest possible test of "do not assume clique-based behavior," since a fully-connected triangle fixture would not have distinguished the two approaches at all.

## 14. Combinatorial Complexity Discussion

Nominal count restated unchanged from Phase 2B Part 5 ($2^n - n - 1$: 1,013 at $n{=}10$; 32,752 at $n{=}15$; 1,048,555 at $n{=}20$) — no new complexity claim is made. **Primary control, exactly as Phase 2B specifies:** geographic pruning via the proven $2D_{max}$ triangle-inequality result, which partitions the vendor set into independent pools *before* any subset is generated, so combinatorial growth applies only within each (typically much smaller) pool. **No universal scalability claim is made** — the documented scope remains ~5–20 vendors, restated here, not re-derived.

**Large-pool diagnostic (Step 11):** `PoolDiagnostic.large_pool_warning` fires at `LARGE_POOL_WARNING_THRESHOLD = 15` — chosen as Phase 2B Part 5's own explicitly-tabulated reference point (32,752 candidates), not an arbitrary new number. **This is a non-blocking, informational flag only** — `test_large_pool_triggers_non_blocking_diagnostic_without_dropping_anyone` confirms a 15-vendor pool still produces the full, correct 32,752 candidates with every vendor accounted for; nothing is truncated, dropped, or silently limited.

## 15. Candidate-Group Contract

**No new competing "candidate group" shape was invented.** `CandidateGroupRecord` wraps Phase 6A's existing, unmodified `CandidateGroup` (`group_id` + `members`) with exactly the traceability metadata Step 13/14 ask for (`commodity_id`, `context_date`, `source_pool_id`, `pool_vendor_ids`) — and **no final-decision field** (no `BUY_TOGETHER`, no savings, no `selected` flag) appears anywhere in it, verified by inspection of the dataclass definition itself.

## 16. Deterministic Ordering Strategy

Enforced at three points, all keyed on `vendor_id` (never on insertion order, object identity, or Python's default set/dict iteration): (1) graph nodes are added in `vendor_id`-sorted order; (2) connected components are sorted by their own sorted-vendor-id tuple; (3) `group_id` is derived from the sorted member-ID join (`"+".join(sorted(vendor_ids))`), which **also** guarantees no duplicate candidate can ever be produced under a different member order — `[A,B]` and `[B,A]` always collapse to the identical `group_id` by construction, not by a post-hoc deduplication pass. Verified by `test_9` (identical output across repeated runs, including with deliberately shuffled input order) and `test_12` (`_group_id(["A","B"]) == _group_id(["B","A"])`, plus a full uniqueness check over a real 5-vendor pool's 26 candidates).

## 17. Traceability Strategy

Every `CandidateGroupRecord` carries `source_pool_id` and `pool_vendor_ids`, so the chain **Candidate Group → Source Pool → Eligible Vendors → Phase 6B** is fully reconstructable from the record alone. **No explanation-generator module was built** (correctly out of scope, per Step 14's own instruction) — only the data needed to support one later.

**Step 15's WAIT_OR_EXPAND_GROUP boundary, addressed explicitly:** Phase 5F's own implementation-order document (`reports/phase5f_traceability_and_implementation_plan.md`, Section 4) places candidate generation strictly *before* the Decision Engine's per-candidate evaluation and *before* the WAIT/EXPAND resolver — confirming this ordering was inspected, not assumed, before deciding what Phase 6C should and should not do. **No superset/subset relationship is precomputed or stored beyond what `source_pool_id` already exposes.** A future Phase 6D resolver can trivially find "every other candidate sharing this candidate's pool" by filtering on `source_pool_id` and comparing member sets — this module deliberately does not compute or cache that relationship itself, so as not to implement any fragment of the actual WAIT/EXPAND *decision* logic prematurely.

## 18. Tests Implemented

| Test | Covers |
|---|---|
| `test_1`–`test_3` (`test_compatibility.py`) | Exact compatible pair, exact incompatible pair, boundary inclusivity at exactly $2D_{max}$ |
| `test_2x_dmax_factor_is_exact_not_dmax_alone` | Regression guard against the specific mistake Step 5 warns about |
| 3 defensive-misuse tests | Duplicate `vendor_id`, missing location, out-of-range location — all raise `VendorContractViolation` |
| `test_4`–`test_12` (`test_group_formation.py`) | Chain/non-pairwise-transitivity, disconnected pools, commodity isolation, singleton exclusion, non-clique enumeration, determinism, ineligible-vendor misuse, Phase 5E structural reproduction, no-duplicate-candidates |
| 6 additional edge tests | Empty collection, single vendor, all mutually incompatible, all in one pool, large-pool diagnostic (fires), small-pool diagnostic (does not fire) |

## 19. Test Results

```
63 passed, 0 failed, 0 skipped
```

| Suite | Tests | Result |
|---|---|---|
| Phase 6A (4 files, unchanged) | 20 | ✅ all pass |
| Phase 6B (2 files, unchanged) | 21 | ✅ all pass |
| Phase 6C — `test_compatibility.py` | 7 | ✅ all pass |
| Phase 6C — `test_group_formation.py` | 15 | ✅ all pass |
| **Total** | **63** | **63 passed, 0 failed, 0 skipped** |

No failure was hidden; no test was skipped or marked `xfail`.

## 20. Edge Cases

Empty eligible collection; exactly one eligible vendor (a trivial singleton); all vendors mutually incompatible (all singletons, zero candidates); all vendors in one pool; a genuinely large pool (15 vendors, 32,752 candidates, all correctly generated, diagnostic fires); a small pool confirming the diagnostic does *not* fire below threshold; direct-misuse cases (duplicate ID, missing location, malformed coordinate, an ineligible vendor bypassing Phase 6B entirely) — every misuse case fails clearly via `VendorContractViolation` rather than silently producing a wrong graph.

## 21. Deferred Functionality

Unchanged from the explicit exclusion list this phase was given: per-candidate cost/savings/MOQ/freshness evaluation (calling `evaluate_group`), the actual `BUY_TOGETHER`/`WAIT_OR_EXPAND_GROUP`/`DO_NOT_BUY_TOGETHER` decisions, Phase 5E's superset-search WAIT/EXPAND *resolution* (structural support only is provided, per Section 17), overlap resolution / final weighted-set-packing selection, any API/database/frontend work. All remain Phase 6D/6E's scope.

## 22. Final Consistency Audit

| # | Check | Result |
|---|---|---|
| 1 | Phase 2B graph-based design preserved | ✅ compatibility graph → connected components → subset enumeration, unchanged |
| 2 | Exact $2D_{max}$ pruning preserved | ✅ Section 9, tested explicitly |
| 3 | Existing Haversine code reused | ✅ Section 10 |
| 4 | No duplicate geographic-distance implementation | ✅ confirmed by inspection |
| 5 | Compatibility geographic only | ✅ Section 8 |
| 6 | Compatibility remains pairwise | ✅ `are_geographically_compatible(a, b, ...)` — two vendors only |
| 7 | Connected component ≠ final feasible group | ✅ `test_4`, Section 12 |
| 8 | Connected component ≠ `BUY_TOGETHER` decision | ✅ no decision-state code exists anywhere in Phase 6C |
| 9 | Group-level feasibility not implemented here | ✅ `evaluate_group` is never called from any Phase 6C module |
| 10 | No cost/savings formulas modified | ✅ `decision_math.py` untouched |
| 11 | No ML introduced | ✅ confirmed |
| 12 | No clustering introduced | ✅ confirmed — only graph connected-components, an exact method, is used |
| 13 | No greedy replacement algorithm | ✅ confirmed |
| 14 | No routing optimization | ✅ confirmed |
| 15 | Vendors never grouped across commodities | ✅ Section 7, `test_6` |
| 16 | Candidate generation deterministic | ✅ Section 16, `test_9` |
| 17 | No duplicate candidate groups | ✅ Section 16, `test_12` |
| 18 | Singleton collaborative groups not generated | ✅ `test_7`, minimum size 2 enforced |
| 19 | No overlap resolution implemented | ✅ confirmed |
| 20 | No final group selection implemented | ✅ confirmed |
| 21 | Phase 6A tests still pass | ✅ 20/20 |
| 22 | Phase 6B tests still pass | ✅ 21/21 |
| 23 | Existing research files untouched | ✅ confirmed |
| 24 | Closed Potato ML experiment untouched | ✅ confirmed — no file under `data/raw/ceda/` read or written this phase |

**No inconsistency found.**

## 23. Recommendation for Phase 6D

Phase 6D should take `GroupFormationResult.candidate_groups` and, for each `CandidateGroupRecord.candidate` (a `CandidateGroup` already in the exact shape Phase 6A's `evaluate_group` consumes), call `evaluate_group` unmodified to obtain the real decision state. Phase 6D should then implement Phase 5E Section 12's superset-search refinement, using `source_pool_id`/`pool_vendor_ids` to find, for any candidate flagged `WAIT_OR_EXPAND_GROUP`, whether another candidate sharing the same pool achieved `BUY_TOGETHER` — exactly the lookup this phase's traceability metadata was designed to make trivial. Overlap resolution / final selection (Phase 2B Parts 11–12) remains Phase 6E's job, to run only after Phase 6D's per-candidate evaluation is complete. No API, database, or frontend work should begin before Phase 6D/6E close the decision-evaluation loop.

---

**Files read for this phase:** `research/phase2a_mathematical_model.md`, `research/phase2b_algorithm_selection.md`, `reports/phase5d_mathematical_decision_model.md`, `reports/phase5e_group_formation_design.md`, `reports/phase5e_phase2b_reconciliation.md`, `reports/phase5f_system_architecture.md`, `reports/phase5f_module_interfaces.md`, `reports/phase5f_traceability_and_implementation_plan.md`, `reports/phase5g_implementation_fixtures.md`, `reports/phase5g_fixture_test_mapping.md`, `reports/phase6a_core_foundation_report.md`, `reports/phase6b_validation_and_eligibility_report.md`, and the actual `backend/` source files listed in Section 3.
**Files modified:** none outside the new `backend/`, `tests/` additions, `requirements.txt`, and this report.
