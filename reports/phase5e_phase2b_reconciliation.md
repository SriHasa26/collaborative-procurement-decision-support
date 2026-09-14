# Phase 5E — Phase 2B Reconciliation Audit (Group Formation)

**Date:** 2026-09-14
**Scope:** Inspect Phase 2B (`research/phase2b_algorithm_selection.md`) in full and classify every component of its group-formation design as **preserve unchanged**, **clarify**, **extend**, or **revise only if a real logical conflict exists**, before anything new is proposed. The companion document, `reports/phase5e_group_formation_design.md`, builds strictly on this audit's conclusions.

---

## Summary Verdict

**No component of Phase 2B was found to contain a real logical conflict requiring revision.** Every strong element of Phase 2B's design — the graph-based candidate generation, the exact geographic pruning result, the rejection of clustering/ML, the lexicographic objective, the overlap-resolution rule — is preserved unchanged below. The only gaps found are things Phase 2B never had occasion to address, because Phase 5D's four-state decision model and the ABSTAIN concept did not exist yet when Phase 2B was written. These are genuine **extensions**, not corrections of anything Phase 2B got wrong.

## Extracted Components and Classification

### 1. Input vendor universe
**What Phase 2B specifies:** the full vendor set $V$, narrowed at Step 0 to $V_c = \{i \in V : r_{i,c} > 0\}$ — the commodity-relevant subset for commodity $c$ on date $t$ (Phase 2B, Part 2, Part 6C).
**Classification: A — PRESERVE UNCHANGED.** Nothing in Phases 3–5 changes what a "vendor" or "commodity-relevant" means.

### 2. Existing eligibility rules
**What Phase 2B specifies:** exactly one eligibility rule — commodity relevance ($r_{i,c}>0$). A second, economic pre-filter (excluding vendors whose individual price doesn't beat the effective group price) was proposed in an earlier draft and **explicitly retracted after review** (Part 6C's counterexample: such a vendor's quantity can still be what pushes a group past $MOQ_c$).
**Classification: A — PRESERVE the commodity filter and the retraction unchanged; B — CLARIFY / C — EXTEND for data-completeness eligibility.** Phase 2B never defined a rule for a vendor with *missing* required data (undefined $r_{i,c}$, unusable $L_i$, undefined $H_{i,c}$ with no proxy) — it implicitly assumed every vendor in $V$ already has usable values, because Phase 1C's data collection was that assumption's job, not Phase 2B's. This is a genuine gap to fill (Section 4 of the companion document), not a flaw in what Phase 2B did specify.

### 3. Existing compatibility rules
**What Phase 2B specifies:** geographic compatibility via the exact $2D_{max}$ triangle-inequality threshold (Part 6B) — any two vendors farther apart than $2D_{max}$ can never co-occur in a centroid-feasible group, a *proven*, not assumed, necessary condition. No social, reputation, demographic, or ML-based similarity is used anywhere.
**Classification: A — PRESERVE UNCHANGED.** This is one of Phase 2B's strongest results and nothing in Phases 3–5 touches geography or introduces any social/behavioral data. The companion document reuses this exact rule (Section 5) and does not add social/reputation/demographic/ML compatibility factors, per this phase's explicit instruction not to introduce them without existing justification.

### 4. Existing group-generation method
**What Phase 2B specifies:** graph-based generation — build a compatibility graph over $V_c$ with edges at the $2D_{max}$ threshold, decompose into connected components (independent candidate pools), then enumerate subsets of size $\ge 2$ within each pool (full enumeration by default; clique-restriction documented as a refinement if a pool grows large) (Part 15, Steps 0–3).
**Classification: A — PRESERVE UNCHANGED.** This phase's Step 6 instruction to "evaluate the existing Phase 2B method" and only replace it if genuinely inappropriate finds no such case — Section 6 of the companion document confirms this is still the right choice at prototype scale.

### 5. Existing optimization objective
**What Phase 2B specifies:** a **lexicographic** pair, not a weighted composite — primary: maximize total net savings across selected, mutually disjoint groups; secondary (tie-break only): maximize distinct vendor coverage (Part 11). Explicitly rejected: vendor-count maximization or feasible-group-count maximization as sole objectives (both would favor many marginal groups over fewer strong ones, with no data to justify that trade).
**Classification: A — PRESERVE UNCHANGED.** No demonstrable problem with this objective was found anywhere in Phases 3–5 — the companion document (Section 9) reuses it exactly, per this phase's explicit instruction not to invent a new objective without cause.

### 6. Existing constraints
**What Phase 2B specifies:** it introduces no new constraints of its own — it calls Phase 2A's Stage 2 constraint set (conditional MOQ, geographic, freshness/practical-horizon, economic) unmodified, once per candidate, at Step 4.
**Classification: A — PRESERVE UNCHANGED**, with one carried-forward update already made correctly in Phase 5D: Stage 2's *output* now has four states instead of two (Section 7 below), but the *constraints themselves* are untouched.

### 7. Existing algorithm/search method
**What Phase 2B specifies:** within-pool exhaustive subset enumeration (V1 default) feeding Phase 2A's Stage 2 evaluation, then exact final selection via brute-force enumeration over non-overlapping feasible candidates (small ILP documented as a scale-up fallback, not needed at V1 size) (Part 15, Steps 3, 6; Part 7's comparison table explicitly rejecting greedy heuristics and metaheuristics as unjustified at this scale).
**Classification: A — PRESERVE UNCHANGED.** Section 6/8 of the companion document re-confirms this against current complexity numbers and finds no reason to change it.

### 8. Treatment of overlapping groups
**What Phase 2B specifies:** overlap is expected and harmless during *generation* (proposing both would-be-conflicting candidates costs nothing and avoids foreclosing a better option too early); resolved exactly once, at *final selection*, via exact weighted set packing — no vendor may appear in more than one *selected* group for the same (commodity, date) pair; a vendor *can* appear in separately-selected groups for two *different* commodities on the same day (Part 11, Part 12).
**Classification: A — PRESERVE UNCHANGED.** This is exactly the mechanism Section 10 of the companion document restates formally (as $\sum_{G \ni i} x_G \le 1$) — a direct translation of Part 11's existing rule into the notation this phase's brief requests, not a new rule.

### 9. Computational complexity assumptions
**What Phase 2B specifies:** nominal search space $2^n - n - 1$ (concretely 1,013 at $n=10$; 32,752 at $n=15$; 1,048,555 at $n=20$); the exact geographic pruning result (Part 6B) reduces this to small, independent per-pool subset counts; brute-force enumeration is confirmed computationally *possible but not recommended* at $n\le20$, and an honest scalability ceiling is stated (pools $\gtrsim$25 start to slow; $n\gtrsim50$–100 per pool needs a greedy/ILP fallback within that pool only; $n\gtrsim1000$ needs a different architecture entirely) (Part 5, Part 14).
**Classification: A — PRESERVE UNCHANGED.** Nothing in Phases 3–5 provides new evidence about vendor counts or complexity — Section 14 of the companion document restates these figures, not re-derives new ones.

### 10. Outputs produced
**What Phase 2B specifies:** per selected group, a recommendation ($k^*$, aggregate quantity, per-vendor allocation, net savings, constraint trace); per eligible-but-unselected vendor, a "no recommendation" output with a *specific* reason (already anticipated in Part 15, Step 7: "the specific reason (e.g., no compatible pool, no feasible candidate group, excluded by set-packing conflict resolution)"); per commodity-irrelevant vendor, "no demand for this commodity today."
**Classification: B — CLARIFY / C — EXTEND.** Phase 2B already anticipated that unselected vendors need *differentiated* reasons — it just did not yet have Phase 5D's formal state vocabulary (`WAIT_OR_EXPAND_GROUP`, `DO_NOT_BUY_TOGETHER`, `ABSTAIN`) to slot those reasons into. This is filling in a label set Phase 2B's own design already left room for, not correcting an error.

## D. Components Requiring Revision Due to a Real Logical Conflict

**None found.** This is stated plainly, as the honest result of the audit, not as a foregone conclusion assumed in advance. The one place a superficial mismatch might appear — Phase 2B's Part 15, Step 4 literally says "obtain $y_{g,c,t}$" (a binary variable) — is not a conflict once examined: Phase 2B's own selection logic (Part 11) only ever *needed* to know, for each candidate, "is this feasible with positive net savings, and if so, how much" — exactly what `BUY_TOGETHER` now represents. The three new states are additional information Phase 2B's original binary output simply didn't carry, not a contradiction of anything Phase 2B computed or decided. Section 7 of the companion document confirms this explicitly.

---

**Files read for this audit:** `research/phase2b_algorithm_selection.md` (full, re-inspected in this phase), `research/phase2a_mathematical_model.md`, `reports/phase5d_mathematical_decision_model.md`, `reports/phase5d_phase2_reconciliation.md`.
**Files modified:** none. Phase 2A/2B and Phase 5D are preserved exactly as they stand.
