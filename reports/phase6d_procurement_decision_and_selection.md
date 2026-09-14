# Phase 6D — Procurement Decision Evaluation and Final Selection

**Date:** 2026-09-14
**Scope:** Evaluate every Phase 6C candidate group via Phase 6A's unmodified `evaluate_group`; apply Phase 5E Section 12's WAIT_OR_EXPAND_GROUP superset resolution within the same compatibility pool only; resolve final vendor-exclusivity overlap via exact exhaustive search; select the lexicographically optimal disjoint set of BUY_TOGETHER groups (savings primary, coverage tie-break only). No new candidate groups, no new math, no ML/API/database/frontend.

---

## 1. Phase Objective

Take Phase 6C's already-generated candidate groups for one procurement context and produce the final, authoritative, fully-traceable batch decision: which candidates are BUY_TOGETHER / WAIT_OR_EXPAND_GROUP / DO_NOT_BUY_TOGETHER / ABSTAIN, which WAIT_OR_EXPAND_GROUP results are resolved or terminated by an already-generated pool superset, and which disjoint subset of BUY_TOGETHER candidates is finally selected under Phase 2B's lexicographic objective. This phase adds no new decision logic beyond what Phase 5D/5E/2B already specify — it wires existing, authoritative pieces together for the first time.

## 2. Authoritative Rules Implemented

| Rule | Source |
|---|---|
| Per-candidate decision, unmodified | Phase 5D Section 9, via `decision_engine.evaluate_group` |
| WAIT_OR_EXPAND_GROUP superset refinement: keep WAIT if a same-pool superset is BUY_TOGETHER, else downgrade to DO_NOT_BUY_TOGETHER | Phase 5E Section 12 |
| Superset search confined to `source_pool_id` | Phase 5E Section 12; Phase 6C's own pool traceability design |
| Mutual exclusivity: Σx_G ≤ 1 per vendor across selected groups | Phase 2B Part 12 |
| Lexicographic objective: maximize savings (primary), then vendor coverage (secondary, tie-break only — never a weighted composite) | Phase 2B Part 11 |
| Exact exhaustive search over combinations (V1 default), appropriate at ~5–20 vendor scope | Phase 2B Part 15 Step 6 |
| No third-level criterion specified — a neutral, documented, non-mathematical fallback is required only if both above tie exactly | Phase 2B Part 11 (silent on a further level); this phase's own explicit instruction not to invent a new optimization objective |

## 3. Existing Phase 6A/6B/6C Components Reused

Inspected directly before writing any code:

| Component | Reused as-is |
|---|---|
| `decision_engine.evaluate_group` | ✅ Called unmodified, once per candidate — **no cost/savings/MOQ/freshness/allocation formula is reimplemented anywhere in Phase 6D** |
| `GroupDecisionResult` | ✅ Embedded verbatim inside the new `EvaluatedGroupResult` wrapper — never mutated |
| `CandidateGroupRecord` / `GroupFormationResult` (Phase 6C) | ✅ Consumed exactly as produced — `source_pool_id`/`pool_vendor_ids` drive the superset search with no new pool concept introduced |
| `DecisionState` enum | ✅ Unchanged; no fifth state introduced |

Confirmed by inspection: no file under `backend/core/` (`geo_math.py`, `decision_math.py`) was modified, and neither is imported by any new Phase 6D file — all mathematics flows exclusively through `evaluate_group`.

## 4. Files Created

- `backend/models/decision_contracts.py` — `EvaluatedGroupResult`, `FinalSelectionResult`
- `backend/services/decision_evaluation.py` — `evaluate_candidate_groups`, `resolve_wait_or_expand`
- `backend/services/selection.py` — `_is_disjoint`, `_select_best_combination`, `select_final_groups`, `explain`
- `backend/services/batch_decision.py` — `run_procurement_decision` (thin orchestration only)
- `tests/fixtures/decision_selection_fixtures.py`
- `tests/unit/test_decision_evaluation.py`, `tests/unit/test_selection.py`, `tests/unit/test_batch_decision.py`
- This report

## 5. Files Modified

**None** under `backend/core/`, `backend/services/decision_engine.py`, `backend/services/group_formation.py`, `backend/models/contracts.py`, `backend/models/group_formation_contracts.py`, `tests/fixtures/group_formation_fixtures.py`, `data/`, `research/`, or any prior `reports/` file. Phase 6A/6B/6C's own files were read but not written to.

## 6. Candidate Group Evaluation Flow

`evaluate_candidate_groups(formation_result, commodity, context, config)` iterates `formation_result.candidate_groups` (Phase 6C's own list, in its own deterministic order) and calls `decision_engine.evaluate_group(record.candidate, commodity, context, config)` once per candidate — no filtering, reordering, or new candidate is introduced at this step. Each raw result is wrapped in an `EvaluatedGroupResult` with `final_decision_state` initialized to the base `decision.decision_state`, then the whole list is passed through `resolve_wait_or_expand` before being returned.

## 7. Decision-State Handling

All four `DecisionState` values pass through unchanged in meaning:
- **BUY_TOGETHER** and **ABSTAIN**: no refinement applies; `final_decision_state == decision.decision_state` always.
- **DO_NOT_BUY_TOGETHER**: no refinement applies (Phase 5E Section 12 only concerns WAIT_OR_EXPAND_GROUP results); passes through unchanged.
- **WAIT_OR_EXPAND_GROUP**: the only state subject to refinement — see Section 8.

`GroupDecisionResult` (Phase 6A's object) is **never mutated**; embedded as-is inside `EvaluatedGroupResult.decision` for permanent audit traceability of the base-definition answer, per Phase 5D Section 9's own honest finding.

## 8. WAIT_OR_EXPAND_GROUP Implementation

`resolve_wait_or_expand` groups all evaluated results by `source_pool_id` (a single `defaultdict` pass), then for every result whose **base** decision is WAIT_OR_EXPAND_GROUP:
1. Compares its vendor-ID set against every other result sharing the same `source_pool_id`.
2. Keeps only strict supersets (`this_vendors < other_vendors`) whose own base decision is BUY_TOGETHER.
3. If ≥ 1 such superset exists: `final_decision_state` **remains** WAIT_OR_EXPAND_GROUP (never silently upgraded to BUY_TOGETHER — that upgrade belongs to the superset candidate itself, evaluated and eligible independently); `resolving_superset_group_ids` records which already-generated candidate(s) resolved it.
4. If none exists: `final_decision_state` becomes DO_NOT_BUY_TOGETHER (Phase 5E Section 12's termination rule), with an explicit `expansion_reason`.

Implementation is `dataclasses.replace()` on the wrapper only — the embedded `GroupDecisionResult` object is identical (by value) before and after, verified directly by `test_resolve_wait_or_expand_does_not_mutate_input_objects`.

## 9. Superset Search Logic

Superset comparison is plain Python `set` comparison (`this_vendors < other_vendors`) over `vendor_ids` tuples already computed once per candidate — no graph search, no recursion, no new group is ever constructed. The search space for one WAIT candidate is exactly "every other candidate already in `formation_result.candidate_groups` sharing its `source_pool_id`" — a finite, already-enumerated list from Phase 6C.

## 10. Pool Isolation

Enforced structurally: the `by_pool` lookup is keyed on `source_pool_id`, so a candidate in a different pool is never even considered, regardless of whether its vendor set would otherwise look like a superset. `test_t7_no_cross_pool_expansion` proves this directly with a constructed pair that IS a real superset by vendor-ID but lives in a different pool — the WAIT result still terminates to DO_NOT_BUY_TOGETHER, confirming the pool boundary is honored even when the "wrong" answer would otherwise be easy to produce by accident.

## 11. Termination Behavior

Confirmed via `test_t6_unsuccessful_expansion_terminates_to_do_not_buy_together`: a WAIT_OR_EXPAND_GROUP candidate in a pool containing no larger candidate at all (the pool has exactly the group's own 2 members) terminates to DO_NOT_BUY_TOGETHER rather than remaining an open-ended, unresolved wait — Phase 5E Section 12's own explicit rule, not a new invented fallback.

## 12. Final Candidate Eligibility

Only candidates whose **final** decision state is BUY_TOGETHER are ever passed into `_select_best_combination`. This falls out of the code by construction (`select_final_groups` partitions by `final_decision_state` before calling the search), and is additionally never violated by the refinement step itself, since `resolve_wait_or_expand` has no code path that sets `final_decision_state` to BUY_TOGETHER — it can only leave a WAIT candidate as WAIT or downgrade it to DO_NOT_BUY_TOGETHER. `test_t13_wait_or_expand_excluded_from_selection_even_with_high_savings` and `test_t12_abstain_excluded_from_optimization` confirm ABSTAIN and WAIT_OR_EXPAND_GROUP candidates are excluded by **state**, never by comparing savings figures.

## 13. Overlap-Resolution Method

`_is_disjoint` checks pairwise vendor-set disjointness across a candidate combination via simple set-union accumulation. `_select_best_combination` enumerates **every** subset size (`0` through `n`) of the BUY_TOGETHER candidate list via `itertools.combinations`, filters to disjoint combinations only, and tracks the best `(total_savings, coverage)` key — Phase 2B Part 15 Step 6's V1 exact-exhaustive-search default, not ILP, not a greedy/heuristic packing method.

## 14. Lexicographic Objective

The comparison key is the Python tuple `(total_savings, coverage)`, compared with `>`/`==` directly — tuple comparison is itself lexicographic (first element decides unless exactly equal), so savings strictly dominates coverage by construction, never a weighted sum. `test_t9_savings_priority_over_coverage` proves this with a case where the higher-coverage alternative has strictly lower savings and loses outright; `test_t10_coverage_tie_break_when_savings_are_equal` proves coverage only breaks an EXACT savings tie.

## 15. Deterministic Tie-Breaking

If multiple combinations tie at the exact same `(savings, coverage)` key (a genuine third-level tie Phase 2B does not resolve), the fallback is `min()` over each combination's sorted group-ID tuple — a neutral, content-derived, non-mathematically-meaningful rule, documented explicitly in `tie_break_note` and in `selection.py`'s own docstring as an implementation-level choice, never presented as a new optimization criterion. Verified by `test_third_level_neutral_tie_break_on_exact_double_tie`. When no tie exists, `tie_break_note` says so explicitly rather than fabricating a tie-break narrative.

## 16. Data Contracts Created

- `EvaluatedGroupResult` — wraps Phase 6A's `GroupDecisionResult` unchanged (`decision` field) plus `final_decision_state`, pool/vendor traceability fields, `resolving_superset_group_ids` (default `()`), `expansion_reason` (default `""`). No field competes with or duplicates `GroupDecisionResult`'s own fields.
- `FinalSelectionResult` — the batch-level output: selected/non-selected/waiting/rejected/abstained partitions (all `EvaluatedGroupResult` tuples), `total_savings_rs`, `total_vendor_coverage`, `tie_break_note`.

Neither contract is a database schema, an API response model, or a UI view model — plain, frozen dataclasses only, consistent with every prior phase's contract style.

## 17. Test Fixtures

`tests/fixtures/decision_selection_fixtures.py` reuses Phase 5E Section 15's own worked example (imported via Phase 6C's `group_formation_fixtures.V1/V2/V3/V4/V7`, already regression-verified) for every scenario that example's structure already covers (BUY_TOGETHER, DO_NOT_BUY_TOGETHER, WAIT_OR_EXPAND_GROUP-with-a-real-superset). New fixtures were added only where genuinely new structure was needed: an ABSTAIN vendor (missing `q_i`), a 2-vendor pool with no possible superset (termination case), and `make_buy_together`/`make_wait_or_expand`/`make_do_not_buy`/`make_abstain` builders for the pure selection-layer tests, which deliberately bypass `evaluate_group` since `selection.py`'s contract only needs `group_id`/`savings_rs`/`vendor_ids`/`final_decision_state` — using minimal, explicitly-labeled fixtures there rather than re-deriving new economics for every combination tested.

## 18. Test Cases (T1–T14)

| # | Case | File | Result |
|---|---|---|---|
| T1 | BUY_TOGETHER candidate evaluation | `test_decision_evaluation.py` | ✅ |
| T2 | DO_NOT_BUY_TOGETHER candidate evaluation | `test_decision_evaluation.py` | ✅ |
| T3 | ABSTAIN candidate evaluation | `test_decision_evaluation.py` | ✅ |
| T4 | WAIT_OR_EXPAND_GROUP base decision, before resolution | `test_decision_evaluation.py` | ✅ |
| T5 | Successful superset expansion (same pool) | `test_decision_evaluation.py` | ✅ |
| T6 | Unsuccessful expansion / termination | `test_decision_evaluation.py` | ✅ |
| T7 | Different pools — no cross-pool expansion | `test_decision_evaluation.py` | ✅ |
| T8 | Simple overlap | `test_selection.py` | ✅ |
| T9 | Savings priority over coverage | `test_selection.py` | ✅ |
| T10 | Coverage tie-break | `test_selection.py` | ✅ |
| T11 | Non-overlapping groups: both selected | `test_selection.py` | ✅ |
| T12 | ABSTAIN exclusion from optimization | `test_selection.py` | ✅ |
| T13 | WAIT_OR_EXPAND_GROUP exclusion from selection | `test_selection.py` | ✅ |
| T14 | Determinism across repeated runs | `test_selection.py` (selection layer), `test_batch_decision.py` (full pipeline) | ✅ |

Plus: one additional test for the neutral third-level tie-break path (not separately numbered in the task spec, but a real code path otherwise left untested), `explain()` text checks, a non-mutation guard, and an integration test (`test_batch_decision.py`) running the real, complete 26-candidate enumeration of the 5-vendor pool through Phase 6C's actual `form_candidate_groups` and the full Phase 6D pipeline end-to-end.

## 19. Test Results

```
20 new tests passed, 0 failed, 0 skipped
83 total: passed, 0 failed, 0 skipped
```

| Suite | Tests | Result |
|---|---|---|
| Phase 6A (4 files, unchanged) | 20 | ✅ all pass |
| Phase 6B (2 files, unchanged) | 21 | ✅ all pass |
| Phase 6C (2 files, unchanged) | 22 | ✅ all pass |
| Phase 6D — `test_decision_evaluation.py` | 8 | ✅ all pass |
| Phase 6D — `test_selection.py` | 10 | ✅ all pass |
| Phase 6D — `test_batch_decision.py` | 2 | ✅ all pass |
| **Total** | **83** | **83 passed, 0 failed, 0 skipped** |

No failure was hidden; no test was skipped or marked `xfail`.

## 20. Regression Results

All 63 pre-existing tests (Phase 6A + 6B + 6C) pass unchanged, confirmed by a full `pytest -q` run after every new file was added — no existing test was modified to make it pass.

## 21. Explicit Non-Goals (Confirmed Not Implemented)

No ML, clustering, greedy heuristic, or genetic algorithm anywhere; no new Haversine or cost/savings/MOQ formula; no dynamic candidate-group creation; no cross-pool superset search; no silent WAIT→BUY_TOGETHER upgrade; no weighted composite of savings and coverage; no ILP solver; no API endpoint; no database schema or persistence; no frontend code; no reopening of the closed Potato ML experiment or its underlying CEDA/Agmarknet data — confirmed by inspection, no file under `data/raw/ceda/` or the ML experiment's own modules was read or written this phase.

## 22. Limitations

The exhaustive overlap-resolution search is `O(2^m)` in the number of BUY_TOGETHER candidates surviving to final eligibility — appropriate and explicitly scoped to this project's ~5–20 vendor target, not claimed as an internet-scale method (restating Phase 2B Part 15 Step 6's own stated scope, not a new caveat). The third-level tie-break (sorted group-ID) is deliberately non-mathematical and would need a project-level decision (not an algorithmic one) if a real deployment ever needed a principled fourth-level rule — Phase 2B does not specify one, and this phase does not invent one beyond a documented, neutral default.

## 23. Final Consistency Audit

| # | Check | Result |
|---|---|---|
| 1 | Phase 6A's `evaluate_group` reused unmodified | ✅ Section 3, 6 |
| 2 | No cost/savings/MOQ/allocation formula reimplemented | ✅ confirmed by inspection — no import of `decision_math`/`geo_math` in any new file |
| 3 | `GroupDecisionResult` never mutated | ✅ Section 7, `test_resolve_wait_or_expand_does_not_mutate_input_objects` |
| 4 | No new candidate group ever created | ✅ Section 6, 9 |
| 5 | Superset search confined to same `source_pool_id` | ✅ Section 8, 10; `test_t7` |
| 6 | No cross-pool expansion | ✅ `test_t7_no_cross_pool_expansion` |
| 7 | WAIT never silently upgraded to BUY_TOGETHER | ✅ Section 8, 12; `test_t5` |
| 8 | Termination rule applied when no resolving superset exists | ✅ Section 11; `test_t6` |
| 9 | No recursion / no infinite loop possible | ✅ single pass over a finite list, by construction (Section 9) |
| 10 | Only BUY_TOGETHER (post-refinement) candidates eligible for selection | ✅ Section 12; `test_t12`, `test_t13` |
| 11 | Mutual exclusivity (Σx_G ≤ 1 per vendor) enforced | ✅ Section 13; every selection test's disjointness assertions |
| 12 | Exact exhaustive search (V1 default), not ILP/greedy | ✅ Section 13 |
| 13 | Savings is the strict primary objective | ✅ Section 14; `test_t9` |
| 14 | Coverage used only as a tie-break, never combined numerically | ✅ Section 14; `test_t10` |
| 15 | Third-level tie-break is neutral/non-mathematical and documented | ✅ Section 15; `test_third_level_neutral_tie_break_on_exact_double_tie` |
| 16 | ABSTAIN never treated as algorithm failure or included in optimization | ✅ `test_t3`, `test_t12` |
| 17 | No fabricated/estimated values anywhere in decision or selection logic | ✅ confirmed by inspection — every field traces to `evaluate_group`'s own computed output |
| 18 | Deterministic behavior (repeated runs identical) | ✅ `test_t14` (both layers) |
| 19 | No I/O inside decision/selection logic | ✅ confirmed — pure functions over in-memory dataclasses only |
| 20 | No ML/clustering/greedy/genetic algorithm introduced | ✅ Section 21 |
| 21 | No API/database/frontend work started | ✅ Section 21 |
| 22 | Closed Potato ML experiment untouched | ✅ Section 21 |
| 23 | No file created that the architecture did not already call for | ✅ every new file maps to an explicit Part 6/12 requirement |
| 24 | Phase 6A tests still pass | ✅ 20/20 |
| 25 | Phase 6B tests still pass | ✅ 21/21 |
| 26 | Phase 6C tests still pass | ✅ 22/22 |
| 27 | No existing test modified to force a pass | ✅ confirmed — only new files were added |
| 28 | Geographic/price-granularity metadata never fabricated or upgraded | ✅ no new geographic status logic exists in Phase 6D at all — it is entirely inherited via the embedded `GroupDecisionResult` |
| 29 | `EvaluatedGroupResult`/`FinalSelectionResult` do not duplicate `GroupDecisionResult`/`CandidateGroup` | ✅ Section 16 |
| 30 | Explanations reflect only actual computed fields | ✅ Section 12; `explain()`'s tests |
| 31 | Full end-to-end pipeline (Phase 6C → 6D) integration-tested | ✅ `test_batch_decision.py` |
| 32 | Report and final response match the required structure | ✅ this document; final response below |

**No inconsistency found.**

---

**Files read for this phase:** `research/phase2b_algorithm_selection.md`, `reports/phase5d_mathematical_decision_model.md`, `reports/phase5e_group_formation_design.md`, `reports/phase5e_phase2b_reconciliation.md`, `reports/phase5f_module_interfaces.md`, `reports/phase6a_core_foundation_report.md`, `reports/phase6c_group_formation_report.md`, and the actual `backend/` source files listed in Section 3.
**Files modified:** none outside the new `backend/`, `tests/` additions, and this report.
