# 📂 PROJECT DEVELOPMENT FILE — PHASE 2A
### Mathematical Problem Formulation & Collaborative Procurement Decision Model
**Subject:** An AI-Assisted, Freshness- and Logistics-Aware Collaborative Procurement Decision Framework for Street Vendors
**Question this phase answers:** Can the validated real-world problem (Phases 1A–1D) be converted into a precise, minimal, implementable computational and mathematical decision model — without inventing data, without forcing ML, and without selecting a final algorithm?

**Data labeling used throughout:** 🟢 REAL PUBLIC DATA · 🔵 REAL PRIMARY DATA (to be collected per the Phase 1C timeline) · 🟡 EXPERIMENTAL ASSUMPTION · 🟠 SIMULATED DATA

This document does not re-derive facts already established in Phases 1A–1D; it cites them by section number and builds the mathematical model on top of them. Where a prior phase left a number as a range or an assumption, that status is carried forward unchanged — this phase formalizes structure, it does not upgrade evidence.

---

## 1. Executive Summary

**Verdict: 🟢 MODEL APPROVED → PROCEED TO PHASE 2B.**

The naive draft model (the prompt's own starting point) over-specified decision variables that don't need to exist and under-specified the one design choice that actually drives the project's central economic tension. This version incorporates a reviewer pass that caught three further refinements (below); four corrections matter most:

**First**, "which commodity to procure" and "which vendors form a group" are not free decisions this model should solve — V1 works from a fixed, small commodity set (onion, potato, tomato — Phase 1B, Section 4) and treats candidate-group generation as a separate upstream step (Part F). What this phase actually needs to formalize is, given a candidate group already proposed for a commodity on a given day: (a) a go/no-go call, and (b) **how many days' worth of demand to bundle into one order** — a genuine decision variable that the naive draft omitted entirely, even though it is exactly the tension Phase 1B's freshness analysis (Section 12) already demonstrated numerically (buying more amortizes the fixed transport charge but raises spoilage risk).

**Second**, that order-horizon variable is bounded by two independent things, not one. Freshness sets a *biological/physical* ceiling on how long the commodity stays usable — but a real vendor's practical ability to buy several days ahead is separately limited by cash on hand, storage space, and how confident they are in their own near-term sales, none of which freshness measures. **Corrected:** the horizon is capped by $k \le \min(F_c, H_{i,c})$ across a group's members (Part 7, Part 19) — freshness and practical procurement capacity are two distinct constraints that happen to both bound the same variable, not one constraint wearing two names. Within whichever of the two binds first, net savings is still monotonically non-decreasing in the horizon within a fixed vehicle-cost tier, so the per-group "optimization" this phase needs remains a trivial bounded search over a handful of integers, not a hard combinatorial problem. **The real combinatorial problem is upstream: which vendors should be proposed as a candidate group in the first place.** That is Phase 2B's actual subject, and this phase deliberately does not solve it — it only defines the cost/feasibility function Phase 2B's algorithm will need to evaluate candidate groups against.

**Third**, several parameters in the naive draft (a distance-based transport formula, minimum order quantity, a maximum-acceptable-cost cap, a weighted viability score) are corrected or dropped because Phases 1B/1C already found they are either factually wrong for this context (per-km transport pricing), not reliably obtainable (a formal MOQ), redundant (a cost cap on top of a savings threshold), or would require preference data that does not exist (composite weights) — consistent with the refined problem statement's earlier decision to drop the weighted "viability score" as a core metric. **Corrected further this pass:** a formal MOQ and the Phase 1B break-even quantity are not the same kind of thing — one is a supplier-side procurement rule, the other is where the economics turn favorable — so they no longer share a constraint slot (Part 18); the break-even figure is retained purely as an explanatory number attached to the economic-feasibility check (Part 16), not as an independent gate that could redundantly duplicate it.

**Fourth**, the original demand-uncertainty treatment applied a small percentage "haircut" ($\alpha_c$) to perishable-commodity demand with no data-grounded way to justify *why* that specific percentage. **Corrected:** the core model now aggregates demand from the observed/estimated rate $r_{i,c}$ directly, with no built-in adjustment factor; conservatism is handled instead as an explicit, labeled low/base/high demand **scenario** (Part 12, Part 25) — a comparison a reader can inspect, rather than a single constant baked silently into the headline numbers.

The resulting model is deliberately small: two real decision variables, one scalar objective, and a small hard-constraint set — economic, geographic, and freshness/practical-horizon apply unconditionally, with a procurement-quantity (MOQ) constraint applied only where a real MOQ is confirmed to exist. No soft constraints, no probability distributions fitted to data too thin to support them, and no algorithm selection. It is built to survive contact with the actual field data once collected (Phase 1C's Weeks 1–6 timeline), not to look sophisticated on paper.

---

## 2. Refined Computational Problem Definition

**Rejected as imprecise (per the prompt's own instruction):**

> "Given a set of small vendors with commodity requirements, locations, current procurement prices, and operational constraints, determine whether collaborative procurement is beneficial and identify feasible vendor groups that minimize procurement cost or maximize net economic benefit."

This blends two different computational problems (finding good groups vs. evaluating a given group) and leaves "minimize cost" and "maximize benefit" as if they were interchangeable, which Part 15 below shows they are not.

**Refined definition, split into its two real stages:**

> **Stage 1 (candidate-group generation, Phase 2B's subject):** From the set of vendors currently requiring a given commodity on a given day, propose one or more candidate subsets ("candidate groups") worth evaluating for joint procurement, using geographic and/or demand information.
>
> **Stage 2 (this phase's subject — the decision model):** For a given candidate group, commodity, and date, determine (a) the maximum number of days' demand that can safely and practically be bundled into a single order without exceeding the commodity's freshness window, the group's own practical procurement capacity, geographic, or economic constraints, and (b) whether, at that bundling level, collaborative procurement produces strictly positive net savings relative to the group's members procuring individually — recommending collaboration only if so.

Stage 2 is fully specified by this document. Stage 1 is referenced only to the extent needed to define its input/output contract with Stage 2 (Part 3); its internal mechanism is explicitly out of scope here (Rule 2).

---

## 3. System Decisions

| Decision | Description | V1 Priority | Reason |
|---|---|---|---|
| **Group formation** (which vendors are proposed together) | Stage 1 above | 🟢 Essential, but **delegated** — this model consumes a candidate group as an input, it does not compute group membership itself (Part 6) | This is the one genuinely combinatorial part of the problem; solving it inside this phase's cost model would smuggle an algorithm choice into a phase that is explicitly forbidden from selecting one (Rule 2) |
| **Go/No-Go** (recommend collaborative procurement for this group/commodity/day or not) | Stage 2 core output | 🟢 Essential | This is literally the question the refined problem statement (Phase 1A onward) exists to answer |
| **Order horizon** (how many days' demand to bundle into one order) | Decision variable, bounded by *both* freshness and the group's practical procurement capacity | 🟢 Essential | Omitting this collapses the freshness-vs-transport-amortization tension that is the project's central economic finding (Phase 1B, Section 12) into a non-decision; keeping it is what makes the freshness constraint mathematically meaningful rather than decorative. Freshness alone is not sufficient to bound it — a commodity can stay fresh far longer than a small vendor can realistically afford or store to buy ahead for (Part 7, Part 19) |
| **Which commodity to jointly procure** | — | ❌ Excluded as a decision | V1 works from a fixed, pre-selected commodity set (onion, potato, tomato — Phase 1B Section 4); the model evaluates one commodity per scenario (Phase 1D's already-approved "commodity–vendor-cluster–date" unit of analysis), it does not choose among commodities |
| **Aggregate quantity procured** | — | ❌ Excluded as a free decision | Fully derived once group membership and order horizon are fixed (Part 12) — making it independently "chosen" would double-count the order-horizon decision |
| **Whether the procurement is economically beneficial** | — | ❌ Not a separate decision | This is a constraint evaluated *inside* the Go/No-Go decision (Part 20), not a standalone system choice |
| **Whether the procurement is operationally feasible** | — | ❌ Not a separate decision | Same reasoning — folded into Go/No-Go as one of several feasibility checks (Part 20) |

**Be strict, per the prompt's instruction:** this model makes exactly two computational decisions (Go/No-Go, Order Horizon) for each candidate group it is handed, and treats everything else (which vendors are candidates, which commodities exist, how much is derived-demand) as either an upstream input or an arithmetic consequence.

---

## 4. Decision-Maker and System Role

**The system is decision support, not autonomous procurement** — this was already established in Phase 1D (Part 14, "Ethical and Practical Validation") and is reaffirmed here as a modeling constraint, not just an ethical stance: the model's output (Part 24) is a recommendation plus its reasoning (which constraints passed/failed, at what horizon, with what estimated savings), delivered to vendors via the dashboard already scoped in the refined problem statement (component 9). No decision variable in this model represents "place the order" — only "recommend placing the order."

**Who acts on the recommendation:** given Phase 1B's payment-feasibility finding (Section 13) that the most realistic V1 payment models are Model 4 (a trusted anchor/lead vendor collects and pays) or Model 5 (a partner trader extends group credit), the natural real-world decision-maker who converts a "yes" recommendation into an actual order is either the anchor vendor or the partner trader — not each individual vendor acting alone, and not the platform. The model itself is agnostic to this (it evaluates the group as a unit either way), but this should be stated explicitly in the system design so the eventual interface doesn't imply an autonomous or fully decentralized ordering flow that the payment model doesn't actually support.

---

## 5. System Entities

| Entity | Meaning | Required for V1? | Reason |
|---|---|---|---|
| **Vendor** | An individual street vendor, identified by anonymous ID (Phase 1C schema) | ✅ Yes | Core unit vendor-side data attaches to |
| **Commodity** | One of the fixed V1 set (onion, potato, tomato) with an associated freshness window | ✅ Yes | Core unit commodity-side data attaches to |
| **Vendor–Commodity Requirement** | A (vendor, commodity) pair with an associated daily consumption rate | ✅ Yes | This is what demand aggregation sums over (Part 12); without it "group demand" has no defined components |
| **Procurement Group (candidate)** | A subset of vendors proposed together for one commodity on one date | ✅ Yes | The unit Stage 2 evaluates |
| **Procurement Scenario** | One (candidate group, commodity, date) triple — Phase 1D's already-approved experimental unit | ✅ Yes | Every calculation in this document is scoped to one scenario; keeping it explicit avoids ambiguity about what a "result" refers to |
| **Market/Supplier** | The source of the wholesale reference price for a commodity on a date | ✅ Yes, but simplified | Per the refined problem statement's explicit operating assumption (routing through a single partner trader/commission agent, not open mandi access), V1 treats this as **one effective price per commodity per date**, not a set of competing suppliers to choose among (Part 17) — modeling supplier choice would be inventing a decision the field context doesn't actually offer in V1 |
| **Transport Event** | — | ❌ Not a separate entity | Folded into the Procurement Group as a derived cost attribute (Part 13); a group's one order implies at most one transport trip in V1's single-collection-point design (Phase 1B, Section 2), so there is nothing a separate entity would represent |
| **Time/Date** | The day a scenario is evaluated | ✅ Yes | Prices (Agmarknet) and the go/no-go decision are both explicitly re-evaluated daily (Phase 1B, Section 11's volatility finding) — date is a required index, not decoration |
| **Freshness Constraint** | — | ❌ Not a separate entity | It is an attribute of Commodity (`freshness_window_days`, already in the Phase 1C schema), not an object with its own identity |

---

## 6. Mathematical Sets

| Symbol | Meaning | Required for V1? |
|---|---|---|
| $V = \{1, ..., n\}$, $n \approx 10\text{–}20$ | Vendors in the primary field sample (Phase 1C) | ✅ Yes |
| $C = \{\text{onion, potato, tomato}\}$ | Fixed V1 commodity set (Phase 1B, Section 4) | ✅ Yes — deliberately small, not a general commodity catalog |
| $T$ | Dates over which the scenario grid is evaluated (Phase 1D, Parts G/H) | ✅ Yes |
| $G_{c,t} \subseteq 2^{V}$ | The **candidate** groups proposed for commodity $c$ on date $t$ by the (out-of-scope) Stage 1 procedure — **not** the full power set of $V$ | ✅ Yes, as an input set; **not enumerated by this model** |
| $S$ (suppliers/markets, as separate choosable entities) | — | ❌ Excluded for V1 | Collapsed into a single per-commodity-per-date effective price parameter (Part 5); reintroducing a real supplier-choice set is future work if the single-partner-trader assumption is ever relaxed |

**On $G_{c,t}$:** the naive draft implicitly assumed $G$ is predefined and fixed. It is neither. It is (a) commodity- and date-specific, because who currently needs a commodity changes, and (b) generated, not enumerated — with $n \le 20$, the full power set ($2^{20} \approx 10^6$ subsets) is not something V1 should exhaustively evaluate, and doing so would smuggle in a brute-force "algorithm" this phase is not supposed to choose. Part 9 formalizes $G_{c,t}$ purely as an input Stage 2 receives.

---

## 7. Model Parameters

| Symbol | Meaning | Unit | Data Source | Real / Estimated / Assumed | Required for V1 |
|---|---|---|---|---|---|
| $r_{i,c}$ | Vendor $i$'s average daily consumption rate of commodity $c$ | kg/day | Survey (point estimate) or diary (mean, for the 5–10 vendor subset) | 🔵 Primary; for cold-start vendors, backstopped by Layer 1 similarity estimation (Phase 1C, Section 11) | ✅ Yes |
| $p^{ind}_{i,c}$ | Vendor $i$'s current, individually-paid procurement price for $c$ | ₹/kg | Survey/diary — the Priority 2 economic baseline (Phase 1C, Section 3 C2) | 🔵 Primary | ✅ Yes |
| $p^{wh}_{c,t}$ | Wholesale/mandi modal price for $c$ on date $t$ | ₹/kg | Agmarknet API — the Priority 1 economic baseline | 🟢 Real | ✅ Yes |
| $p^{eff}_{c,t}$ | Effective group-access price after an assumed trader margin | ₹/kg | $p^{wh}_{c,t} \times (1 + m)$, $m \in \{0, 0.10, 0.15\}$ | 🟡 Assumption — Phase 1B, Section 10 explicitly flagged the raw mandi price as a best-case figure | ✅ Yes, as a sensitivity parameter (Part 17) — $m=0$ is not asserted as fact |
| $L_i = (\text{lat}_i, \text{lon}_i)$ | Vendor $i$'s approximate stall coordinates | decimal degrees | Survey, tied only to anonymous ID (Phase 1C, Section 3 C4 / Section 14) | 🔵 Primary | ✅ Yes |
| $d(g)$ | Maximum distance from any member of group $g$ to $g$'s centroid | km | Derived from $L_i$ (Haversine) | Derived, not independently collected | ✅ Yes |
| $D_{max}$ | Maximum acceptable centroid distance | km | — | 🟡 Assumption — 1–2 km starting radius (Phase 1B, Section 7) | ✅ Yes, explicitly labeled provisional |
| $F_c$ | Freshness window for commodity $c$ — the *biological/physical* ceiling on order horizon | days | FAO/USDA ARS (refrigerated, scientific) with an ambient downward extrapolation, or trader-practical triangulation | 🟢 scientific / 🟡 assumed / 🔵 trader-practical — kept as three distinct sub-labels per the Phase 1C schema's `freshness_window_source` field, never merged | ✅ Yes |
| $H_{i,c}$ | Vendor $i$'s maximum **practical** procurement horizon for commodity $c$ — the cash-flow/storage/confidence ceiling on order horizon, independent of freshness | days | Survey — vendor-declared maximum buying interval, or, where that isn't reliably answerable, the vendor's current purchase frequency $f_{i,c}$ as a fallback proxy | 🔵 Primary if directly declared; 🟡 assumption where derived from purchase frequency instead | ✅ Yes — added per reviewer correction; **do not invent a value where neither source is available** (Rule 1) |
| $TC(\text{tier})$ | Flat local transport charge for a vehicle-capacity tier | ₹/trip | Commercial rental listings, Hyderabad (Phase 1B, Section 6) | 🟢 Real, bounded ranges; exact tier weight cutoffs (e.g., ~750 kg) are 🟡 assumption | ✅ Yes |
| $MOQ_c$ | Trader-confirmed minimum order quantity | kg | Trader interview (Phase 1C, Section 7) | 🔵 Primary **if obtained** — Phase 1C explicitly rates this only "Should Have," not guaranteed | ⚠️ Conditional — Part 18; **no fallback value is substituted when absent, the constraint is simply not applied** (reviewer correction) |
| $BE_c(t)$ | Break-even quantity — the quantity at which $NetSavings_{g,c}(k)=0$ | kg | Computed from $p^{ind}_{i,c}$, $p^{eff}_{c,t}$, $TC(\text{tier})$ | Derived, not independently collected | ✅ Yes, but **only as an explanatory/display figure attached to economic feasibility (Part 16) — not a constraint in its own right** (reviewer correction, Part 18) |
| $Savings_{min}$ | Minimum acceptable net savings (beyond strictly positive) | ₹ | — | 🟡 Assumption, sensitivity-only | 🔵 Nice to have — **not** part of the V1 hard constraint (Part 16) |
| Purchase frequency $f_{i,c}$ | Raw survey field | times/period | Survey | 🔵 Primary | ⚠️ Not a model parameter in its own right for demand aggregation — used to help derive $r_{i,c}$, and doubles as the fallback proxy for $H_{i,c}$ above where a direct answer isn't obtainable |
| Maximum acceptable procurement cost | — | — | — | — | ❌ Excluded — redundant with $NetSavings_g > 0$ (Part 16); adding a second, separately-thresholded cost cap with no data to justify its value would be exactly the kind of unjustified parameter Rule 5 warns against |
| $\alpha_c$ (demand haircut) | — | — | — | — | ❌ **Removed per reviewer correction** — an unjustified fixed percentage with no data-grounded way to pick its value; replaced by explicit low/base/high demand scenarios (Part 12, Part 25) |

**Data classification is consolidated in Part 8.**

---

## 8. Data Classification

| Category | Parameters |
|---|---|
| 🟢 **REAL PUBLIC DATA** | $p^{wh}_{c,t}$ (Agmarknet); the scientific component of $F_c$ (FAO/USDA ARS refrigerated figures); $TC(\text{tier})$'s rate bands (commercial listings) |
| 🔵 **REAL PRIMARY DATA** | $r_{i,c}$ (and its low/high scenario bounds, Part 12), $p^{ind}_{i,c}$, $L_i$, $MOQ_c$ (where obtained), $H_{i,c}$ (where directly declared), the trader-practical component of $F_c$ |
| 🟡 **EXPERIMENTAL ASSUMPTION** | $p^{eff}_{c,t}$'s margin $m$, $D_{max}$, the ambient component of $F_c$ for tomato, $TC(\text{tier})$'s exact weight cutoffs, $Savings_{min}$, $H_{i,c}$ where derived from purchase frequency instead of directly declared |
| 🟠 **SIMULATED DATA** | Any of the above when used to generate the calibrated scenario grid for stress-testing group formation at scale (Phase 1C, Section 12) — not used in the real-vendor evaluation itself |

No parameter in this model is asserted as fact without one of these four labels attached, per Rule 6.

---

## 9. Decision Variables

| Variable | Meaning | Type | Required for V1 |
|---|---|---|---|
| $y_{g,c,t} \in \{0,1\}$ | 1 if group $g$ is recommended to procure $c$ collaboratively on date $t$ | Binary | ✅ Yes — the model's core output |
| $k_{g,c,t} \in \{1, ..., \lfloor \min(F_c, \min_{i \in g} H_{i,c}) \rfloor\}$ | Order horizon: how many days' worth of demand this order bundles | Bounded positive integer | ✅ Yes — the corrected addition (Part 1), bound corrected to include practical procurement capacity, not freshness alone (reviewer correction) |
| $x_{i,g}$ (vendor membership in candidate group $g$) | — | — | ❌ **Not a decision variable in this model** — it is an *output of Stage 1* (Part 6/9's $G_{c,t}$), consumed here as a given. Treating it as jointly optimizable within Stage 2 would re-introduce the combinatorial group-formation problem this phase explicitly defers to 2B |
| $Q_{g,c}(k)$ (aggregate quantity) | — | — | ❌ **Derived**, not a decision variable (Part 12) — it is a deterministic function of $g$, $c$, and $k_{g,c,t}$ |

**Why $k_{g,c,t}$ must be a real decision variable and not a fixed constant:** if $k$ were hardwired to 1 (always buy exactly one day's demand), neither the freshness constraint nor the practical-horizon constraint would ever bind for any commodity in the tested range (Phase 1B's Scenario 1 in Section 12 already showed 1-day orders sit "well within window" for all three commodities) — the entire freshness-aware design premise (component 6 of the refined problem statement) would have nothing to do. Making $k$ a bounded choice is what lets the model actually trade off transport-cost amortization against spoilage risk and against practical buying limits, which is the mechanism Phase 1B's Section 12 exists to demonstrate.

**Why the bound is $\min(F_c, H_{i,c})$ and not $F_c$ alone:** freshness measures whether the commodity is still usable; it says nothing about whether a small, cash-constrained vendor can actually afford, store, or confidently commit to several days' worth of stock at once. A potato can physically last weeks, but a vendor who only ever buys 2–3 days ahead (limited cash, limited storage, uncertain sales) would not realistically follow a 5-day recommendation just because the potato would survive that long. Collapsing these into one constraint would silently assume storage/cash-flow capacity tracks shelf life, which has no basis in anything established in Phases 1A–1D. $H_{i,c}$ is deliberately vendor-specific (not a single per-commodity constant like $F_c$), since practical buying capacity is a property of the vendor, not the commodity; for a group, the binding value is the tightest member's, $\min_{i\in g} H_{i,c}$, since the whole group's order is capped by whichever member can least afford to buy ahead.

**Why $x_{i,g}$ is correctly excluded, per the prompt's own prompt to "determine whether explicit groups $G$ should even be predefined":** predefining and solving over an exhaustive $G$ inside this cost model would conflate two different kinds of problem — a combinatorial search over group membership (Stage 1, unbounded in structure, Phase 2B's job) and a small bounded evaluation over order horizon (Stage 2, at most $F_c$ ≈ single-digit options, this document's job). Keeping them separate is what makes both problems individually simple; merging them would make the whole thing needlessly harder to reason about and would pre-empt Phase 2B's algorithm choice.

---

## 10. Individual Procurement Cost Model

For vendor $i$, commodity $c$, over an order horizon of $k$ days:

$$C^{ind}_{i,c}(k) = k \times r_{i,c} \times p^{ind}_{i,c}$$

**Transportation is excluded from this formula**, carrying forward Phase 1B's Section 2 finding verbatim: individual vendor transport is largely an embedded time/opportunity cost bundled into routine trips or trader-advance arrangements, not a distinct cash outflow comparable to a dedicated group transport charge. Forcing a monetary figure onto it without primary data would be inventing a number (Rule 1). This is stated here as a carried-forward limitation, not re-litigated.

**Total individual cost for a group's members**, used as the comparison baseline (Part 15):

$$C^{ind}_{total,g}(k) = \sum_{i \in g} C^{ind}_{i,c}(k)$$

evaluated at the **same $k$** as the collaborative alternative, since comparing a 1-day individual baseline against a 5-day collaborative order would not be a fair comparison (Phase 1D's fair-comparison rule, Part L).

---

## 11. Collaborative Procurement Cost Model

$$C^{collab}_{g,c}(k) = Q_{g,c}(k) \times p^{eff}_{c,t} + TC_g(k)$$

Handling and wastage costs remain excluded from the base-case formula, per Phase 1B Section 2's finding that no real data exists to populate them — this is carried forward unchanged, not re-decided here.

**On $p^{eff}_{c,t}$ versus raw $p^{wh}_{c,t}$:** Phase 1B's own caution (Section 10) is that the raw mandi average is a best-case, upper-bound figure, since actual group access will likely run through a registered trader charging a margin. The V1 hard model uses $p^{wh}_{c,t}$ (margin $m=0$) as the primary, most-defensible figure because it is the one figure that is 🟢 real rather than assumed — but every result must also be reported at $m \in \{0.10, 0.15\}$ as a labeled sensitivity variant, not folded silently into the headline number.

---

## 12. Demand Aggregation Model

$$Q_{g,c}(k) = k \times \sum_{i \in g,\ r_{i,c} > 0} r_{i,c}$$

using the observed/estimated daily rate $r_{i,c}$ directly — no adjustment factor is applied inside this core formula (see "On demand uncertainty" below for why). Vendors in $g$ with $r_{i,c} = 0$ (no demand for $c$) are simply excluded from the sum — a group can contain such vendors (they may be relevant for a different commodity's scenario), they just contribute nothing to this particular commodity's aggregation.

**On modeling one commodity at a time:** a real group order could in principle bundle multiple commodities into a single transport trip, sharing the fixed transport charge across them — this would improve the economics further and is worth flagging as a genuine future extension (Part 28). V1 does **not** model this, because Phase 1D already fixed the experimental unit as a single "commodity–vendor-cluster–date" scenario (its Part on Final Research Methodology). Reopening that here, mid-formalization, would create an inconsistency with an already-approved methodology rather than a genuine correction — so it is deliberately deferred, not silently reintroduced.

**On demand uncertainty (corrected per reviewer comment):** the refined problem statement's newsvendor-style "uncertainty-aware ordering" concept remains conceptually right, but Phase 1C (Sections 9–10) already found that a fitted demand *distribution* is only weakly supportable outside the 5–10 vendor diary subset. An earlier version of this model handled that by applying a fixed percentage "haircut" to $r_{i,c}$ for perishable commodities — that has been removed, because there was no data-grounded way to justify *why* it should be 10% rather than 5% or 30%; a constant like that would read as a number invented to make the model look safer, which is exactly what Rule 1 warns against, even when honestly labeled as an assumption.

**Corrected treatment:** the core aggregation formula above uses $r_{i,c}$ (the base/observed estimate) with no built-in adjustment. Demand uncertainty is instead handled entirely as an explicit, labeled **scenario comparison**, evaluated alongside the base case rather than folded into it:

$$r^{low}_{i,c} < r^{base}_{i,c} = r_{i,c} < r^{high}_{i,c}$$

with the low/high bounds drawn from whatever the diary subset's observed variability actually shows (for the 5–10 diary vendors), or, for cold-start vendors without diary data, from the range of the comparable-vendor estimates Layer 1's similarity reasoning already produces (Phase 1C, Section 11) — not from an invented percentage. Every result reported for a scenario should show all three rows side by side (🟡 low / base / 🟢 or 🔵 high, per Part 8's labeling) so a reader can see exactly how sensitive the recommendation is to demand uncertainty, rather than trusting a single pre-adjusted number. This is not a probability distribution and requires no distributional fitting — it is the same kind of small, explicit range already used elsewhere in this model (Part 7's $m$, Part 19's $F_c$ tiers). A fully probabilistic newsvendor treatment remains documented as future work once the diary dataset grows (Part 25, Part 28).

---

## 13. Transportation Cost Model

Per Phase 1B, Section 6's key structural finding, short intra-city trips are dominated by a near-fixed per-trip charge, not a linear per-km rate — so a $Rate \times Distance$ formula would not be a more sophisticated model here, it would be a *less accurate* one for this specific context. V1 uses a small, fixed vehicle-capacity lookup:

$$TC_g(k) = TC(\text{tier}(Q_{g,c}(k)))$$

| Tier | Capacity (🟡 assumed cutoff) | Cost band (🟢 real, Phase 1B Section 6) |
|---|---|---|
| Small (Chota Hathi / mini-truck) | up to ~750 kg | ₹800–1,500 |
| Medium (pickup/Bolero) | up to ~1.5 t | ₹1,200–2,500 |

Given V1's group sizes (7–15 vendors, 2–5 kg/vendor/day, $k \le \min(F_c, H_{i,c})$ ≤ single digits for the tested commodities), almost all realistic scenarios stay within the small tier — the medium tier exists mainly so the model doesn't silently misprice an unusually large group, not because V1 expects to need it often. **Level 2 (distance-based estimation) and Level 3 (route optimization) are explicitly rejected for V1** — Level 2 because Phase 1B's own data contradicts the assumption that makes it appropriate, and Level 3 because it is disproportionate to a single-collection-point, single-trip V1 design (Rule 4).

---

## 14. Cost Allocation Model

Per-vendor share of both the commodity cost and the transport cost is allocated **quantity-proportionally**:

$$\text{Share}_i = \frac{k \times r_{i,c}}{Q_{g,c}(k)} \times C^{collab}_{g,c}(k)$$

**Why quantity-proportional, not equal-split:** an equal split would overcharge low-demand vendors relative to what they actually consume and undercharge high-demand vendors — a fairness distortion with no data to justify it. Value-proportional splitting would require no additional information beyond what quantity-proportional already uses (since price is uniform within a scenario, value-proportional and quantity-proportional coincide here), so it adds complexity without adding a distinct outcome. **This allocation rule does not itself increase or manufacture savings** — it only redistributes an already-computed $C^{collab}_{g,c}(k)$ across members, which is the fairness property Part G of the prompt specifically asked to verify.

---

## 15. Net Benefit Model

$$NetSavings_{g,c}(k) = C^{ind}_{total,g}(k) - C^{collab}_{g,c}(k)$$

**Is maximizing net savings equivalent to minimizing total cost?** No, and this matters. Minimizing $C^{collab}_{g,c}(k)$ alone is a degenerate objective — it is trivially minimized at $k=0$ (order nothing), which is meaningless. The two objectives are only equivalent when demand is held fixed and exogenous; here it is not, because $k$ is itself a decision variable that scales both sides of the comparison. **Net savings, not raw cost, is therefore the only sensible primary objective for V1** — this is Option 2 from the prompt's list.

**A useful structural fact, not assumed but shown:** within a single transport tier (no tier boundary crossed), $C^{ind}_{total,g}(k)$ grows linearly in $k$ at the members' individual price, while $C^{collab}_{g,c}(k)$'s commodity term grows at the (lower) effective price and its transport term is constant. Since $p^{ind}_{i,c} > p^{eff}_{c,t}$ is exactly the condition that makes collaboration worth considering at all, $NetSavings_{g,c}(k)$ is **non-decreasing in $k$ within a tier**. This means the "optimization" over $k$ for a fixed, already-formed group is not a hard search problem — it is a small enumeration over at most $\lfloor \min(F_c, \min_{i\in g}H_{i,c}) \rfloor$ integers (plus a check at each tier boundary), which any straightforward evaluation can do exhaustively. **The genuinely hard, combinatorial part of this whole problem is Stage 1 (group formation), not this benefit calculation** — reinforcing Part 9's decision to keep them separate.

**Rejected:** Option 1 (minimize cost alone, degenerate, above); Option 4 (multi-objective/Pareto formulation) — rejected because V1 has exactly one real currency to optimize (rupees) once freshness/practical-horizon, geography, and procurement quantity are treated as hard constraints rather than competing objectives (Part 21), and introducing a second objective axis without a second thing worth trading rupees against would be complexity for its own sake, echoing the refined problem statement's earlier, already-made decision to drop the weighted "viability score."

**Recommended primary objective:** maximize $NetSavings_{g,c}(k)$ subject to the hard feasibility constraints of Parts 16–19 (this is Option 2/3 merged, since Option 3's "subject to feasibility" clause is not a distinct objective, just the constraint set already required).

---

## 16. Economic Feasibility

$$NetSavings_{g,c}(k) > 0 \quad \text{(hard constraint for V1)}$$

The prompt's question of whether a strictly-positive threshold is *sufficient*, versus requiring $NetSavings_{g,c}(k) \ge Savings_{min}$ for some minimum margin, is answered by not inventing a value for $Savings_{min}$: no primary or secondary data source establishes what margin is "worth the operational effort" for this vendor population, and asserting a number (e.g., "₹50" or "5%") would be exactly the kind of unjustified constant Rule 1 prohibits. **V1's hard constraint is the zero threshold.** A positive $Savings_{min}$ is retained only as a labeled 🟡 sensitivity variant, evaluated as part of the Phase 1D sensitivity analysis already planned (its Part 11), not baked into the core model.

**Break-even quantity as explanatory context (reviewer correction):** $BE_c(t) = TC(\text{small tier}) / (p^{ind}_{i,c} - p^{eff}_{c,t})$ — Phase 1B's own break-even formula (Section 10), evaluated with that day's prices — is exactly the quantity at which $NetSavings_{g,c}(k) = 0$. It is computed and displayed here as part of the vendor-facing "reasoning" output (component 9 of the refined problem statement, Part 23's Step 8) so a rejected recommendation can say *how far* a group's order fell short of being worthwhile, not just that it failed. **It is not applied as an independent constraint** — doing so alongside $NetSavings_{g,c}(k) > 0$ would check the same threshold twice under two different names, since $BE_c(t)$ is nothing more than that threshold expressed in kilograms instead of rupees (see Part 18 for the earlier, corrected version of this document, which conflated $BE_c(t)$ with a demand/MOQ constraint).

---

## 17. Geographic Feasibility

$$d(g) = \max_{i \in g} \text{Haversine}(L_i, \text{centroid}(g)) \le D_{max} \quad \text{(hard constraint)}$$

**Correction to the naive draft's pairwise formulation** ($d_{i,j} \le D_{max}$ for all pairs): Phase 1B (Section 2) already fixed the collection-point design as a single point at the vendor cluster's centroid, not a network of pairwise pickups. A centroid-distance constraint is both computationally simpler ($O(n)$ vs. $O(n^2)$ pairwise checks) and the constraint that is actually physically meaningful under that already-established design — a pair of vendors could be individually close to each other yet both far from any sensible single collection point, which pairwise checking alone would miss. $D_{max}$ itself remains the 🟡 1–2 km experimental starting radius from Phase 1B, Section 7, explicitly pending validation against real vendor location data.

---

## 18. Procurement Quantity Constraint (MOQ)

**Corrected per reviewer comment — this is no longer named or treated as "demand feasibility."** A formal minimum order quantity and the Phase 1B break-even quantity are two different kinds of thing, and blending them into one constraint under a single "demand feasibility" label mislabeled a supplier-side procurement rule as if it were something the vendors' own demand determines. $MOQ_c$ is a rule the trader/supplier imposes ("I won't sell wholesale below this quantity"); the break-even quantity is a point on the *economics*, not a procurement rule — it belongs to economic feasibility (Part 16), not here.

$$
\text{Procurement quantity constraint} =
\begin{cases}
Q_{g,c}(k) \ge MOQ_c & \text{if a trader-confirmed } MOQ_c \text{ exists for commodity } c \text{ (🔵)} \\
\text{— no constraint applied —} & \text{otherwise}
\end{cases}
$$

**No fallback value is substituted when $MOQ_c$ is unknown.** Phase 1C (Section 3, MVD table) already found that a formal trader-published MOQ may not exist for every commodity — an earlier version of this document filled that gap with the break-even quantity as a proxy, which the reviewer correctly flagged as smuggling an economic threshold in under a procurement label, and as producing exactly the redundancy the correction below removes. The corrected rule is simpler: **where $MOQ_c$ exists, apply it; where it doesn't, this constraint is inapplicable for that commodity — Part 16's economic-feasibility check (with its own break-even figure, computed and shown there) already does the real filtering work.**

---

## 19. Freshness and Practical Procurement Horizon

$$k_{g,c,t} \le \min\!\big(F_c,\ \min_{i \in g} H_{i,c}\big) \quad \text{(hard constraint, not a risk score, for V1)}$$

**Corrected per reviewer comment: this is two constraints sharing one bound, not one.** $F_c$ (Part 1's clean form still holds here) is the *biological/physical* ceiling — because $Q_{g,c}(k) = k \times \sum r_{i,c}$ and ConsumptionDays $= Q_{g,c}(k) / \sum r_{i,c} = k$ exactly (Phase 1B, Section 12's own ConsumptionDays formula), freshness feasibility reduces to a direct bound on the order-horizon variable itself. $H_{i,c}$ (Part 7, Part 9) is a separate, independent ceiling — the vendor's own practical capacity to buy several days ahead, governed by cash flow, storage space, and sales confidence, none of which freshness measures. A commodity can outlast a vendor's practical buying capacity (onion/potato, typically) or a vendor's practical buying capacity can outlast the commodity's freshness (tomato, typically) — either can be the one that actually binds, so both must be checked and the tighter one governs.

**Hard constraint, not a graded risk flag, is recommended for both components in V1** — for $F_c$, because there is no finer-grained spoilage-rate data (Phase 1B, Section 14 gap audit) to support a graded score, and a hard cutoff is simpler and no less defensible given the evidence available; for $H_{i,c}$, because it is meant to represent a real practical ceiling a vendor reported, not a soft preference to trade off against savings. Uncertainty in $F_c$ itself (particularly tomato's ambient figure) is handled by testing multiple $F_c$ values in the already-planned sensitivity analysis (Phase 1D, its H5 tiers); uncertainty in $H_{i,c}$ is bounded by using it only where a vendor gave a usable answer or a purchase-frequency proxy exists (Part 7), never invented outright — not by softening either constraint.

---

## 20. Operational Feasibility

**Excluded from the hard-constraint set for V1**, per the prompt's own warning against unmeasurable behavioral constraints. Vendor participation willingness and payment-model trust (Phase 1C, Sections A5–A6) are real concerns but have no quantitative, per-scenario measurement available — only the exogenous scenario tiers already defined in Phase 1D (H6: 50%/75%/100% assumed participation). **Recommendation:** treat vendor participation as a **scenario parameter for simulation/stress-testing** (already Phase 1D's role for it), not as a live constraint this decision engine evaluates for a specific real group on a specific day. Building a fabricated "trust score" into the hard-constraint set would violate Rule 1 far more than simply not modeling operational feasibility as a per-scenario check.

---

## 21. Hard and Soft Constraints

**Corrected structure per reviewer comment** — the constraint set is now the reviewer's recommended four, with procurement quantity separated from economic feasibility and freshness merged with the newly-added practical-horizon check rather than kept as a fifth item:

| # | Constraint | Hard / Soft | Reason | V1 Treatment |
|---|---|---|---|---|
| 1 | Procurement quantity ($Q \ge MOQ_c$) | Hard, **conditional** — applied only if $MOQ_c$ is confirmed | Where a trader genuinely won't transact below a quantity, no amount of savings changes that | Part 18 |
| 2 | Geographic feasibility ($d(g) \le D_{max}$) | Hard | Beyond this radius, the single-collection-point design (Phase 1B) is not physically realistic | Part 17 |
| 3 | Freshness & practical procurement horizon ($k \le \min(F_c, H_{i,c})$) | Hard | Violating $F_c$ directly causes spoilage/waste; violating $H_{i,c}$ recommends a purchase the vendor cannot practically make | Part 19 |
| 4 | Economic feasibility ($NetSavings > 0$) | Hard | A recommendation that loses money contradicts the system's entire decision-support premise; the break-even quantity $BE_c(t)$ is computed and shown here for explanation only, not as a separate gate | Part 16 |
| — | Operational feasibility (participation, trust) | **Excluded, not soft** | No per-scenario data exists to grade it; forcing a soft weight here would be inventing a number, not softening a real one | Not modeled as a constraint; used only as an exogenous simulation parameter |

**V1 uses zero soft constraints.** The naive draft's example ("preferred geographic proximity" as soft) is unnecessary once $D_{max}$ is itself the operative cutoff — introducing a second, gradient preference on top of a hard cutoff would require a weight, and no preference data exists to set one, which is precisely the reasoning that already led to dropping the composite "viability score" earlier in this project's history. A soft-constraint layer is documented as future work, contingent on collecting real vendor preference data (Part 28).

---

## 22. Objective Function

$$
\max_{k \in \{1,...,\lfloor \min(F_c, \min_{i\in g}H_{i,c}) \rfloor\}} \; NetSavings_{g,c}(k)
\quad \text{subject to Parts 16–19}
$$

with the resulting recommendation:

$$
y_{g,c,t} = \begin{cases} 1 & \text{if some } k \text{ satisfies Parts 16–19 simultaneously, evaluated at } k^* = \arg\max NetSavings_{g,c}(k) \text{ over the feasible set} \\ 0 & \text{otherwise} \end{cases}
$$

As shown in Part 15, this maximization is a bounded, small-integer enumeration for a fixed $g$ — not a search problem requiring an "algorithm" in the sense Phase 2B will investigate. Phase 2B's algorithm question concerns how $G_{c,t}$ (candidate groups) gets generated, not how this objective is evaluated once a group exists.

---

## 23. Collaborative Procurement Decision Rule

**Corrected sequence** (the naive draft's 7-step version checked demand before geography, had no notion of order horizon, and conflated a procurement rule with an economic threshold; this version reflects the reviewer's four-constraint structure from Part 21):

1. **Input:** a candidate group $g \in G_{c,t}$ (from Stage 1), commodity $c$, date $t$.
2. **Geographic feasibility (hard, Part 17):** compute $d(g)$; if $d(g) > D_{max}$, stop — $y_{g,c,t} = 0$.
3. **Determine the feasible horizon range:** $k \in \{1, ..., \lfloor \min(F_c, \min_{i\in g} H_{i,c}) \rfloor\}$ — freshness and practical procurement capacity applied together (Part 19).
4. **For each feasible $k$** (a small enumeration, Part 15): compute $Q_{g,c}(k)$, look up $TC_g(k)$'s tier, compute $C^{ind}_{total,g}(k)$, $C^{collab}_{g,c}(k)$, and $NetSavings_{g,c}(k)$.
5. **Procurement quantity constraint (hard, conditional, Part 18):** discard any $k$ for which $Q_{g,c}(k) < MOQ_c$ — **only if a trader-confirmed $MOQ_c$ exists for this commodity; otherwise skip this step entirely.**
6. **Economic feasibility (hard, Part 16):** among the remaining $k$, keep only those with $NetSavings_{g,c}(k) > 0$; compute $BE_c(t)$ alongside for the explanatory output, not as a further filter.
7. **If any $k$ survives:** set $y_{g,c,t}=1$, $k_{g,c,t} = \arg\max NetSavings_{g,c}(k)$ over the survivors; compute per-vendor allocations (Part 14).
8. **If none survives:** set $y_{g,c,t}=0$; record which constraint(s) failed at every tested $k$ (including, where relevant, how far $Q_{g,c}(k)$ fell short of $BE_c(t)$), so the vendor-facing output can explain *why* (supporting the refined problem statement's "reasoning" requirement, component 9), not just state a bare no.

Operational feasibility (Part 20) is deliberately absent from this sequence — it is not evaluated live per scenario.

---

## 24. Input → Process → Decision → Output Model

**INPUT:** $r_{i,c}$ (base, plus low/high scenario bounds), $p^{ind}_{i,c}$, $p^{wh}_{c,t}$, $L_i$, $F_c$, $H_{i,c}$, $TC(\text{tier})$, $MOQ_c$ (if known), a candidate group $g \in G_{c,t}$ from Stage 1.

**PROCESSING:** demand aggregation from the base rate, with low/high scenarios run in parallel (Part 12) → geographic check (Part 17) → horizon enumeration bounded by $\min(F_c, H_{i,c})$ (Part 19/23) → cost and net-savings computation (Parts 10–11, 15) → procurement-quantity check, only if $MOQ_c$ known (Part 18) → economic check, with $BE_c(t)$ computed for explanation (Part 16) → allocation (Part 14).

**DECISION:** $y_{g,c,t} \in \{0,1\}$ and, if 1, $k_{g,c,t}$.

**OUTPUT:** recommended horizon and aggregate quantity, per-vendor allocated share and estimated individual savings, the constraint(s) that passed or failed (for transparency), and — only if $y_{g,c,t}=1$ — the recommendation itself, delivered as decision support (Part 4), never as an automatic order.

---

## 25. Uncertainty Handling

Per Phase 1C's finding that a fitted demand distribution is only weakly supportable outside the small diary subset, V1 uses **simple ranges and scenario analysis**, not probabilistic modeling:

- Demand uncertainty is handled by the explicit low/base/high $r_{i,c}$ scenario comparison (Part 12), reported side by side rather than folded into a single adjusted figure — this replaces an earlier fixed-percentage haircut ($\alpha_c$) that the reviewer correctly flagged as an unjustified constant.
- $p^{eff}_{c,t}$'s margin $m$, $D_{max}$, $F_c$, and now $H_{i,c}$ are each varied across small, explicit tiers rather than treated as point-certain (this is exactly Phase 1D's already-approved sensitivity analysis, Parts H/I of that document — not duplicated here, only relied upon).
- No chance-constrained or stochastic-programming formulation is introduced. Given the sample sizes established in Phase 1C (Section 9), fitting and validating a real probability distribution for demand or price would produce a false sense of statistical rigor the data cannot support — exactly the "fake statistical significance" risk this project has been told throughout to avoid.

---

## 26. Numerical Illustrative Example

**ILLUSTRATIVE EXAMPLE — NOT REAL DATA.** Figures are drawn from Phase 1B's real bounded ranges (Sections 5, 6, 9) for plausibility, but the specific group and vendor IDs are hypothetical.

Group $g$ = 5 vendors, commodity = onion, date = illustrative. $r_{i,\text{onion}} = 5$ kg/day each (🟡 Phase 1B base-case assumption — this is the base scenario; a full analysis would run this table again at low/high $r_{i,c}$ per Part 12), so $\sum r_{i,c} = 25$ kg/day. $p^{ind} = ₹62.5/\text{kg}$ (Phase 1B retail midpoint), $p^{wh} = ₹40/\text{kg}$ (Phase 1B, Section 5), $m=0$. $F_{\text{onion}} = $ several weeks (long shelf life), so freshness does not bind in this example. All 5 vendors declared a maximum practical buying interval of $H_{i,\text{onion}} = 5$ days (🔵 vendor-declared, illustrative), so $\min(F_c, \min_i H_{i,c}) = \min(\text{several weeks}, 5) = 5$ — **it is the practical-horizon constraint, not freshness, that actually bounds this example**, exactly the case the reviewer's correction was meant to capture. $D_{max} = 2$ km, and $d(g) = 1.4$ km (passes).

| $k$ (days) | $Q_{g}(k)$ (kg) | $C^{ind}_{total}(k)$ | $TC$ tier | $C^{collab}(k)$ | $NetSavings(k)$ |
|---:|---:|---:|---|---:|---:|
| 1 | 25 | ₹1,562.50 | Small, ₹1,150 (midpoint) | ₹1,000+₹1,150 = ₹2,150 | **−₹587.50** |
| 2 | 50 | ₹3,125.00 | Small, ₹1,150 | ₹2,000+₹1,150 = ₹3,150 | **−₹25.00** |
| 3 | 75 | ₹4,687.50 | Small, ₹1,150 | ₹3,000+₹1,150 = ₹4,150 | **+₹537.50** |
| 5 | 125 | ₹7,812.50 | Small, ₹1,150 | ₹5,000+₹1,150 = ₹6,150 | **+₹1,662.50** |

**Step 5 (procurement quantity constraint):** no trader-confirmed $MOQ_{\text{onion}}$ in this example, so this step is **skipped entirely** — it is not evaluated with a substitute value (Part 18's corrected treatment).
**Step 6 (economic feasibility):** $NetSavings_{g,c}(k) > 0$ directly rules out $k=1,2$ and keeps $k=3,5$. For explanation only, the break-even quantity is also computed: $BE = 1{,}150 / (62.5-40) = 51.1$ kg — note this falls between $k=2$'s 50 kg and $k=3$'s 75 kg, i.e., it marks exactly the same zero-crossing the $NetSavings$ column already shows, confirming Part 16's point that $BE_c(t)$ is a restatement of the economic threshold in kilograms, not a second, independent check.
**Step 7:** $k^* = 5$ (the largest feasible value within this example's $\min(F_c,H_g)=5$ bound; a full enumeration would also check whether crossing into the medium transport tier at a larger, hypothetical $k$ could still pay off, which does not arise here since $k$ is capped at 5).
**Decision:** $y_{g,\text{onion},t} = 1$, recommend a 5-day bundled order of 125 kg, estimated net savings ≈ ₹1,662.50, allocated quantity-proportionally (₹332.50 in savings per vendor, since demand is symmetric in this illustration).

This example demonstrates exactly the mechanism Part 15 described analytically: net savings rising with $k$ within a fixed transport tier, and a real possibility that small orders (here, $k=1,2$) are recommended *against* even though the price spread itself is favorable — because the fixed transport charge dominates at low volume. No claim is made that these specific numbers reflect real vendor behavior.

---

## 27. Model Assumptions

| Assumption | Why Needed | Risk | How It Will Be Tested/Limited |
|---|---|---|---|
| Vendors report a usable point estimate (or diary-derived mean) of daily consumption | Without it, $r_{i,c}$ has no value | Recall bias (Phase 1C, K1) | Diary subset cross-checks survey estimates; ranges preferred over false-precision figures |
| A single effective price per commodity per date is realistic (no supplier choice) | Matches the refined problem statement's partner-trader routing assumption | If real vendors access multiple, differently-priced channels, this understates variability | Stated explicitly as a V1 simplification (Part 5); trader interviews (Phase 1C, Part 7) can surface if this is unrealistic |
| A single collection point at the group centroid is operationally workable | Keeps the transport and geographic models simple (Parts 13, 17) | Real terrain/road access may not match straight-line centroid geometry | Haversine distance is already flagged (Phase 1C, C4) as an approximation, not routed distance |
| The vehicle-tier lookup approximates real transport pricing | No granular per-shipment quote data exists yet | Real quotes could fall outside the assumed bands | Priority primary-data item already flagged in Phase 1B (non-motorized/informal transport options) |
| Ambient freshness figures (tomato) are usable even though only trader-triangulated, not scientifically verified | Needed to make $F_c$ operable for the one short-shelf-life commodity in the set | Could be optimistic or pessimistic relative to true ambient spoilage | Sensitivity-tested across the H5 tiers (Phase 1D); trader interviews triangulate, don't certify (Phase 1C, C5) |
| Vendors can give a usable answer for their maximum practical buying interval $H_{i,c}$, or purchase frequency is an adequate proxy where they can't | Without it, $k$ would be bounded only by freshness, silently assuming every vendor can afford/store as much as the commodity allows to stay fresh (reviewer correction, Part 9) | A vague or overly cautious self-reported answer could under- or over-state real practical capacity | Added to the vendor survey instrument alongside the existing demand questions (Phase 1C, Section 6); cross-checked against purchase frequency where both are available |
| Participation/trust does not need to be modeled as a live constraint | No per-scenario data exists to grade it | Real-world adoption could differ sharply from what the model assumes | Treated only as an exogenous scenario parameter (Part 20), never presented as validated behavior |

---

## 28. Model Limitations

Explicitly **not** solved by this mathematical model:

- Multi-commodity joint transport bundling (deferred to preserve consistency with Phase 1D's fixed single-commodity experimental unit).
- Multi-stop, multi-vendor last-mile distribution beyond a single collection point.
- MOQ negotiation or dynamic trader pricing.
- Independent verification of vendors' self-reported practical procurement horizon $H_{i,c}$ — it is taken at face value (or from the purchase-frequency proxy) as primary/assumed data, not cross-checked against actual buying behavior over time.
- A fitted, validated probabilistic demand distribution (newsvendor in its full stochastic form); low/base/high scenario bounds (Part 12) are a substitute, not an equivalent.
- Vehicle routing / route optimization.
- A live, per-scenario operational-feasibility (participation/trust) check.
- Payment execution, settlement, or dispute handling (Phase 1B's payment *models* are referenced as context for who acts on a recommendation, Part 4 — this document does not model money movement).
- Automatic order placement of any kind (Part 4).
- Real-time or sub-daily re-evaluation (the model is explicitly a once-per-day batch computation, matching Agmarknet's daily price granularity).
- Candidate-group generation itself (Stage 1, Phase 2B).

---

## 29. Computational Problem Characteristics

*(Preparation for Phase 2B — no algorithm is named or implied here, per Rule 2.)*

| Problem Characteristic | Present? | Explanation |
|---|---|---|
| Combinatorial subset selection | ✅ Yes — but only in Stage 1 (group formation), explicitly outside this document's scope |
| Binary decision variable | ✅ Yes — $y_{g,c,t}$ |
| Bounded small-integer decision variable | ✅ Yes — $k_{g,c,t}$, resolved by simple enumeration (Part 15), not search |
| Benefit maximization subject to hard constraints | ✅ Yes — Part 22 |
| Multiple simultaneous hard constraints | ✅ Yes — three unconditional (geographic, freshness/practical-horizon, economic) plus one conditional (procurement quantity, only where $MOQ_c$ is known), Part 21 |
| Multi-stage decision structure | ✅ Yes — Stage 1 (group formation) feeds Stage 2 (this model) |
| Real-valued objective with discrete jumps (vehicle tiers) | ✅ Yes — relevant to how Stage 1's candidate groups should be sized |
| Combinatorial explosion risk if handled naively | ✅ Yes — the reason Stage 1 cannot brute-force all subsets of $V$ at $n$ up to 20 |
| Multi-objective tradeoff | ❌ No — a single scalar (net rupee savings), by design (Part 15, Part 21) |
| Real-time/continuous re-optimization | ❌ No — daily batch cadence is sufficient (Part 28) |
| Learning/prediction component | ⚠️ Present, but external to this model — Layer 1's similarity estimation (Phase 1C) feeds $r_{i,c}$ upstream; it is not part of the optimization formulated here |

---

## 30. Exact V1 Scope

**INCLUDED IN V1**
- 10–20 real vendors, one city/locality (Phase 1C).
- Fixed commodity set: onion, potato (primary), tomato (freshness stress-test); cooking oil excluded (Phase 1B, Section 4).
- Daily re-evaluation against the latest available Agmarknet price.
- Single collection point per group, at the group centroid.
- A two-tier flat-rate transport-cost lookup.
- Three unconditional hard feasibility constraints (geographic, freshness/practical-horizon, economic) plus one conditional constraint (procurement quantity, applied only where a real $MOQ_c$ exists) — Parts 16–19, zero soft constraints.
- Explicit low/base/high demand scenarios in place of either a fixed haircut or a fitted probability distribution.
- Quantity-proportional cost allocation.
- One commodity evaluated per scenario (Phase 1D's fixed experimental unit).
- A bounded order-horizon decision, $k \le \min(F_c, H_{i,c})$, evaluated by direct enumeration.

**EXCLUDED FROM V1 (why)**
- Multi-commodity bundled transport — would contradict Phase 1D's already-approved single-commodity experimental unit; revisit only if that unit definition is itself revisited.
- MOQ negotiation / variable trader pricing — no data exists; would require invented numbers (Rule 1).
- A separate, independently-verified value for $H_{i,c}$ beyond self-report/purchase-frequency — no data collection mechanism for it beyond the survey exists in the current field-study design.
- Full stochastic newsvendor modeling — insufficient diary data volume to fit and validate a distribution (Phase 1C, Section 9).
- Vehicle routing / multi-stop logistics — disproportionate to a mini-project timeframe and to the single-collection-point design (Rule 4).
- Soft/weighted constraint scoring — would require vendor preference data that does not exist; echoes the earlier, already-made decision to drop the composite "viability score."
- Real-time or sub-daily re-optimization — no real-time price or demand feed exists to act on.
- Automatic order execution — contradicts the decision-support design principle (Phase 1D, Part 14).
- Candidate-group generation mechanism — reserved for Phase 2B.

---

## 31. Model Quality Audit

1. **Is every variable measurable?** Yes for the two true decision variables ($y$, $k$); all derived quantities ($Q$, costs, savings) compute directly from measurable parameters.
2. **Is every parameter obtainable?** Mostly. $MOQ_c$ is conditional and, per the reviewer's correction, **has no substitute value** when unobtainable — the constraint is simply not applied for that commodity (Part 18), rather than being propped up with a derived proxy. $H_{i,c}$ is obtainable either directly (vendor-declared) or via the purchase-frequency fallback (Part 7); if genuinely neither is answerable for a given vendor, that vendor's practical-horizon bound is undefined and should exclude them from horizon optimization for that commodity rather than default to an invented number.
3. **Are any parameters unsupported?** $D_{max}$, $m$, tomato's ambient $F_c$, the vehicle-tier weight cutoffs, and $H_{i,c}$ where derived from purchase frequency rather than directly declared, remain 🟡 assumptions — flagged, not hidden, and each is already slated for sensitivity testing (Phase 1D) or primary confirmation (Phase 1C's remaining timeline).
4. **Does the model depend on data we do not have yet?** Yes, by design — this is a pre-registration of the model's structure ahead of the Phase 1C data-collection timeline (Weeks 1–6), which is good research practice (specifying the model before seeing the data avoids fitting the model to whatever the data happens to show).
5. **Are any constraints unnecessarily complicated?** No — every hard constraint reduces to a single inequality (freshness/practical-horizon to two inequalities sharing one $\min(\cdot)$ bound); the naive draft's pairwise-distance formulation and the earlier draft's conflation of MOQ with break-even quantity were the more complicated (and, in both cases, less correct) versions, both simplified here per direct correction.
6. **Is the objective measurable?** Yes — net rupee savings, computed from parameters already required elsewhere in the model.
7. **Can the model actually be implemented?** Yes — every computation is closed-form or a small bounded enumeration; nothing requires an unavailable solver or unbounded search.
8. **Is the V1 scope realistic?** Yes, per Part 30 and Rule 4 — no requirement exceeds what a 10–20 vendor, single-city mini-project can support.
9. **Does the model accidentally force ML?** No — the only estimation component (Layer 1 similarity reasoning for $r_{i,c}$) sits outside this model, correctly scoped per Phase 1C's three-layer architecture; everything defined in this document is constrained decision evaluation, not a trained model.
10. **Are real and simulated inputs clearly separated?** Yes — Part 8's classification table, plus the $y_{g,c,t}$/$k_{g,c,t}$ notation itself, keeps every parameter's evidence status explicit; nothing here blends a 🟢/🔵 figure with a 🟠 synthetic one without saying so.

No open issue found in this audit requires a structural change to the model as specified — the remaining open items (exact $D_{max}$, margin $m$, ambient $F_c$, vehicle-tier cutoffs) are data-collection and sensitivity-analysis tasks already scheduled in Phases 1C/1D, not modeling defects.

---

## 32. Final Mathematical Formulation

**Sets:** $V$ (vendors), $C = \{\text{onion, potato, tomato}\}$, $T$ (dates), $G_{c,t}$ (candidate groups, Stage-1 input).

**Parameters:** $r_{i,c}$ (base; $r^{low}_{i,c}, r^{high}_{i,c}$ for scenario analysis), $p^{ind}_{i,c}$, $p^{wh}_{c,t}$, $p^{eff}_{c,t} = p^{wh}_{c,t}(1+m)$, $L_i$, $D_{max}$, $F_c$, $H_{i,c}$, $TC(\text{tier})$, $MOQ_c$ (conditional) — each labeled per Part 8. ($\alpha_c$, the demand haircut in an earlier version of this document, has been removed per reviewer correction — see Part 12.)

**Decision Variables:** $y_{g,c,t} \in \{0,1\}$, $k_{g,c,t} \in \{1,...,\lfloor \min(F_c, \min_{i\in g}H_{i,c}) \rfloor\}$.

**Derived quantities:**
$$Q_{g,c}(k) = k\sum_{i \in g} r_{i,c}, \quad d(g) = \max_{i\in g}\text{Haversine}(L_i,\text{centroid}(g))$$
$$C^{ind}_{total,g}(k) = k\sum_{i\in g} r_{i,c}\, p^{ind}_{i,c}, \quad C^{collab}_{g,c}(k) = Q_{g,c}(k)\,p^{eff}_{c,t} + TC(\text{tier}(Q_{g,c}(k)))$$
$$NetSavings_{g,c}(k) = C^{ind}_{total,g}(k) - C^{collab}_{g,c}(k), \quad BE_c(t) = \frac{TC(\text{small tier})}{p^{ind}_{i,c} - p^{eff}_{c,t}} \text{ (explanatory only, Part 16)}$$

**Feasibility conditions (corrected structure, per Part 21):**
1. Procurement quantity (hard, **conditional**): $Q_{g,c}(k) \ge MOQ_c$ — applied only if a trader-confirmed $MOQ_c$ exists; no constraint otherwise (Part 18)
2. Geographic (hard): $d(g) \le D_{max}$
3. Freshness & practical procurement horizon (hard): $k \le \min(F_c, \min_{i\in g}H_{i,c})$
4. Economic (hard): $NetSavings_{g,c}(k) > 0$; $BE_c(t)$ reported alongside for explanation, not as a further gate
- Operational: not modeled as a per-scenario constraint (Part 20)

**Objective:** $\max_{k} NetSavings_{g,c}(k)$ subject to the above, evaluated by direct enumeration over $k \in \{1,...,\lfloor\min(F_c,\min_{i\in g}H_{i,c})\rfloor\}$.

**Hard constraints:** three unconditional plus one conditional, as listed above. **Soft constraints:** none (Part 21).

**Final decision rule:** Part 23's 8-step sequence.

**Inputs:** Part 24. **Outputs:** Part 24.

---

## 33. Final Verdict

**🟢 MODEL APPROVED → PROCEED TO PHASE 2B.**

This model is deliberately minimal: two real decision variables, a small hard-constraint set (three unconditional, one conditional), one scalar objective, no invented constants, no forced ML, and no algorithm selection. Its central contribution over the naive draft is recognizing that the project's one genuinely hard computational problem — which vendors should be grouped together — is not the same problem as evaluating a group once proposed, and keeping those two problems formally separate rather than blending them into one underspecified formulation.

**This version incorporates a reviewer pass with three corrections, all applied throughout the document, not just at their original location:** (1) the order horizon is now bounded by both freshness $F_c$ and a new vendor-side practical procurement horizon $H_{i,c}$, since a commodity staying fresh does not mean a small vendor can practically buy that far ahead; (2) the demand "haircut" $\alpha_c$ has been removed from the core model and replaced with explicit low/base/high demand scenarios, since a specific percentage haircut had no data-grounded justification even though it was honestly labeled as an assumption; (3) minimum order quantity and the Phase 1B break-even quantity are no longer merged into one "demand feasibility" constraint — $MOQ_c$ is now applied only where a real, trader-confirmed value exists, and the break-even quantity is retained purely as an explanatory figure attached to economic feasibility, since it was otherwise duplicating that same check under a different name.

**What Phase 2B inherits from this document:** the cost/feasibility evaluation function (Part 32) that any candidate-group-generation method must be scored against, the confirmed absence of a real, ever-present MOQ (so Phase 2B's algorithm cannot assume one), the confirmed small, enumerable nature of the order-horizon sub-problem — now bounded by two independent factors rather than one — (so Phase 2B's algorithmic effort should concentrate entirely on Stage 1, group formation), and the problem-characteristics table (Part 29) as its starting point for algorithm-family screening.

**What remains open, not as a modeling defect but as a data-collection dependency already scheduled:** confirming $D_{max}$, the trader margin $m$, ambient $F_c$ for tomato, vendors' practical procurement horizon $H_{i,c}$, and the vehicle-tier cutoffs against real primary data collected per the Phase 1C timeline, and running the sensitivity analysis already planned in Phase 1D across these same parameters once real scenario data exists.
