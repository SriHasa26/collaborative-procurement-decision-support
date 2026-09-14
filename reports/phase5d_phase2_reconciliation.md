# Phase 5D — Phase 2A/2B Reconciliation Audit

**Date:** 2026-09-14
**Scope:** Inspect Phase 2A (`research/phase2a_mathematical_model.md`) and Phase 2B (`research/phase2b_algorithm_selection.md`) in full, and reconcile that existing mathematical work against everything learned in Phases 3–5 (real price-data acquisition, the closed Potato ML experiment, the demand-data feasibility audit, and the Phase 5A system policy). Nothing in Phase 2A/2B is rewritten here — this document only classifies each part of it as **valid**, **needing clarification**, **in tension with a later finding**, or **requiring revision**, per this phase's Step 1 instruction. The companion document, `reports/phase5d_mathematical_decision_model.md`, is where any actual consolidation/extension happens, built on top of this audit's conclusions.

---

## Summary Verdict

**The overwhelming majority of Phase 2A/2B's mathematical model remains valid, unmodified, and does not conflict with anything found in Phases 3–5.** This is not a surprising coincidence — Phase 2A explicitly built its demand and price inputs to come from primary data collection and Layer-1 estimation, never from a trained ML model (Layer 2 was explicitly deferred in Phase 2A/2B itself, before Phases 3A.1–5C ever examined the question). The two genuinely new things Phases 3–5 add are (1) a real, tested example of a project-internal ML experiment failing to generalize, which **reinforces** rather than contradicts Phase 2A/2B's original caution about not forcing ML in, and (2) a sharper, evidence-based vocabulary (geographic-granularity labeling, the four-tier decision-state distinction, the ESTIMATE-vs-PREDICTION distinction) that this document uses to **extend**, not overwrite, the existing model.

## A. What Remains Valid (No Change Needed)

| Phase 2A/2B element | Why it remains valid |
|---|---|
| Two-stage separation: Stage 1 (group formation, Phase 2B) feeds Stage 2 (group evaluation, Phase 2A) | Nothing in Phases 3–5 touches group formation or evaluation logic at all — this structural decision is untouched |
| $y_{g,c,t}$ (go/no-go) and $k_{g,c,t}$ (order horizon) as the only two real decision variables | Still the correct minimal decision set; Phase 5D's Step 9 extension (Section D below) refines $y$'s possible *output states*, it does not add a new decision variable |
| Demand aggregation $Q_{g,c}(k) = k\sum_{i\in g} r_{i,c}$ | Structurally unaffected — only the *provenance* of $r_{i,c}$ is clarified (Section B) |
| Individual cost $C^{ind}_{i,c}(k) = k\, r_{i,c}\, p^{ind}_{i,c}$, collaborative cost $C^{collab}_{g,c}(k) = Q_{g,c}(k)\,p^{eff}_{c,t} + TC_g(k)$, and $NetSavings_{g,c}(k)$ | Unaffected by any later phase — none of Phases 3–5 touched cost or transport modeling |
| Quantity-proportional cost allocation (Phase 2A, Part 14) | Unaffected; still the correct, data-minimal fairness rule |
| MOQ as a *conditional* hard constraint, never substituted with a proxy when unknown (Phase 2A, Part 18) | Unaffected, and this document's Step 5 extension (Section D) builds directly on this exact rule rather than changing it |
| Freshness/practical-horizon bound $k \le \min(F_c, \min_{i\in g} H_{i,c})$ (Phase 2A, Part 19) | Unaffected — still the correct dual-ceiling formulation; Section E below adds one derived consistency fact, not a change |
| Geographic feasibility via centroid distance, not pairwise distance (Phase 2A, Part 17); the $2D_{max}$ triangle-inequality pruning result (Phase 2B, Part 6B) | Unaffected — no later phase touched logistics or geography |
| Rejection of ML/clustering/metaheuristics for group formation (Phase 2B, Parts 8–9) | **Reinforced, not merely unaffected** — Phase 4C's Potato result is a concrete demonstration of exactly the generalization risk Phase 2B already reasoned about abstractly when rejecting ML for this step |
| Layer 1 (similarity/case-based cold-start estimation) as the source of $r_{i,c}$ for new vendors; Layer 2 (trained ML) explicitly deferred (Phase 2A, Part 7; Phase 1C's three-layer architecture) | **Directly confirmed by Phase 5C**, which independently re-derived the same conclusion (demand ML not justified at this data scale) four phases later. This is agreement across independent audits, not new information changing an old answer |
| The "decision support, never autonomous procurement" system role (Phase 2A, Part 4) | Unaffected, and consistent with Phase 5A's abstention/explanation policy, which extends the same non-autonomous posture to the price/forecasting side of the system |
| Rejection of a fitted probabilistic demand distribution in favor of low/base/high scenario ranges (Phase 2A, Part 25) | Unaffected, and consistent in spirit with Phase 3A.7–4C's own insistence on not overstating what a small dataset can support |

## B. What Needs Clarification (Not a Conflict — a Precision Gap Later Phases Now Let Us Close)

**B1. What, exactly, does $p^{wh}_{c,t}$ need — a price *time series*, or a single *current* value?**

Re-reading Phase 2A closely: $p^{wh}_{c,t}$ is defined as "wholesale/mandi modal price for $c$ **on date $t$**" (Part 7), consumed once per day in a "once-per-day batch computation" (Part 28), with no historical window anywhere in Stage 2's formulas. **Phase 2A never needed a price time series for its core decision function — only one fresh value per commodity per day.** This was true before Phases 3A.1–4C existed; it simply was never stated as explicitly as it can be now, because no prior phase had yet gone looking for a historical price dataset and found the acquisition process this complicated.

**This matters because it resolves what could otherwise look like a serious problem.** Phase 3A.2 found that data.gov.in's "Current Daily Price" dataset is a same-day snapshot, unusable for time-series ML — and flagged this as a limitation for the (separate, optional) ML trend-signal work in Phase 3A.1. **That same "limitation" is not a limitation for Phase 2A's core model at all — a same-day snapshot is precisely, exactly what $p^{wh}_{c,t}$ requires.** Phase 2A's price input and Phase 3A.1's ML-forecasting price input are two different consumers of Agmarknet-family data with two different, non-overlapping requirements, and this document is the first to state that distinction explicitly.

**Clarification, not a revision:** $p^{wh}_{c,t}$'s data source is confirmed still viable — the data.gov.in current-daily-price snapshot resource (Phase 3A.2) — with one honest caveat carried forward: this project has so far only **manually downloaded** that snapshot once (Phase 3A.2); it has not verified an automated, registered-API-key pull of a fresh snapshot on demand. That automation step is unverified, not proven broken — a distinction Section 5 of this document's companion report treats as an open item for Phase 5E, not as a resolved capability.

**B2. Does the CAPTCHA finding (Phase 3A.3) affect $p^{wh}_{c,t}$ at all?**

No, and this is worth stating precisely so it is not misread as a bigger problem than it is. The CAPTCHA gate applies specifically to `api.agmarknet.gov.in`'s own **report-generation** endpoints (the official Agmarknet 2.0 web portal's live system) — a different system from data.gov.in's Open Government Data API, which is what Phase 3A.2 actually used for the snapshot. **Phase 2A's daily price need was never routed through the CAPTCHA-gated system**, and nothing here requires it to be.

**B3. Geographic-granularity labeling was never explicit in Phase 2A/2B — it now must be.**

Phase 2A's worked example and Part 7 table both discuss $p^{wh}_{c,t}$ and market access generically ("the mandi," "a single effective price per commodity per date") without a formal tag distinguishing a specific-mandi figure from a district-aggregate figure. Phase 5A's Data Granularity Rule (`MANDI_LEVEL` / `DISTRICT_LEVEL_PROXY` / `UNKNOWN_GRANULARITY`) did not exist when Phase 2A was written. **This is a clarification Phase 2A implicitly needed all along** (Phase 1B already worried about price-source reliability, Section 10) and Phase 5A now supplies the missing vocabulary for. See Section C2 below for why this is flagged as needing a labeling requirement, not a structural change.

## C. What Is In Tension With a Later Finding (Examined Carefully — Mostly Resolves to "No Real Conflict")

**C1. Does the Potato ML experiment's negative result conflict with anything in Phase 2A/2B?**

**No.** Phase 2A/2B never proposed using a trained price-forecasting model anywhere inside the core cost/decision model — $p^{wh}_{c,t}$ was always meant to be a **realized, observed** price, not a predicted one (Phase 2A, Part 3: "whether the procurement is economically beneficial" is evaluated from the *current* realized price, explicitly not a future one — the same reasoning Phase 3A.1 later used to reject "predictive input" as ML's role, Section 3 there). The Potato experiment lived entirely in Phase 3A.1's optional, display-layer "decision insight" concept — a component Phase 2A/2B's core model never depended on. Its failure is a finding about that optional layer, not about anything in the core model this reconciliation is auditing.

**C2. Does Potato's `DISTRICT_LEVEL_PROXY` status conflict with Phase 2A's price/market assumptions?**

**Only if a future implementation carelessly reused CEDA's district-level Potato series as if it were Bowenpally's own mandi price — which nothing in Phase 2A/2B ever actually did, since Phase 2A's real price source has always been Agmarknet (via data.gov.in), not CEDA.** CEDA was investigated in Phases 3A.2–3A.4 specifically as a candidate for the *separate* ML-forecasting experiment, never adopted as Phase 2A's own price feed. **There is no existing conflict — only a future risk to guard against explicitly**, which is why Section D's model consolidation adds a binding rule: any price or demand-comparator figure Phase 2A's model consumes must carry a geographic-granularity tag, and a `DISTRICT_LEVEL_PROXY` figure must never silently stand in for a specific mandi's price in a vendor-facing recommendation.

**C3. Does "demand ML is not justified" (Phase 5C) conflict with Phase 2A's $r_{i,c}$ parameter?**

**No — it is the same conclusion Phase 2A already reached (Part 7's Layer-1/Layer-2 split), reached independently.** If anything, Phase 5C's more careful audit (explicit scenario table, explicit ESTIMATE-vs-PREDICTION labeling requirement) **strengthens** Phase 2A's original, lighter-touch treatment of the same issue. Section D adopts Phase 5C's sharper vocabulary for describing $r_{i,c}$'s provenance without changing what $r_{i,c}$ *is* or how it is *used*.

## D. What Must Be Revised (Genuine Extensions — Specified in the Companion Document)

Only two things in this audit actually require adding something new to the model, as opposed to clarifying or reaffirming it — both are extensions, not corrections of an error:

**D1. The binary decision output $y_{g,c,t} \in \{0,1\}$ must be extended to a four-state decision (`BUY_TOGETHER`, `WAIT_OR_EXPAND_GROUP`, `DO_NOT_BUY_TOGETHER`, `ABSTAIN`), per this phase's explicit Step 9 instruction.** Phase 2A's original binary framing conflated two different kinds of "no": a group that fails now but could plausibly succeed if joined by more compatible vendors (e.g., an MOQ shortfall), versus a group that fails for a reason more vendors joining *that same candidate* would not fix (e.g., a geographic infeasibility specific to that candidate's own membership), versus a case where the model simply cannot run at all because a required input is missing. Phase 2A's own Part 23, Step 8 already *computed* enough information to distinguish these ("record which constraint(s) failed... so the vendor-facing output can explain why") — it just never split that trace into distinct named output states. This is a genuine, non-trivial addition, fully specified in the companion document's Step 9.

**D2. The consumption-time / freshness check, as posed by this phase's Step 6, should be stated per-vendor as well as per-group, even though Phase 2A's group-level bound already implies it exactly.** This is not a correction — Phase 2A's Part 19 derivation ("ConsumptionDays $= Q_{g,c}(k)/\sum r_{i,c} = k$ exactly") already proves the per-vendor consumption time under quantity-proportional allocation equals $k$ for every vendor, identically. The companion document states this per-vendor formula explicitly (as this phase's Step 6 requires), and shows it is a direct, already-implied consequence of Phase 2A's own math — not a new constraint being bolted on.

## What This Audit Did Not Find

- No unsupported constant was discovered hiding in Phase 2A/2B that Phases 3–5 now contradict.
- No parameter in Phase 2A/2B was found to depend on data this project's later phases showed to be unavailable — every 🔵/🔴-flagged gap in Phase 2A (exact $D_{max}$, margin $m$, tomato's ambient $F_c$, vehicle-tier cutoffs, per-vendor $H_{i,c}$, $MOQ_c$) was already honestly marked as pending primary data collection in Phase 2A itself (its Part 33), and remains exactly that — pending, not contradicted.
- No double-counting, unit inconsistency, or circular logic was found in the cost/savings/allocation chain (Parts 10–15 of Phase 2A) — this is re-verified directly in the companion document's Step 13 final audit, not merely asserted here.

---

**Files read for this audit:** `research/phase2a_mathematical_model.md` (full), `research/phase2b_algorithm_selection.md` (full), `reports/phase5a_research_findings_and_system_policy.md`, `reports/phase5c_demand_data_and_ml_feasibility.md`, `reports/phase4c_final_test_results.md`.
**Files modified:** none. Phase 2A/2B are preserved unchanged, as required.
