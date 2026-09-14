# 📂 RESEARCH AUDIT FILE — PHASE 1D
### Research Methodology & Experimental Design
**Subject:** An AI-Assisted, Freshness- and Logistics-Aware Collaborative Procurement Decision Framework for Street Vendors
**Question this phase answers:** Can this project be evaluated in a scientifically credible way with the available data, real-world constraints, and proposed experimental framework?

**Data labeling used throughout:** 🟢 REAL PUBLIC DATA · 🔵 REAL PRIMARY DATA · 🟠 SIMULATED/CALIBRATED DATA · 🟡 EXPERIMENTAL ASSUMPTION

---

## 1. Executive Summary

**Verdict: 🟡 APPROVED WITH REQUIRED MODIFICATIONS.**

The methodology sketched across Phases 1A–1C can support a credible evaluation, but three specific corrections are required before it does. First, the four hypotheses drafted in the prompt (H1–H4) must not be tested as formal statistical hypotheses — a 10–20 vendor convenience sample cannot support significance testing or any generalization claim, and treating it as if it could would be exactly the "fake statistical significance" this audit was told to avoid. They are reframed below as **experimental propositions**, evaluated by direct scenario computation rather than p-values. Second, the largest simulated scenario tier (50–100 vendors) and the computational-performance metrics are not necessary to answer any of this project's actual research questions — they are dropped from the core evaluation to avoid scale being added purely for appearance. Third, "accuracy" is explicitly excluded as a metric anywhere no ground truth exists (per the project's own Rule 7); decision quality is instead measured through constraint satisfaction and net savings, which do not require a labeled ground truth to be meaningful.

With those corrections, the recommended research design is **Design Science Research (Hevner et al.'s IS research paradigm — build and rigorously evaluate a purposeful artifact addressing a real problem) as the overarching frame, with an embedded exploratory case study using real vendor and market data, and simulation-based scenario evaluation to compensate for the small real sample.** This combination is explicitly sanctioned within the Design Science Research literature itself, which calls for artifact evaluation via multiple methods (case study, simulation, experimentation) rather than any single one alone — so this is not an improvised hybrid, it is a named and defensible methodological choice.

**Direct answer to the governing question: yes**, this project can be evaluated credibly, provided the corrections above are adopted and the research is framed throughout as an exploratory, scenario-based evaluation of a decision-support artifact — never as a statistically representative study, a validated forecasting model, or a system with guaranteed real-world outcomes.

---

## 2. Primary Research Objective

**Rejected as too vague (per the prompt's own caution):** "To develop an AI system for street vendors."

**Recommended objective:**

> *"To design and evaluate, through an exploratory field study and calibrated scenario simulation, whether a constraint-aware collaborative procurement decision framework — one that checks price advantage, transportation cost, minimum viable quantity, and commodity freshness before recommending a group purchase — produces measurably better procurement-cost and feasibility outcomes than individual procurement and simpler (geography-only or demand-only) grouping strategies, for the specific street vendors, commodities, and city context studied."*

This is measurable (net savings, feasibility rate — defined in Part F), bounded to what the available data can actually support (explicitly scoped to "the specific vendors, commodities, and city context studied," not a general population claim), and does not overreach into forecasting-accuracy or national-scale claims that Phases 1B/1C already ruled out.

---

## 3. Research Questions

**Primary Research Question:**

> Under what price, transport-cost, group-size, and freshness conditions does a constraint-aware collaborative procurement decision framework produce positive net savings relative to individual procurement, for the vendors and commodities studied?

| Research Question | Importance | Required Data | Evaluation Method |
|---|---|---|---|
| **RQ1 (Primary, above)** | This is the whole point of the project — Phase 1B already showed the answer is conditional, not universal; RQ1 formalizes exactly what "conditional" means | Real wholesale/retail prices (🟢), real transport-cost benchmarks (🟢), primary vendor demand/location data (🔵), calibrated scenario grid (🟠) | Compute net savings for each scenario in the Part G/H grid; report the sub-conditions (price spread, transport cost, group size) under which the sign flips positive |
| RQ2 — How sensitive is net savings to transportation cost specifically? | Phase 1B's preliminary break-even calculations suggested transport cost has a large effect on outcomes — this deserves its own dedicated question, not just a sub-point of RQ1. Whether it turns out to matter more than price spread is left open and answered empirically under P3, not assumed here | Same as RQ1, varying transport cost only | One-variable-at-a-time sensitivity analysis (Part I) |
| RQ3 — Does combining geographic and demand-aware grouping outperform geography-only grouping? | Directly tests whether the "intelligence" in the system (vs. a naive clustering app) adds real value — the core novelty claim from Phase 1A | Same base data, run through Baseline 2 vs. Baseline 3 vs. Proposed Method (Part E) | Compare net savings and feasibility rate across the three methods on identical scenarios (Part L's fair-comparison rules) |
| RQ4 — To what extent do freshness constraints reduce the set of economically viable procurement options, and for which commodities does this bind hardest? | Phase 1B found this binds hard for tomato and not at all for onion/potato — RQ4 turns that finding into a formal, repeatable test | Commodity-specific shelf-life data (🟢 refrigerated / 🟡 ambient assumption), demand scenarios (🟡/🟠) | Compare the proposed method's accepted-order set with and without the freshness constraint enabled, per commodity |
| RQ5 — What is the minimum group size/aggregate quantity at which collaborative procurement becomes viable, and how does this vary by commodity? | This is the practical, actionable number a vendor-facing recommendation needs — and Phase 1B already computed a first estimate (35–70 kg) that this question re-derives more rigorously across the full scenario grid | Same as RQ1 | Break-even calculation (Part I) repeated across the scenario grid, not just the single base case Phase 1B used |

All five questions are answerable with the data established in Phases 1B/1C, require no statistical inference beyond direct computation, and stay within the bounds of the sampled vendors/commodities/city — none require national-scale generalization, a large ML training set, or a longitudinal behavioral study.

---

## 4. Research Hypotheses or Experimental Propositions

**Determination: formal statistical hypothesis testing is not appropriate here**, and adopting it would violate the project's own Rule 3. A 10–20 vendor convenience sample, collected non-randomly from a single city, cannot support a defensible null-hypothesis-significance-test framework — there is no sampling distribution to speak of, and any p-value computed on it would be a decoration, not evidence. The correct, established alternative for a design-science artifact evaluation of this kind is **experimental propositions**: falsifiable statements evaluated by direct computation across a defined scenario set, not by inferential statistics.

**P1** *(replaces H1)*: Under the price, transport, and group-size conditions established in Phase 1B (roughly 35–70 kg break-even, ₹800–1,500 local transport), the constraint-aware framework produces positive net savings for at least the long-shelf-life commodities (onion, potato) across a majority of the tested medium/high price-spread scenarios.
*Testable?* Yes — direct computation, no inference required. *Evaluated by:* the scenario grid in Part G/H.

**P2** *(replaces H2)*: Combined geographic-and-demand-aware grouping achieves a higher constraint-satisfaction and economic-feasibility rate than geography-only grouping across identical scenarios.

> **Feasibility Rate** = Number of groups satisfying all constraints ⁄ Total candidate groups evaluated

This replaces the earlier "correctly identified" wording, which implied a ground-truth label for what the "correct" group is — no such label exists (Rule 7). Feasibility Rate is instead a directly computable fraction: of all candidate groups the two methods generate across the scenario grid, what share pass every stated constraint (price, transport, freshness, MOQ where known)? No judgment of "correctness" against an external standard is required or implied.
*Testable?* Yes. *Evaluated by:* direct comparison across identical scenarios (Part E/L), using the Feasibility Rate formula above — the same metric reported as F3 in Part 8.

**P3** *(replaces H3)*: Net savings are sensitive to changes in transportation cost and price advantage, with the relative influence of these factors quantified through sensitivity analysis.
*Testable?* Yes — this is directly what the sensitivity analysis (Part I) measures. The design deliberately does not presuppose which of the two factors matters more: both transport cost and price spread are varied under the OFAT design in Part I, and their relative influence on net savings and Feasibility Rate is reported as an empirical result, not assumed in advance. (Phase 1B's preliminary break-even calculations hinted that transport cost has a large effect, but that was a single-scenario observation, not a controlled sensitivity comparison — this proposition is what lets the full scenario grid confirm or overturn that hint.)

**P4** *(replaces H4)*: Enabling the freshness constraint measurably shrinks the set of orders the system will recommend for tomato, but has negligible effect for onion and potato.
*Testable?* Yes — directly reproduces and formalizes Phase 1B Section 12's finding.

**Why propositions, not hypotheses:** each is evaluated by computing an outcome across a defined, documented scenario set and reporting whether the pattern holds — a deterministic, reproducible check, not a claim about a population. This is the correct framing for a small-sample design-science evaluation and should be stated explicitly in the paper's methodology section to preempt a reviewer asking why no significance tests are reported.

---

## 5. Recommended Research Design

| Approach | Fit for this project |
|---|---|
| Exploratory case study alone | Good for grounding RQ1–RQ5 in real data, but on its own cannot cover the sensitivity analysis (Part I) or the scenario breadth (Part G) needed — 10–20 real vendors is too thin a base for that alone |
| Design Science Research (DSR) alone | Correct overarching paradigm — the project is literally building and evaluating a purposeful IT artifact (a decision framework) to address a real, evidenced problem — but DSR is a frame, not a complete evaluation plan by itself; it needs an evaluation method nested inside it |
| Simulation-based evaluation alone | Necessary for scenario/sensitivity breadth, but alone risks becoming disconnected from real vendor behavior if not calibrated against Phase 1C's real data |
| Prototype evaluation alone | Necessary to confirm the built system behaves correctly (constraint satisfaction, no illegal outputs), but says nothing about whether the underlying economics are realistic |
| **Hybrid: DSR (frame) + embedded exploratory case study (real data) + simulation-based scenario evaluation (breadth) + prototype/logical validation (correctness)** | **Recommended.** This is not an ad hoc combination — DSR's own evaluation guideline explicitly calls for multiple evaluation methods (case study, simulation, controlled experiment) applied to the artifact, so this hybrid is a textbook-correct instantiation of DSR, not an improvisation |

**Why this is the strongest fit:** it lets each data source do the job it's actually good for — the small real dataset grounds the project in truth and prevents disconnected simulation, the calibrated simulation supplies the scenario breadth and sensitivity analysis a 10–20 vendor sample cannot, and the prototype/logical validation confirms the artifact itself is correctly built, independent of whether the underlying economic assumptions turn out to be favorable.

---

## 6. Experimental Baselines

**Baseline 1 — Individual Procurement**

$$C_{individual} = \sum_{i=1}^{n} q_i \times p_i$$

*Inputs:* each vendor's own reported/observed quantity ($q_i$) and procurement price ($p_i$, per Phase 1C — vendor-reported, never substituted with PMS consumer retail price). *Assumption:* no explicit transport cost included (per Phase 1B's decision to treat individual transport as an unmodeled opportunity cost, not a cash cost). *Output:* total cost as if every vendor bought alone.

**Baseline 2 — Simple/Naive Group Procurement**

All vendors within a fixed geographic radius (🟡 1–2 km, per Phase 1C's reasoned starting point) are grouped **automatically**, with no check on price advantage, transport-cost viability, or freshness. This is the deliberately "dumb" baseline representing what a plain clustering app (with no decision intelligence) would do — it always executes the group order once the radius condition is met.

**Baseline 3 — Demand-Aware Grouping**

Vendors are grouped by geography **and** overlapping commodity need with roughly compatible quantities, but still without checking transport-cost viability or freshness feasibility — an intermediate baseline that adds demand-compatibility intelligence but stops short of full constraint-awareness. This isolates exactly how much of the proposed method's advantage (if any) comes from demand-matching alone, versus from the transport/freshness viability check.

**Proposed Method (conceptual scope only — no algorithm specified here, per this phase's restriction)**

Allowed to use: vendor demand, geographic distance, current market price (wholesale and vendor-reported procurement price), transport cost estimate, and commodity freshness window — the same underlying data available to the baselines, but additionally permitted to **decide not to form a group at all** when the constraints aren't met. This last point is the crux of the whole project's novelty (per Phase 1A) and must be preserved as the single defining difference in the comparison.

**Baseline Comparison Table**

| Method | Demand | Distance | Transport | Freshness | Price | Can decide "don't group" |
|---|---|---|---|---|---|---|
| Baseline 1 — Individual | ✓ (per-vendor) | — | — | — | ✓ (vendor's own price) | N/A (never groups) |
| Baseline 2 — Naive geographic | — | ✓ | — | — | — | ✗ (always groups if radius met) |
| Baseline 3 — Demand-aware | ✓ | ✓ | — | — | — | ✗ (always groups if demand+radius met) |
| Proposed Method | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

This table is designed so that each baseline adds exactly one more piece of information than the last, isolating which component of "intelligence" actually drives any measured improvement — a fair, incremental comparison rather than an all-or-nothing one.

---

## 7. Proposed Method Evaluation Scope

Per this phase's explicit restriction, the proposed method is defined here only by **what information it is allowed to use**, not by its internal algorithm:

- Vendor demand (real 🔵 where available, 🟠 simulated for scenario breadth)
- Geographic distance between vendors and to the procurement source (Haversine, per Phase 1C)
- Current wholesale price (🟢 Agmarknet) and vendor procurement price (🔵 primary)
- Transport cost estimate (🟢 real local benchmark, per Phase 1B)
- Commodity freshness window (🟢 refrigerated benchmark / 🟡 ambient assumption, per Phase 1C)
- The ability to output "do not form a group — recommend individual procurement" as a valid result, not just a group recommendation

No clustering algorithm, optimization solver, or ML model is named or committed to in this phase — that is explicitly deferred to a later design phase, per this project's own instruction.

---

## 8. Evaluation Metrics

**F1. Economic Metrics**

$$NetSavings = C_{baseline} - C_{proposed}$$
$$Savings\% = \frac{C_{baseline} - C_{proposed}}{C_{baseline}} \times 100$$

No modification needed to these formulas, with one clarification: $C_{baseline}$ must be explicitly stated per comparison (Baseline 1, 2, or 3) — reporting a single unlabeled "baseline" would obscure which comparison is being made.

**F2. Logistics Metrics:** transport cost per kg (derived, useful for cross-commodity comparison), total distance traveled per group order. *Average vendor-to-group-centroid distance* is kept because it is a direct input to the transport-cost model, not a decorative metric.

**F3. Grouping Metrics:** group size (vendor count), aggregate quantity, and — added here as the most meaningful of this category — **Feasibility Rate** = Number of groups satisfying all constraints ⁄ Total candidate groups evaluated (defined in Part 4, P2), which directly operationalizes RQ3's feasibility comparison. "Group utilization" (how close the aggregate quantity comes to an ideal batch size) is kept only as a secondary, descriptive statistic, not a primary metric.

**F4. Freshness Metrics:** percentage of recommended groups satisfying the freshness constraint (should be 100% by construction for the proposed method — this is a correctness check, not a research finding); quantity-at-risk avoided (the volume the naive baselines would have over-ordered relative to the freshness window); number of would-be-infeasible orders correctly declined.

**F5. Decision Quality Metrics:** percentage of proposed-method recommendations that are economically beneficial (net savings > 0) among all "proceed" recommendations; percentage of infeasible or spoilage-risking groups avoided compared with Baselines 2/3. **No "accuracy" metric is used**, per Rule 7 — there is no independent ground truth for "the correct decision" beyond the constraints the system itself is built to check, so these are framed as constraint-satisfaction and cost-outcome metrics, not classification accuracy.

**F6. Computational Metrics: not adopted as a primary metric for this mini-project.** Execution time and scalability are legitimate concerns for a production system, but none of RQ1–RQ5 requires them, and testing them meaningfully would require exactly the kind of large synthetic scale-up (Part G4, dropped below) this audit was told not to add just to look impressive. A simple, one-line sanity check ("the prototype completes evaluation of the tested scenario grid in a reasonable time") is acceptable as a footnote, not a reported research result.

| Metric | Formula/Definition | Why It Matters | Baseline Comparison |
|---|---|---|---|
| Net Savings | $C_{baseline}-C_{proposed}$ | Core economic outcome | vs. Baselines 1, 2, 3 separately |
| Savings % | $(C_{baseline}-C_{proposed})/C_{baseline}\times100$ | Normalizes across commodities of different price levels | Same |
| Transport cost/kg | $C_{transport}/Q$ | Cross-commodity, cross-scenario comparability | Proposed vs. Baseline 2/3 (Baseline 1 has none) |
| Group formation rate | % of scenarios producing a viable group | Directly tests RQ3 | Proposed vs. Baseline 2/3 |
| Freshness-safe rate | % of formed groups meeting the freshness constraint | Tests RQ4; should be 100% for the proposed method by construction, and reveals how often naive baselines would violate it | Proposed vs. Baseline 2/3 |
| Quantity-at-risk avoided | Volume Baselines 2/3 would over-order beyond the freshness window, that the proposed method avoids | Makes the freshness benefit concrete and commodity-specific | Proposed vs. Baseline 2/3 |
| Break-even quantity | $C_{transport}/SavingsPerUnit$ | Directly answers RQ5 | Computed once per scenario, not "compared" per se |

---

## 9. Experimental Scenarios

**G1 — Real vendor scenarios.** Using the actual 10–20 surveyed vendors, their real reported demand/location/procurement price, and date-matched real Agmarknet/PMS prices, form whatever real vendor clusters the geography and commodity overlap actually allow. This will likely yield only a small handful of genuine real-data comparison points (plausibly 2–5 clusters across 2–3 commodities) — **this must be presented explicitly as an illustrative demonstration, not a powered experiment**, consistent with Phase 1C's sample-size framing. Its value is showing the framework works end-to-end on real inputs, not producing a generalizable result.

**G2 — Simulated small cluster (5–10 vendors).** The primary quantitative testbed: vary distance, quantity, and price spread across the ranges established in Part 10 below, anchored to Phase 1B/1C's real data wherever possible.

**G3 — Simulated medium cluster (20–50 vendors).** Useful for checking whether grouping quality/stability holds up with a larger candidate pool than the real sample could ever provide — a legitimate secondary tier, not required for the primary research questions but adding useful robustness evidence at low additional cost.

**G4 — Simulated large cluster (50–100 vendors): not included in the core evaluation.** None of RQ1–RQ5 requires this scale, and Part G's own instruction warns explicitly against adding scale "simply to make the project look impressive." If time permits after the core evaluation is complete, a single large-scale run may be reported as a computational feasibility footnote (tying back to F6), but it is not part of the core experimental design and should not be advertised as a primary result.

---

## 10. Scenario Parameters

| Parameter | Low | Medium | High | Labeling |
|---|---|---|---|---|
| **H1. Transportation cost** | ₹800 | ₹1,200 | ₹2,000 | 🟢 Real measured range (Phase 1B local-trip benchmarks, ₹800–2,500; medium interpolated) |
| **H2. Price advantage** | ~36% (onion, as observed) | ~50% (interpolated) | ~65–68% (tomato/potato, as observed) | 🟢 Real measured (low/high) / 🟡 Interpolated (medium) — anchoring to actual observed commodity spreads rather than inventing round numbers |
| **H3. Vendor density** | 3–5 vendors within radius | 8–12 | 15–20+ | 🟡 Experimental assumption — no real density data exists (confirmed gap, Phase 1C); flag as the least-grounded parameter |
| **H4. Aggregate demand** | 2 kg/vendor/day | 5 kg/vendor/day | 8 kg/vendor/day | 🟡 Experimental assumption, carried forward unchanged from Phase 1C for cross-phase consistency |
| **H5. Freshness window** | 2–3 days (tomato, ambient) | 7–10 days (tomato, refrigerated benchmark) | Weeks+ (onion/potato) | 🟡 Short bound is an assumption / 🟢 Medium and Long bounds are literature-sourced (FAO/USDA ARS + general food-science consensus) |
| **H6. Vendor participation rate** | 50% | 75% | 100% | 🟡 Experimental assumption — no data exists on how many geographically-eligible vendors would actually opt in (ties to the unresolved trust/payment question from Phase 1A) |

**Which parameters genuinely matter most:** H1 (transport cost) and H2 (price advantage) are the two dominant economic levers, both partly grounded in real data. H3 (density) and H6 (participation) are structurally important — they determine whether a viable group can even be assembled — but are the least evidentially grounded, so any conclusion drawn primarily from varying them should be stated as more speculative than conclusions drawn from H1/H2. None of the six parameters is dropped, but they are not all equally trustworthy, and the write-up should say so.

---

## 11. Sensitivity Analysis

**One-variable-at-a-time (OFAT), holding all others at their Medium value:**
- **Transport cost** (₹800 → ₹1,200 → ₹2,000): effect on net savings and on Feasibility Rate (directly answers RQ2, and — together with the price-difference run below — is what P3 is evaluated against).
- **Price difference** (36% → 50% → 68%): effect on break-even quantity and net savings (the other half of P3's comparison).
- **Group size** (via H3's density tiers, translated into vendor count at a fixed H4 demand level): effect on transport-cost-sharing and total aggregate quantity.
- **Distance** (implicit in H3 and in the transport-cost model): effect on feasibility and effective transport cost.
- **Freshness window** (H5's tiers): effect on maximum safe procurement frequency and feasible order quantity, isolating tomato from onion/potato.

**Multi-variable analysis:** a single joint sensitivity run — **transport cost × group size**, chosen because Phase 1B's preliminary break-even calculation showed both moving the break-even point substantially in a single scenario — is recommended as an addition beyond pure OFAT, since it directly maps the break-even frontier as a small 3×3 grid rather than five separate one-dimensional slices, at negligible extra computational cost. Broader multi-variable (3+ parameter) analysis is not recommended for this mini-project — the interpretive payoff drops sharply relative to the added complexity, and OFAT plus one joint grid already answers RQ1–RQ5 adequately.

**Reporting P3:** the transport-cost and price-difference OFAT runs above will be reported side by side (e.g., percentage change in net savings/Feasibility Rate per unit change in each factor), so the write-up can state which factor showed the larger effect in the tested ranges as a finding, not a premise.

---

## 12. Experimental Procedure

| Step | Input | Process | Output |
|---|---|---|---|
| 1 | Survey/diary responses, trader interviews | Clean, anonymize, normalize units (per Phase 1C, Section 13) | Cleaned primary dataset (🔵) |
| 2 | Agmarknet/PMS raw pulls, date-matched to primary data collection window | Verify units, cross-check against a second date (per Phase 1B's aggregator-discrepancy caution) | Cleaned Market_Price table (🟢) |
| 3 | Cleaned primary + market data | Compute real-data individual and naive-baseline costs for the small set of real vendor clusters (G1) | Real-data illustrative results |
| 4 | Cleaned data + Part 10 scenario parameters | Generate the calibrated synthetic scenario grid (G2/G3), documenting every generation rule (per Phase 1C, Section 12) | Labeled synthetic scenario set (🟠), reproducible via a documented seed |
| 5 | Real + synthetic scenarios | Run Baseline 1 (individual) on every scenario | Baseline 1 cost table |
| 6 | Same scenarios | Run Baseline 2 (naive geographic) | Baseline 2 cost/feasibility table |
| 7 | Same scenarios | Run Baseline 3 (demand-aware) | Baseline 3 cost/feasibility table |
| 8 | Same scenarios | Run the Proposed Method (conceptual scope per Part 7) | Proposed-method cost/feasibility table |
| 9 | All four result tables | Compute Part 8's metrics for every method/scenario pair | Consolidated metrics table |
| 10 | Consolidated metrics | Run the Part 11 sensitivity analysis (OFAT + joint grid) | Sensitivity results and break-even curves |
| 11 | All results | Run the Part 13 validation checks (constraint satisfaction, cost-calculation spot checks, leave-one-out plausibility check on demand estimates) | Validation report |
| 12 | Everything above | Interpret findings against the Part 16 threats to validity; write up strictly within the Part 19 claim boundaries | Final results and discussion |

This improves on the original 10-step skeleton by explicitly separating real-data illustration (Steps 1–3) from synthetic scenario construction (Step 4), by running all three baselines *and* the proposed method through an identical pipeline (Steps 5–8, satisfying Part 14's fair-comparison requirement structurally rather than as an afterthought), and by inserting an explicit validation step (11) before interpretation rather than treating validation as an implicit part of "analyze results."

---

## 13. Validation Strategy

**Determination: no train/test split or cross-validation is appropriate**, because no supervised ML model is being trained (confirmed in Phase 1C) — applying that vocabulary here would misrepresent what is actually being evaluated.

| Component | What Is Validated? | Validation Method |
|---|---|---|
| Demand estimation (similarity/category-based) | Whether the estimate is a reasonable approximation of real observed demand | Leave-one-vendor-out plausibility check: estimate each surveyed vendor's demand from the *other* vendors in its category, compare to that vendor's actual reported/diary demand — not a formal ML validation, but a legitimate, cheap, honest sanity check at this sample size |
| Grouping/optimization decisions | Whether the framework correctly accepts feasible groups and rejects infeasible ones | Scenario testing / logical constraint validation: construct a small set of hand-designed edge cases (e.g., a group that clearly should fail on freshness, one that clearly should fail on transport cost) and confirm the framework decides correctly on each |
| Cost calculations | Arithmetic and formula correctness | Manual back-of-envelope recomputation of a sample of cases, cross-checked against Phase 1B's original hand calculations |
| Optimization outputs | Whether every accepted group actually satisfies all stated constraints, and whether better feasible groupings exist that were missed | Constraint-satisfaction audit (every accepted output re-checked against all constraints) plus, where group sizes are small enough (≤15–20 candidate vendors), a brute-force/exhaustive comparison — computationally trivial at this scale, and a rigor uniquely available *because* the real sample is small |
| Trader/practical assumptions (MOQ, effective wholesale price, ambient shelf life) | Whether assumptions match real-world practice | Expert/practical validation via the Phase 1C trader interviews (Section 7) |

---

## 14. Fair Comparison Requirements

All methods compared within a single experimental run (Steps 5–8 above) must use: the same vendor set, the same demand figures, the same market-price date/snapshot, the same commodity, and the same transport-cost assumption. The **only** permitted difference between methods is the information and decision logic defined in Part 6's comparison table (e.g., Baseline 2 is not allowed to see price data; the Proposed Method is not allowed to see a more favorable price snapshot than the baselines see in the same run).

**Why this matters:** if, for example, the proposed method were evaluated using a same-day price pull while a baseline were evaluated using a stale price from a different date, any measured improvement could trivially reflect that data mismatch rather than genuine framework superiority — a classic and easily-overlooked source of an inflated, non-reproducible result. Fixing this rule at the experimental-design stage (rather than trying to catch it during analysis) is the reliable way to prevent it.

---

## 15. Reproducibility Plan

Practical checklist — record, for every experimental run:

1. Market data pull date and exact query parameters (commodity, market, date range) used against the Agmarknet API and Price Monitoring System.
2. Primary data collection window (survey dates, diary date range).
3. The exact scenario parameter table used (Part 10), including which tier — Low/Medium/High — was used in each run.
4. Random seed for any synthetic data generation (per Phase 1C's reproducibility rule).
5. The version/snapshot of the cleaned dataset used (a simple version tag or date stamp is sufficient — no formal data-versioning tooling is needed at this scale).
6. Which baseline/method combination produced each reported result.
7. Any manual assumption applied during cleaning (e.g., a unit-conversion rule used for a vendor who reported "one basket").
8. The exact formulas used for every metric (Part 8), including which $C_{baseline}$ was used in each reported Net Savings/Savings% figure.

This is deliberately a short, practical list — not a formal data-management plan — appropriate to a mini-project's scale and timeline.

---

## 16. Threats to Validity

*(Using the standard four-category framework from empirical software/IS research — internal, external, construct, and conclusion validity.)*

| Threat | Category | Risk | Mitigation |
|---|---|---|---|
| Wholesale price used is the raw mandi average, not an adjusted trader-margin price (Phase 1B caution) | Internal | Measured savings may be systematically overstated | Report a trader-margin-adjusted sensitivity variant (e.g., +10–15%) alongside the base-case figures |
| 10–20 vendors, single city, single season | External | Results cannot be generalized beyond the sampled context | State this explicitly and repeatedly in the write-up; use the Part 2 objective's bounded language, never broader claims |
| "Net savings" may not capture the full construct of "procurement benefit" (ignores vendor time cost, risk aversion, trust cost) | Construct | The metric could be precise but not fully meaningful | Explicitly list these unmeasured dimensions as limitations, not hidden gaps |
| Small N means an observed pattern could reflect the specific sampled vendors/commodities rather than a general effect | Conclusion | Overclaiming a pattern as reliable when it may be sample-specific | Use experimental propositions (Part 4), not hypothesis-testing language; state conclusions as scenario-conditional |
| Secondary price aggregator inconsistency (Phase 1B's 2–3× discrepancy finding) | Internal | Any figure sourced from an aggregator rather than the primary API could be simply wrong | Use only the primary Agmarknet API/PMS report for any number that appears in the final paper; aggregator sites are for early scoping only |
| Ambient shelf-life figures are extrapolated, not directly verified (Phase 1C gap) | Construct/Internal | The freshness constraint could be systematically mis-calibrated | Cross-check against trader interviews (Part 7); report the freshness analysis as conditional on this assumption |

---

## 17. Ethical and Practical Validation

**Determination: the V1 system must be decision-support only, never automated procurement.** Reasoning:

- Real financial risk falls on economically vulnerable vendors (Phase 1A: thin margins, some already credit-dependent) — an automated system that commits vendors to a purchase carries real downside if wrong.
- Meaningful uncertainty exists in every input this phase relies on: demand estimates (Section 13), the ambient freshness assumption (Part 16), and the effective wholesale-access price (Phase 1B) — none of these are precise enough to justify fully automated commitment of vendors' money.
- The payment/trust mechanism remains unresolved at the platform-design level (Phase 1A/1B) — automating procurement before that is solved would compound an already-identified risk.
- No legal/regulatory review of a platform holding or committing vendor funds has been conducted — well outside this project's scope, and a hard blocker to any automated-transaction design regardless of the technical merits.

**Recommended design principle:** every system output is a **recommendation with disclosed reasoning and uncertainty** ("recommended: buy X kg of onion with these vendors today, estimated savings ₹Y, based on Z-day-old price data and an assumed demand range") — never a silent or automatic action. If a recommendation turns out wrong (e.g., the price moved after the recommendation was made), the already-established daily re-evaluation design limits how long any single bad recommendation persists, but this must be disclosed as a real, non-zero possibility in the paper's limitations, not implied away.

---

## 18. Research Success Criteria

**Technical success:** all hard constraints (transport-cost-vs-savings, freshness window, MOQ where known) are correctly enforced in 100% of tested scenarios — a deterministic correctness bar, not a statistical one. No optimization output ever violates a stated constraint.

**Economic success:** positive net savings are demonstrated in at least one real vendor cluster (G1) and in a majority of the Medium/High price-spread synthetic scenarios (G2) for onion and potato specifically — a concrete, falsifiable bar consistent with what Phase 1B's preliminary numbers already suggest is achievable, not an inflated target.

**Research success:** the Proposed Method outperforms Baseline 2 (naive geographic grouping) on net savings and/or feasibility rate across the tested scenario grid, and Part 4's propositions (P1–P4) are evaluated and reported regardless of whether they are supported or not.

**Practical success (optional stretch, time permitting):** a plain-language rendering of a sample recommendation is understandable to a subset of the originally surveyed vendors without requiring them to understand the underlying calculation — tested informally, not as a core requirement of the mini-project.

The project is explicitly **not** considered successful merely because a website or prototype runs — success is defined entirely in terms of the criteria above.

---

## 19. Unsupported Claims to Avoid

- "No procurement platform exists for street vendors" — corrected in Phase 1A; existing B2B/agri platforms and analogues (Kampala, Pinduoduo) must be acknowledged.
- "The AI accurately predicts vendor demand" — no ground truth and no trained model exists to support an accuracy claim (Phase 1C).
- "Bulk buying always saves money" — directly contradicted by Phase 1B's own findings.
- "Mandi price is the exact price available to every vendor" — Phase 1B's trader-margin caution applies.
- "Consumer retail price equals street-vendor procurement price" — repeatedly flagged across Phases 1B and 1C as a distinct, unverified equivalence.
- "The system guarantees profit" — no system built on estimates and assumptions can guarantee an outcome.
- "This is validated for all Indian street vendors" / any claim of national representativeness — sample size and sampling method rule this out (Phase 1C).
- Any reported result described as "statistically significant" — no inferential statistical testing is justified at this sample size (Part 4).
- "The system uses deep learning / LSTM / Prophet" — none of these are used or justified by the available data (Phase 1C); do not claim methods that were not actually applied.
- Any specific ambient shelf-life figure presented as a verified fact rather than a stated, sourced assumption (Phase 1C gap).
- "Vendors want/trust this system," based only on the neutral survey questions — small-N, social-desirability-bias-prone responses (Phase 1C, K6) support only a cautious, qualitative statement, not a confident adoption claim.

---

## 20. Final Research Methodology

**Research Type:** Design Science Research, with an embedded exploratory case study (real data) and simulation-based scenario evaluation as the nested evaluation methods, plus prototype/logical validation for artifact correctness. Not a randomized controlled trial, not a purely qualitative case study, and not a conventional ML study.

**Data Sources:**
- 🟢 Public real data: Agmarknet wholesale prices, Price Monitoring System retail prices, FAO/USDA ARS shelf-life benchmarks, published local transport-rate ranges.
- 🔵 Primary field data: vendor survey and diary responses, trader/wholesaler interviews.
- 🟠 Simulated/calibrated data: the Part 9/10 scenario grid, generated under Phase 1C's synthetic-data rules and this phase's fair-comparison rules.

**Experimental Unit:** a **commodity–vendor-cluster–date scenario** — i.e., one specific commodity, one specific candidate group of vendors, evaluated against one specific market-price snapshot. This is the correct unit of analysis (not "the vendor" alone, and not an abstract system-level claim), and should be stated explicitly in the paper's methods section since it clarifies exactly what each row of every results table represents.

**Baselines:** Individual Procurement; Naive Geographic Grouping; Demand-Aware Grouping (Part 6).

**Proposed Method:** described only by its permitted information scope (Part 7) — algorithm design is explicitly out of scope for this phase.

**Evaluation Metrics:** Net Savings, Savings %, transport cost/kg, Feasibility Rate, freshness-safe rate, quantity-at-risk avoided, break-even quantity (Part 8). No accuracy metric.

**Sensitivity Analysis:** OFAT across transport cost, price spread, group size/density, distance, and freshness window, plus one joint transport-cost × group-size grid (Part 11).

**Validation:** leave-one-out plausibility check (demand estimation), scenario/logical constraint testing (grouping decisions), manual recomputation (cost calculations), constraint-satisfaction + small-scale exhaustive check (optimization outputs), trader-interview cross-check (practical assumptions) — Part 13.

**Limitations:** small, non-random, single-city sample; unverified ambient shelf-life assumption; wholesale price used may overstate real vendor-accessible savings; net savings does not capture time, risk, or trust costs; no automated-procurement claim is made or tested (Part 17).

---

## 21. Final Verdict

**🟡 APPROVED WITH REQUIRED MODIFICATIONS.**

The three required corrections — reframing hypotheses as experimental propositions (Part 4), dropping the large-scale (50–100 vendor) simulation tier and computational-performance metrics from the core evaluation (Parts 8/9), and excluding any "accuracy" metric in favor of constraint-satisfaction and cost-outcome metrics (Part 8) — are all now incorporated into the methodology above. With these in place, the methodology is scientifically defensible for a mini-project and a credible early-stage research paper: it has a precise, bounded objective; answerable, appropriately-scoped research questions; fair, incremental baselines; metrics that don't require evidence the project doesn't have; a validation plan matched to what is actually being built (not a borrowed ML validation vocabulary); and an explicit, honest list of what the project must never claim.

**Direct answer to the governing question:** *Yes, this project can be evaluated in a scientifically credible way with the available data and constraints* — as an exploratory, design-science evaluation of a decision-support artifact, using real government market data and a small real vendor sample to ground a calibrated scenario simulation, with every claim scoped to exactly what that combination can support. The path forward is to build the prototype and run the Part 12 procedure exactly as specified, not to expand the ambition of the evaluation beyond what this phase has just approved.
