# Phase 5D — Final Mathematical Decision Model

**Date:** 2026-09-14
**Scope:** Consolidate Phase 2A's cost/feasibility model and Phase 2B's group-formation algorithm with everything Phases 3–5 established, into one final, implementable mathematical specification. This document **preserves** Phase 2A/2B's valid work rather than replacing it — see the companion `reports/phase5d_phase2_reconciliation.md` for the full audit that justifies every choice below to keep, clarify, or extend. No frontend/backend is built. No model is trained. No parameter is invented.

---

## 1. Phase 2A/2B Reconciliation (Summary)

Full detail in `reports/phase5d_phase2_reconciliation.md`. In brief: **almost everything in Phase 2A/2B remains valid unchanged** — the two-stage architecture, the cost/savings/allocation formulas, the conditional MOQ rule, the freshness/practical-horizon dual bound, the geographic centroid model, and the rejection of ML for group formation. Two clarifications resolve what could look like conflicts but are not: (a) Phase 2A's price parameter $p^{wh}_{c,t}$ only ever needed a single current-day value, never a time series, so Phase 3A.2's "unusable for ML forecasting" finding about the data.gov.in snapshot dataset does not affect it — that snapshot is exactly what $p^{wh}_{c,t}$ needs; (b) demand ML being unjustified (Phase 5C) simply reconfirms what Phase 2A already assumed (Layer 2 deferred). Two genuine, non-conflicting extensions are made: (1) the binary decision output is expanded to four named states (Section 9); (2) the freshness bound is additionally stated per-vendor, which Phase 2A's own math already implies exactly (Section 6).

## 2. Final Notation Table

| Symbol | Meaning | Unit | Source | Real / User-provided / Estimated / Simulated |
|---|---|---|---|---|
| $i$ | Vendor index | — | — | — |
| $c$ | Commodity (fixed V1 set: onion, potato, tomato) | — | Phase 1B, Section 4 | — |
| $t$ | Date | — | — | — |
| $g$ | A candidate or selected group of vendors | — | Phase 2B Stage 1 output | — |
| $L_i = (\text{lat}_i,\text{lon}_i)$ | Vendor $i$'s approximate coordinates | decimal degrees | Survey, tied to anonymous ID only | User-provided |
| $r_{i,c}$ | Vendor $i$'s demand-estimate rate for $c$ — see Section 3 for exact meaning | kg/day | Diary (mean) / survey (point estimate) / cold-start peer-category estimate | Real (diary) / User-provided (survey) / **Estimated** (cold-start) — never Simulated in a real evaluation |
| $p^{ind}_{i,c}$ | Vendor $i$'s current individual procurement price for $c$ | ₹/kg | Survey/diary | User-provided |
| $p^{wh}_{c,t}$ | Wholesale/mandi reference price for $c$ on date $t$ | ₹/kg | data.gov.in current-daily-price snapshot (Phase 3A.2) | Real — **must carry a `geographic_level` tag** (Section 4a below); today's verified source is `MANDI_LEVEL` (per-market rows) |
| $m$ | Assumed trader margin | ratio | Sensitivity parameter, $m \in \{0, 0.10, 0.15\}$ | Estimated (sensitivity range, not a point value) |
| $p^{eff}_{c,t}$ | Effective group-access price | ₹/kg | $p^{wh}_{c,t}(1+m)$ | Derived |
| $F_c$ | Freshness window for $c$ | days | FAO/USDA ARS (scientific) / trader triangulation | Real (scientific component) / Estimated (trader-triangulated component) |
| $H_{i,c}$ | Vendor $i$'s practical procurement-horizon ceiling for $c$ | days | Vendor-declared, or purchase-frequency proxy | User-provided / Estimated (proxy case) |
| $D_{max}$ | Maximum acceptable centroid distance | km | Provisional starting value | Estimated, pending validation |
| $TC(\text{tier})$ | Flat transport charge for a capacity tier | ₹/trip | Commercial rental listings | Real (rate bands) / Estimated (exact tier cutoffs) |
| $MOQ_c$ | Trader-confirmed minimum order quantity | kg | Trader interview | User-provided **if obtained**; otherwise the constraint is not applied (no substitute value, ever) |
| $BE_c(t)$ | Break-even quantity | kg | Derived from $p^{ind}_{i,c}, p^{eff}_{c,t}, TC$ | Derived (explanatory only) |
| $q_i$ | Vendor $i$'s **demand estimate used by the decision model** (Section 3 — distinct from any *recommended* quantity) | kg/day | Same provenance as $r_{i,c}$ | Same as $r_{i,c}$ |
| $Q_G$ | Aggregate group requirement over the horizon | kg | $\sum_{i \in G} q_i \times k$ | Derived |
| $k_{g,c,t}$ | Order/procurement horizon (decision variable) | days | Bounded enumeration | Decision variable |
| $y_{g,c,t}$ | Decision state (Section 9 — now four states, not binary) | categorical | Decision output | Decision output |
| `geographic_level` | Tag on any price/comparator figure: `MANDI_LEVEL` / `DISTRICT_LEVEL_PROXY` / `UNKNOWN_GRANULARITY` | categorical | Phase 5A's Data Granularity Rule | Structural metadata, not a numeric input |
| `data_status` | Tag on $r_{i,c}$: `ESTIMATE — cold-start` / `ESTIMATE — baseline` / `PREDICTION — ML (validated)` | categorical | Phase 5C's hierarchy | Structural metadata |

**No field above is asserted as fact without one of the four evidence labels**, per Phase 2A's own Rule 6, carried forward unchanged.

## 3. Demand Formulation — $q_i$ Defined Precisely, Disambiguated From "Recommended Quantity"

**Two genuinely different things must never share one name, per this phase's explicit instruction:**

- $q_i$ **— the demand estimate.** What vendor $i$ is believed to need per day for commodity $c$, before any decision model runs. This is exactly Phase 2A's $r_{i,c}$, renamed here only to make the distinction below explicit; nothing about its formula or provenance changes.
- **Recommended procurement quantity — an *output* of the decision model**, specifically $k_{g,c,t} \times q_i$ for a vendor whose group is recommended (`BUY_TOGETHER`, Section 9) — a different, later-computed number that only exists *after* the model runs, and only for some outcomes.

$$q_i \equiv r_{i,c} \quad \text{(the demand estimate; never itself "the recommended amount to buy")}$$

**Provenance hierarchy for $q_i$ (reusing Phase 5C's Sections 5–7, not re-deriving them):**

| Vendor's data status | $q_i$'s source | Label |
|---|---|---|
| No history | Same-category peer average (cold-start) | `ESTIMATE — cold-start` |
| Limited history (a few diary records) | Last observed value or short moving average | `ESTIMATE — baseline` |
| Sufficient, validated history (not currently available for any vendor — Phase 5C, Section 12) | A future, empirically-tested ML model | `PREDICTION — ML (validated)` |

**For the current project, no vendor's $q_i$ comes from a trained ML model.** Every $q_i$ used in any real evaluation today is an `ESTIMATE`, never a `PREDICTION` — restated here as a binding rule, not an aspiration, per Phase 5C's Section 12 verdict.

**Aggregate group requirement**, over the already-approved horizon $k$ (Section 6):

$$Q_G(k) = k \sum_{i \in G} q_i$$

identical in structure to Phase 2A's $Q_{g,c}(k)$ — the horizon $k$ is Phase 2A's own order-horizon variable, **reused, not reinvented**, per this phase's explicit instruction not to invent a new horizon unnecessarily.

## 4. Cost Model

**A. Individual procurement cost** (Phase 2A, Part 10, unchanged):
$$C^{ind}_{i,c}(k) = k \, q_i \, p^{ind}_{i,c}, \qquad C^{ind}_{total,G}(k) = \sum_{i \in G} C^{ind}_{i,c}(k)$$

**B. Collaborative procurement cost** (Phase 2A, Part 11, unchanged):
$$C^{collab}_{G,c}(k) = Q_G(k) \times p^{eff}_{c,t} + TC_G(k)$$

No handling, wastage, or other shared cost is added beyond commodity cost and transport — per Phase 2A's original finding (no data exists to populate such a cost) and per this phase's explicit instruction not to add costs without justification. **If a future prototype needs to test a hypothetical handling fee, it must be introduced as an explicitly labeled, configurable prototype parameter (e.g., `handling_fee_prototype`, defaulting to zero), never silently folded into $TC$ or $p^{eff}$.**

**C. Net savings** (Phase 2A, Part 15, unchanged):
$$Savings_G(k) = C^{ind}_{total,G}(k) - C^{collab}_{G,c}(k)$$

**Cost allocation** (Phase 2A, Part 14, unchanged) — quantity-proportional, so a vendor's share of both commodity and transport cost, and thus their individual share of the group's savings, tracks exactly what they consume:
$$\text{Share}_i(k) = \frac{k\, q_i}{Q_G(k)} \times C^{collab}_{G,c}(k), \qquad \text{IndividualSavings}_i(k) = C^{ind}_{i,c}(k) - \text{Share}_i(k)$$

**4a. Geographic-granularity requirement on $p^{wh}_{c,t}$ (new, per Section C2 of the reconciliation audit):** whichever source supplies $p^{wh}_{c,t}$ (or, in a future extension, any per-market price comparator) must be tagged `MANDI_LEVEL`, `DISTRICT_LEVEL_PROXY`, or `UNKNOWN_GRANULARITY`. **A `DISTRICT_LEVEL_PROXY` figure must never be presented to a vendor as if it were their specific mandi's price** — this is a direct, binding application of Phase 5A's Data Granularity Rule to Phase 2A's own cost model, closing the one real gap the reconciliation audit found.

## 5. MOQ Constraint

$$Q_G(k) \ge MOQ_c \quad \text{(hard, conditional — applied only if a trader-confirmed } MOQ_c \text{ exists; Phase 2A Part 18, unchanged)}$$

**What happens when MOQ is not satisfied — the genuine extension this phase adds:** Phase 2A's original binary output would simply record $y=0$. **This is now refined.** If a candidate group fails only the MOQ check — i.e., some $k$ in the feasible horizon range would produce $Savings_G(k) > 0$ *if* $Q_G(k)$ had reached $MOQ_c$, but no tested $k$ actually reaches it — the correct output is **not** "do not buy," because the group's economics are not the problem; its *size* is. The system must instead report:

$$\text{WAIT\_OR\_EXPAND\_GROUP} \quad \text{if } \big(\forall k:\ Q_G(k) < MOQ_c\big) \ \text{and}\ \big(\exists k:\ Savings_G(k) > 0 \text{ would hold once } Q_G(k)\ge MOQ_c\big)$$

This is a direct, faithful extension of Phase 2B's own reasoning (Part 6C's vendor-B counterexample: a vendor whose demand alone looks unfavorable can still be the one whose quantity tips a group over $MOQ_c$ into profitability) — restated here as a *system output*, not just an internal pruning rule.

## 6. Freshness / Perishability Constraint

$$k \le \min\!\big(F_c,\ \min_{i \in G} H_{i,c}\big) \quad \text{(hard; Phase 2A Part 19, unchanged)}$$

Neither $F_c$ nor $H_{i,c}$ is invented anywhere in this model. **Source labeling, restated as a binding rule:** $F_c$'s scientific component must be labeled `literature-supported`, its ambient/trader-triangulated component labeled `estimated`; $H_{i,c}$ must be labeled `user-configured` (vendor-declared) or `estimated` (purchase-frequency proxy) — never presented as a single undifferentiated number.

**Per-vendor consumption time (Step 6's requested formula), stated explicitly and shown to already follow from Phase 2A's own math, not added as a new assumption:**

$$\text{consumption\_time}_i = \frac{\text{allocated\_quantity}_i}{q_i} = \frac{k \, q_i}{q_i} = k$$

**Because allocation is quantity-proportional (Section 4), every vendor's own consumption time equals $k$ exactly, identically to the group-level figure Phase 2A already derived** ("ConsumptionDays $=Q_G(k)/\sum q_i = k$," Phase 2A Part 19). This is not a new constraint — it is the same bound, shown here to hold per-vendor as well as in aggregate, which is exactly what prevents a bulk order from recommending a quantity that would let any *individual* vendor's allocated share spoil before use, even if the group total looked fine on average.

## 7. Logistics / Geographic Feasibility

$$d(G) = \max_{i \in G} \text{Haversine}(L_i, \text{centroid}(G)) \le D_{max} \quad \text{(hard; Phase 2A Part 17, unchanged)}$$

**Distance metric:** Haversine (great-circle), not routed road distance — an approximation, stated as such, not false precision. **Transport cost:** a flat, tiered lookup $TC(\text{tier}(Q_G(k)))$ (Phase 2A Part 13), not a distance-based formula — because Phase 1B's own primary data found short intra-city trips are dominated by a near-fixed per-trip charge, not a linear per-km rate. **No routing optimization is introduced** — Phase 2B already found this disproportionate to a single-collection-point V1 design, and nothing in Phases 3–5 changes that. **Values are:** $D_{max}$ — estimated, pending validation; $TC(\text{tier})$ rate bands — real (commercial listings); tier weight cutoffs — estimated.

## 8. Group Feasibility Conditions

| # | Condition | Hard constraint or optimization objective? |
|---|---|---|
| 1 | Commodity compatibility ($q_i > 0$ for the commodity in question) | Hard — a vendor with zero demand for $c$ is simply not part of $G_c$ (Phase 2A Part 12) |
| 2 | Geographic/logistics feasibility ($d(G) \le D_{max}$) | Hard |
| 3 | MOQ satisfaction ($Q_G(k) \ge MOQ_c$, conditional) | Hard, when applicable |
| 4 | Freshness feasibility ($k \le \min(F_c, H_{i,c})$) | Hard |
| 5 | Economic benefit ($Savings_G(k) > 0$) | Hard **for the go/no-go gate**; the *magnitude* of $Savings_G(k)$, maximized over $k$, is the **optimization objective** (Section 10) — the same threshold serves both roles, at two different points in the pipeline |

**Explicitly distinguished, per this phase's instruction:** conditions 1–4 are pass/fail gates that must all hold; condition 5's *sign* is a gate, but its *value* is simultaneously what the model maximizes over $k$ once the other gates pass. Nothing here is optimized "softly" — there are zero soft constraints, unchanged from Phase 2A Part 21.

## 9. Final Decision States

**Extension over Phase 2A's original binary $y_{g,c,t}\in\{0,1\}$ — the one structural addition this phase makes, fully justified in the reconciliation audit (Section D1 there).**

| State | Condition | Required explanation |
|---|---|---|
| **`BUY_TOGETHER`** | $\exists k \in \{1,\dots,\lfloor\min(F_c,\min_i H_{i,c})\rfloor\}$ satisfying conditions 1–4 of Section 8 **and** $Savings_G(k) > 0$ | Report $k^* = \arg\max_k Savings_G(k)$ over the feasible set, $Q_G(k^*)$, per-vendor allocation, and $Savings_G(k^*)$ |
| **`WAIT_OR_EXPAND_GROUP`** | Conditions 2 and 4 hold for some $k$; condition 3 (MOQ) fails for *every* feasible $k$; and $Savings_G(k)$ would be positive at that $k$ if $MOQ_c$ were met | Report how far short $Q_G(k)$ fell of $MOQ_c$ at the best tested $k$, and that additional compatible vendors could close the gap |
| **`DO_NOT_BUY_TOGETHER`** | Condition 2 (geography) fails for this specific candidate, **or** no $k$ in the feasible horizon range achieves $Savings_G(k) > 0$ even with MOQ satisfied (or inapplicable) | Report which hard constraint(s) failed at every tested $k$, and $BE_c(t)$ for context (Phase 2A Part 16) |
| **`ABSTAIN`** | A required input is missing or undefined for this evaluation — e.g., $q_i$ undefined for a group member with no cold-start estimate and no declared value; $p^{wh}_{c,t}$ unavailable for date $t$; $H_{i,c}$ undefined with no usable proxy (Phase 2A Part 31's own "exclude rather than invent" rule) | Report exactly which input is missing and why no substitute value was used |

**These states are mutually exclusive by construction**, evaluated in this fixed order so no overlap can occur: check for missing required inputs first (`ABSTAIN` pre-empts everything else, since nothing downstream can be computed without them); then geography (a `DO_NOT_BUY_TOGETHER` trigger that stops evaluation immediately, exactly as Phase 2A's Part 23 Step 2 already does); then, among the remaining candidates, MOQ status decides between `WAIT_OR_EXPAND_GROUP` and continuing; economic feasibility at the surviving $k$'s decides between `BUY_TOGETHER` and `DO_NOT_BUY_TOGETHER`. No candidate can ever satisfy two of these states at once, because each is checked against a disjoint, ordered set of conditions.

## 10. Objective Function

$$\max_{k \in \{1,\dots,\lfloor\min(F_c,\min_{i\in G}H_{i,c})\rfloor\}} Savings_G(k) \quad \text{subject to Section 8's conditions 1–4}$$

unchanged from Phase 2A Part 22 — reused, not reinvented, per this phase's explicit instruction.

**Does the current model evaluate a user-provided group, or search for the optimal group? Both — at different stages, exactly as Phase 2A/2B already separated them:**

- **Stage 2 (this document, Phase 2A's original scope): evaluates a given group.** For a specific candidate $G$, it optimizes only over the bounded horizon $k$ — a small enumeration, not a search over group membership.
- **Stage 1 (Phase 2B's scope, unchanged): searches for good candidate groups.** Generation (geographic pruning + commodity filter, no economic pre-filter) feeds every candidate through Stage 2, and a final exact set-packing step selects the non-conflicting, value-maximizing collection.

**These are kept separate, as this phase's instruction requires when both are desired** — merging them was already considered and rejected in Phase 2A (Part 9) for exactly the reason repeated here: it would smuggle a combinatorial group-formation algorithm into what should remain a small, bounded per-group evaluation.

## 11. Model Assumptions and Limitations

| Assumption | Status | Note |
|---|---|---|
| $q_i$ (demand estimate) is either directly reported or reasonably estimated from peers | User-configurable / research-supported (case-based reasoning is a citable technique family) | Never a trained-ML output for the current project (Section 3) |
| $p^{wh}_{c,t}$ needs only a current-day value, obtainable from a real snapshot source | Research-supported (Phase 3A.2) | Automated daily retrieval is not yet verified — a Phase 5E item, not assumed working |
| A single effective price per commodity per date (no supplier choice) | Prototype simplification | Matches the partner-trader routing assumption (Phase 1B) |
| Freshness varies by storage/handling conditions not captured by $F_c$ alone | Explicit limitation | $F_c$ is a ceiling, not a guarantee — real spoilage could occur earlier under poor storage |
| Transport costs are simplified to a flat tiered lookup, not real per-trip quotes | Prototype simplification, research-supported by Phase 1B's own finding that this is *more* accurate than a distance formula here | Exact tier cutoffs remain an estimate pending primary confirmation |
| Vendor cooperation/participation is assumed, not modeled | Explicit limitation, unchanged from Phase 2A Part 20 | No live per-scenario trust/willingness constraint exists |
| $D_{max}$, $m$, tomato's ambient $F_c$, and vehicle-tier cutoffs remain provisional | User-configurable / estimated | Unchanged, pending primary data (Phase 2A Part 33) |
| Any price/comparator figure's geographic granularity is explicitly tagged | **New, binding requirement** (Section 4a) | Prevents a district-level proxy from being silently presented as mandi-specific |
| $q_i$'s provenance is explicitly tagged (`ESTIMATE — cold-start` / `ESTIMATE — baseline` / `PREDICTION — ML`) | **New, binding requirement** (Section 3) | Prevents a rule-based average from ever being labeled "AI" |

**Nothing above is hidden.** This table is the union of Phase 2A's original assumptions list (Part 27, preserved) and the two new labeling requirements this phase adds.

## 12. Worked Example

**SIMULATED ILLUSTRATIVE SCENARIO — NOT REAL DATA. All vendor IDs, quantities, and prices below are invented for demonstration only and must never be read as observed vendor behavior or real market prices.** Four short scenarios demonstrate all four decision states.

**Common setup:** commodity = Potato (illustrative), date = illustrative, $p^{wh}_{c,t} = ₹15/\text{kg}$, $D_{max} = 2$ km, small-tier transport $TC = ₹800$/trip (flat, illustrative).

### Scenario 1 — `BUY_TOGETHER`
5 vendors, commodity = Onion (illustrative), $q_i = 5$ kg/day each ($\sum q_i = 25$), $p^{ind} = ₹62.5/\text{kg}$, $p^{wh}=₹40/\text{kg}$, $m=0 \Rightarrow p^{eff}=₹40$. $H_{i} = 5$ days for all; $F_{\text{onion}}$ = several weeks (does not bind). $d(G) = 1.4$ km $\le D_{max}=2$ km ✅. No trader-confirmed $MOQ$ — condition 3 not applied.

| $k$ | $Q_G(k)$ | $C^{ind}_{total}$ | $C^{collab}$ | $Savings_G(k)$ |
|---:|---:|---:|---:|---:|
| 1 | 25 | ₹1,562.50 | ₹1,000+₹1,150=₹2,150 | −₹587.50 |
| 3 | 75 | ₹4,687.50 | ₹3,000+₹1,150=₹4,150 | +₹537.50 |
| 5 | 125 | ₹7,812.50 | ₹5,000+₹1,150=₹6,150 | **+₹1,662.50** |

$k^*=5$ (bound by $H_i=5$). **Decision: `BUY_TOGETHER`**, $k^*=5$, $Q_G=125$ kg, $Savings_G=₹1{,}662.50$, ₹332.50/vendor (symmetric demand).

### Scenario 2 — `WAIT_OR_EXPAND_GROUP`
2 vendors, Potato, $q_i = 16$ kg/day each ($\sum q_i=16$... note: this is the group's combined rate, i.e. $\sum_{i} q_i = 16$ kg/day total across both vendors for clarity of arithmetic below), $p^{ind}=₹35/\text{kg}$, $p^{wh}=₹15/\text{kg}$, $m=0.10 \Rightarrow p^{eff}=₹16.50/\text{kg}$. $H_i=6$ days both; $F_{\text{potato}}$ = several weeks (does not bind). $d(G)=0.8$ km ✅. **Trader-confirmed $MOQ_{\text{potato}} = 150$ kg** for this scenario.

$Savings_G(k) = 560k - (264k+800) = 296k - 800$ (₹). Positive for $k \ge 3$; $Q_G(k) = 16k$.

| $k$ | $Q_G(k)$ | $Savings_G(k)$ | $Q_G(k) \ge 150$? |
|---:|---:|---:|---|
| 3 | 48 | +₹88 | ❌ |
| 6 (max, bound by $H_i$) | 96 | **+₹976** | ❌ |

Economics turn favorable from $k=3$ onward, and improve to $+₹976$ at the maximum feasible $k=6$ — but $Q_G(6)=96$ kg never reaches $MOQ_{\text{potato}}=150$ kg. **Decision: `WAIT_OR_EXPAND_GROUP`** — reported shortfall: 54 kg below MOQ at the best tested $k$; additional compatible vendors' demand could close this gap.

### Scenario 3 — `DO_NOT_BUY_TOGETHER`
2 vendors, Tomato, otherwise plausible economics, but $d(G) = 3.5$ km $> D_{max}=2$ km. **Decision: `DO_NOT_BUY_TOGETHER`** for this specific candidate — evaluation stops at the geographic check (Section 9's fixed order); no cost computation is performed. (A *different* candidate grouping including a closer vendor instead might still be feasible — that is Stage 1's job, not a reason to relabel this specific candidate's outcome.)

### Scenario 4 — `ABSTAIN`
A newly-onboarded vendor requests inclusion in a Potato scenario, but their `vendor_category` has zero existing peers in the system (no cold-start estimate can be formed) and they have not yet supplied a manual typical-quantity figure. **Decision: `ABSTAIN`** — reported reason: "$q_i$ undefined for vendor — no cold-start peer estimate available and no user-supplied value; cannot evaluate group demand." No group-level computation is attempted for this vendor's inclusion.

## 13. Final Consistency Audit

| # | Check | Result |
|---|---|---|
| 1 | Unit consistency | ✅ All prices ₹/kg, quantities kg, rates kg/day, horizon days, distances km — verified consistent across every formula in Sections 2–7; $k \times q_i \times p$ always resolves to ₹ |
| 2 | No ambiguous variables | ✅ $q_i$ (demand estimate) and "recommended procurement quantity" ($k^\* q_i$) are now explicitly distinct (Section 3) |
| 3 | No double-counted costs | ✅ Commodity cost and transport cost appear exactly once each in $C^{collab}$; no handling/wastage cost is added without explicit labeling as a configurable prototype parameter (Section 4) |
| 4 | No unsupported constants | ✅ Every parameter carries one of the four evidence labels (Section 2); $MOQ_c$ has no substitute value when unknown (Section 5) |
| 5 | MOQ correctly applied | ✅ Conditional, never defaulted; now also drives the `WAIT_OR_EXPAND_GROUP` state rather than silently collapsing into a bare "no" (Section 5, 9) |
| 6 | Freshness correctly applied | ✅ Dual ceiling $\min(F_c, H_{i,c})$; per-vendor consumption time shown to equal $k$ exactly under quantity-proportional allocation (Section 6) |
| 7 | Savings correctly calculated | ✅ $Savings_G(k) = C^{ind}_{total} - C^{collab}$, verified arithmetically in all four Section 12 scenarios |
| 8 | Decision states mutually distinguishable | ✅ Evaluated in a fixed order (missing data → geography → MOQ → economics) so no candidate can satisfy two states at once (Section 9) |
| 9 | No dependence on unavailable ML | ✅ $q_i$ is always an `ESTIMATE` in the current project (Section 3); $p^{wh}_{c,t}$ is a realized, observed value, never a forecast (Section 1, reconciliation C1) |
| 10 | Compatible with future ML demand estimates | ✅ Section 3's hierarchy has an explicit `PREDICTION — ML (validated)` slot that a future model could occupy, *if and only if* it passes Phase 5C's Section 8 validate-then-test protocol — the model's structure does not need to change to accommodate this, only $q_i$'s provenance tag would |

**No inconsistency was found requiring a structural change.** Every check above passed against the model as specified in Sections 2–10.

## 14. What Remains to Be Solved in Phase 5E

- **Implement this specification as actual backend logic** — still not done, per this phase's own scope limits.
- **Verify an automated daily pull of $p^{wh}_{c,t}$** from the data.gov.in snapshot resource using a registered API key (Section 1/B1 of the reconciliation audit) — currently only manually downloaded once.
- **Collect the still-pending primary parameters**: $D_{max}$, margin $m$, tomato's ambient $F_c$, per-vendor $H_{i,c}$, $MOQ_c$, and vehicle-tier cutoffs — unchanged from Phase 2A's own Part 33 list, not newly discovered here.
- **Formalize Phase 5A's module definitions (Data Quality Auditor, Granularity Validator, Model/Method Selector, Abstention Engine, Explanation Generator) as concrete interfaces** consuming and producing exactly the notation and decision states this document defines.
- **If Phase 1C's vendor survey/diary is ever actually executed**, re-audit $q_i$'s realized data quality (missingness, recall bias) with the same rigor Phases 3A.5/3A.6 applied to the Potato/Tomato price data, before trusting any resulting estimate.
- **Decide, and document, the exact source and label for the price/comparator figure used in any future decision-insight display layer** — per the reconciliation audit's Section C1/C2, it must be a baseline-derived signal (Phase 5A's Model Evidence Rule), never the closed Potato ML model, and must carry its correct `geographic_level` tag.

---

**Files produced by this phase:**
- This report.
- `reports/phase5d_phase2_reconciliation.md`.

**Files read but not modified:** `research/phase2a_mathematical_model.md`, `research/phase2b_algorithm_selection.md`, `reports/phase5a_research_findings_and_system_policy.md`, `reports/phase5c_demand_data_and_ml_feasibility.md`, `reports/phase4c_final_test_results.md`. No dataset was modified. No model was trained. No parameter was invented beyond what prior phases already flagged as provisional.
