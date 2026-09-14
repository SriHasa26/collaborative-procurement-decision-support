# Phase 5F — Traceability, Testing, and Implementation Plan

**Date:** 2026-09-14
**Scope:** Companion to `reports/phase5f_system_architecture.md` and `reports/phase5f_module_interfaces.md`. Defines the testing architecture, the requirement-to-test traceability map, the recommended project folder structure's implementation order, and the final consistency audit. No code is written.

---

## 1. Testing Architecture

**Eight categories, per this phase's own list — each grounded in an already-verified source, not a hypothetical.**

| # | Category | What it tests | Deterministic test source |
|---|---|---|---|
| 1 | Mathematical unit tests | $Q_G(k)$, $C^{ind}$, $C^{collab}$, $Savings_G(k)$, per-vendor allocation | Phase 5D §12 (Scenario 1: 5-vendor onion example) and Phase 5E §15 (7-vendor potato example) — both already hand-verified, arithmetic checked line by line |
| 2 | Eligibility tests | Vendor with missing $q_i$/$L_i$/$H_{i,c}$ → `ABSTAIN`; vendor with complete data → proceeds | Phase 5E §15, Vendor V6 (missing location → `ABSTAIN`) |
| 3 | Compatibility tests | $\text{Compatible}(i,j)$ correctly applies the $2D_{max}$ threshold; the chain caveat (connected ≠ jointly feasible) is respected | Phase 2B Part 6B's own worked chain example; Phase 5E §15's 5-vendor pool vs. isolated V5 |
| 4 | Group generation tests | Connected-component decomposition and within-pool subset enumeration produce the expected candidate set | Phase 5E §15: pool = $\{V1,V2,V3,V4,V7\}$, V5 isolated |
| 5 | Overlap-resolution tests | Two overlapping `BUY_TOGETHER`-eligible candidates never both appear in `selected_groups`; the correct one wins by total savings | Phase 5E §15/§10: $G_1$/$G_2$ overlap on V1,V2, both subsumed by $G_{all}$ |
| 6 | Decision-state tests | Each of the four states is produced under its exact triggering condition | Phase 5D §12 (BUY_TOGETHER) + Phase 5E §15 (all four states, in one example: `BUY_TOGETHER` for $G_{all}$, `WAIT_OR_EXPAND_GROUP` for $G_1$/$G_2$/$G_3$, `DO_NOT_BUY_TOGETHER` for $G_4$, `ABSTAIN` for V6) |
| 7 | `ABSTAIN` tests | A missing critical field for one vendor does not affect any other vendor's evaluation | Phase 5E §15: V6's `ABSTAIN` coexists with V1–V5/V7's normal evaluation in the same worked example |
| 8 | End-to-end tests | The full pipeline (Section 4 of the architecture document), run on one complete scenario, reproduces every field of the expected `StructuredResult` | Phase 5E §15's full scenario, used as one complete end-to-end fixture |

**Binding rule, restated because this phase's Step 14 marks it "IMPORTANT": the verified simulated worked examples from Phase 5D and Phase 5E are the future test fixtures, and they must not be altered to make a future implementation's test pass.** If a future implementation's output disagrees with Phase 5D §12 or Phase 5E §15's numbers, the implementation has a bug — the fixture is not adjusted to match the code. Each expected result (e.g., $G_{all}$'s $Savings=₹1{,}840$, individual savings summing to exactly that total) is a target for an eventual independent test assertion, not merely a document to read.

## 2. Traceability Map

| Requirement | Source phase | Module | Input | Output | Test |
|---|---|---|---|---|---|
| Demand estimate hierarchy | Phase 5C §6–7; Phase 5D §3 | Demand Estimation | vendor history, peer records | $q_i$ + provenance | Category 1/2 (no dedicated worked-example number exists yet — flagged in §5 below) |
| Eligibility filter | Phase 5E §4 | Eligibility Module | vendor record | `ELIGIBLE` or `ABSTAIN` | Category 2, 7 |
| Pairwise geographic compatibility | Phase 2B Part 6B; Phase 5E §5 | Group Formation Engine | $L_i, L_j, D_{max}$ | `Compatible(i,j)` boolean | Category 3 |
| Candidate generation | Phase 2B Part 15 Steps 0–3; Phase 5E §6 | Group Formation Engine | $V_c^{elig}$, locations | candidate groups | Category 4 |
| Aggregate demand $Q_G(k)$ | Phase 5D §3 | Procurement Decision Engine | $q_i$, $k$ | $Q_G(k)$ | Category 1 |
| MOQ constraint | Phase 5D §5; Phase 2A Part 18 | Procurement Decision Engine | $Q_G(k)$, $MOQ_c$ | MOQ result (met/not-applicable/not-met) | Category 1, 6 |
| Geographic feasibility | Phase 5D §7; Phase 2A Part 17 | Procurement Decision Engine | $d(G)$, $D_{max}$ | pass/fail | Category 1, 6 |
| Freshness/horizon bound | Phase 5D §6; Phase 2A Part 19 | Procurement Decision Engine | $F_c$, $H_{i,c}$ | feasible $k$ range | Category 1 |
| Cost/savings model | Phase 5D §4 | Procurement Decision Engine | $q_i$, prices, $TC$ | $C^{ind}$, $C^{collab}$, $Savings_G(k)$ | Category 1 |
| Decision-state determination | Phase 5D §9 | Procurement Decision Engine | all of the above | one of 4 states | Category 6 |
| `WAIT_OR_EXPAND_GROUP` resolution | Phase 5E §12 | Decision Engine (sub-routine) | candidate + pool's other evaluated candidates | `WAIT_OR_EXPAND_GROUP` or `DO_NOT_BUY_TOGETHER` | Category 6 |
| Overlap resolution | Phase 2B Parts 11–12; Phase 5E §10–11 | Overlap Resolution / Final Selector | all `BUY_TOGETHER` candidates | selected disjoint groups | Category 5 |
| `ABSTAIN` propagation | Phase 5A; Phase 5E §13 | Eligibility Module, Abstention Handler | missing field | `ABSTAIN` record, no fabricated value | Category 2, 7 |
| Explanation generation | `research/phase3_system_architecture.md` §16; Phase 5D §9 | Explanation Generator | decision state + trace | explanation string | Category 8 |
| Geographic granularity labeling | Phase 5A (Data Granularity Rule); Phase 5D §4a | Input/Data Module, Explanation Generator | price source | `geographic_level` tag on every price figure | Category 8 (no dedicated unit yet — §5 below) |

## 3. Recommended Project Folder Structure

**Reused unchanged from `reports/phase5f_system_architecture.md` §16** — not repeated in full here to avoid two documents defining it differently; see that section for the complete tree. In summary: `data/`, `research/`, `reports/`, `scripts/` are preserved exactly; `app/`, `frontend/`, `tests/`, `docs/` are proposed, not created.

## 4. Exact Implementation Order

**Verified against dependencies, correcting one ordering issue in this phase's own suggested sequence (explained below).**

| Step | Item | Depends on | Why this position |
|---|---|---|---|
| 1 | Data contracts / configuration | — | Nothing else can be typed or validated without the contract existing first (Phase 5F module interfaces §1) |
| 2 | Mathematical calculation functions ($Q_G$, costs, savings, MOQ/freshness/geography checks) | 1 | These are pure functions of already-defined inputs — buildable and testable in complete isolation before any validation or search logic exists, and doing so first lets Category 1 tests (Section 1 above) run immediately |
| 3 | Validation & Eligibility Module | 1 | Needed before real vendor data can safely reach Step 2's functions in a full pipeline, but the functions themselves (Step 2) don't need Step 3 to exist to be unit-tested in isolation — hence Step 2 before Step 3, not after |
| 4 | Compatibility graph (pairwise rule + graph construction) | 1, 3 | Needs eligible vendors (Step 3) as its input population |
| 5 | Candidate generation (connected components → within-pool enumeration) | 4 | Needs the graph (Step 4) |
| 6 | Procurement Decision Engine (wires Step 2's functions into the full per-candidate evaluation + four-state routing) | 2, 5 | Needs both the math (Step 2) and something to evaluate (Step 5) |
| 7 | `WAIT_OR_EXPAND_GROUP` resolver | 6 | Needs a full pool of already-evaluated candidates (Step 6's output) to search over |
| 8 | Overlap resolution / final selection | 6, 7 | Needs finished per-candidate decision states |
| 9 | Explanation generation | 6, 7, 8 | Needs a final decision state and full trace to template against |
| 10 | Structured output assembly | 9 | Needs the explanation and every upstream field |
| 11 | Unit tests (Categories 1–7, Section 1) | 2–9 (written alongside, not strictly after — see note) | — |
| 12 | End-to-end tests (Category 8) | 10, 11 | Needs the full pipeline assembled |
| 13 | API layer | 6–10 (a working core pipeline) | Orchestrates already-correct logic; building it first would have nothing correct to orchestrate |
| 14 | Frontend | 13 | Needs a working API to call |
| 15 | Integration testing | 13, 14 | Needs both ends of the system built |

**Correction to this phase's own suggested order:** the brief lists "Validation" (its item 3) *before* "Mathematical calculation functions" (its item 2) is actually listed *after* in its sketch ("2. Mathematical calculation functions... 3. Validation..." — already in this order in the brief, so no correction needed there). The one place a genuine reordering is warranted relative to a naive reading is unit tests (brief's item 10): **unit tests for Steps 2–9 should be written incrementally alongside each step, not deferred as one block after Step 9**, since Category 1 (mathematical) tests in particular have zero dependency on anything past Step 2 and can catch an arithmetic error immediately rather than after the whole pipeline exists. This is noted as a practice recommendation, not a hard reordering of the dependency chain itself.

## 5. Final Architecture Audit

| # | Check | Result |
|---|---|---|
| 1 | No contradiction with Phase 5D | ✅ Every formula/constraint referenced by name and section, never redefined (architecture doc §2, module interfaces §3) |
| 2 | No contradiction with Phase 5E | ✅ Eligibility, compatibility, generation, WAIT/EXPAND, ABSTAIN all traced to their exact Phase 5E section |
| 3 | No dependency on unavailable ML | ✅ Demand Estimation Module's `PREDICTION — ML` provenance tag is defined but unused (module interfaces §3); no module requires it to function |
| 4 | No fake data treated as real | ✅ Every field in the input contract (module interfaces §1) carries an explicit Real/User-provided/Estimated/Configurable/Simulated label; simulated data appears only in the cited worked examples, always labeled |
| 5 | Every major rule has one authoritative owner | ✅ Architecture doc §2's dependency map and module interfaces §5's routing table both enforce this explicitly |
| 6 | No duplicated mathematical logic | ✅ The Procurement Decision Engine is the sole caller of every Phase 5D formula; no other module recomputes cost, savings, or feasibility |
| 7 | Decision states consistently routed | ✅ Module interfaces §5 — fixed evaluation order, one originating module per state |
| 8 | Missing critical data cannot silently pass | ✅ Module interfaces §4's four-category validation table — every "missing critical" path terminates in an explicit `ABSTAIN`, never a default |
| 9 | Unrelated vendors can still be processed | ✅ Module interfaces §4's binding rule, demonstrated concretely in the Phase 5E §15 fixture (V6 abstains, V1–V5/V7 unaffected) |
| 10 | Core logic independent of frontend | ✅ Architecture doc §12 — no authoritative decision is made in the frontend; it only renders an already-computed `StructuredResult` |
| 11 | System is testable | ✅ Section 1 above — every category has a concrete, already-verified fixture to test against, not a hypothetical one |
| 12 | System is reproducible | ✅ SQLite + Run Logging Module (architecture doc §3/§13); deterministic algorithms throughout (no ML, no randomness) |
| 13 | Folder architecture preserves previous work | ✅ Architecture doc §16 — `data/`, `research/`, `reports/`, `scripts/` untouched; new folders proposed only, not created |
| 14 | Implementation order dependency-safe | ✅ Section 4 above, with dependencies stated explicitly for every step |

**No inconsistency was found requiring a structural change to the architecture.**

## 6. Two Honest Gaps, Named Rather Than Hidden

Per this phase's own standing discipline, two items in the traceability map (Section 2) currently have **no dedicated deterministic worked-example test** and should not be presented as already covered:

1. **Demand Estimation Module's cold-start/baseline hierarchy** — Phase 5C defined the *method* (peer-category average, last-observed-value, moving average) but no worked numeric example was produced for it specifically (Phase 5D/5E's worked examples treat $q_i$ as already-given input, not as something the Demand Estimation Module itself computed from raw history). A future phase should produce one small, explicitly-labeled worked example of the estimation hierarchy itself, the same way Phase 5D/5E did for the decision and grouping math.
2. **Geographic-granularity tagging** — Phase 5D §4a's requirement that every price figure carry a `geographic_level` tag is a structural rule, not yet exercised in any worked example (both Phase 5D §12 and Phase 5E §15 use illustrative prices without explicitly attaching this tag in the worked arithmetic). A future implementation's test suite should include at least one case exercising this tag explicitly, not just the underlying price math.

## 7. Recommendation for Phase 6

**Phase 6 should begin implementation, in the exact order of Section 4 above, starting with data contracts and the mathematical calculation functions (Steps 1–2) — since these are the most already-verified, lowest-risk components (Phase 5D/5E's worked examples are ready-made regression tests for them).** Before writing any frontend or API code, Phase 6 should close this phase's two named gaps (Section 6) with small, explicitly-labeled worked examples, so the full traceability map has no unverified row before implementation begins. The Potato forecasting experiment remains closed and untouched; no ML training occurs in Phase 6.

---

**Files read for this phase:** `reports/phase5f_system_architecture.md`, `reports/phase5f_module_interfaces.md`, `reports/phase5d_mathematical_decision_model.md`, `reports/phase5e_group_formation_design.md`.
**Files modified:** none.
