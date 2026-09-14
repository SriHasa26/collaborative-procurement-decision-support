# Phase 5E — Final Group Formation and Optimization Design

**Date:** 2026-09-14
**Scope:** Formalize how Stage 1 (group formation, Phase 2B) connects to Stage 2 (feasibility/decision evaluation, Phase 5D), filling exactly the gaps `reports/phase5e_phase2b_reconciliation.md` identified — a Stage 1 eligibility filter, an explicit `WAIT_OR_EXPAND_GROUP` mechanism, and an explicit `ABSTAIN` path — without redesigning anything that audit found valid. No frontend/backend is built. No model is trained. No dataset is modified. The Potato forecasting experiment is not reopened.

---

## 1. Phase 2B Audit (Summary)

Full detail in `reports/phase5e_phase2b_reconciliation.md`. **No component of Phase 2B was found to contain a real logical conflict.** Preserved unchanged: the graph-based candidate generation (compatibility graph → connected components → within-pool subset enumeration), the exact $2D_{max}$ geographic pruning result, the retraction of any economic pre-filter, the lexicographic objective (total net savings, vendor-coverage tie-break), the overlap-resolution rule (exact weighted set packing at final selection only), and the honest complexity/scalability analysis. The only gaps are things Phase 2B never had occasion to address — a missing-data eligibility check and a formal expansion mechanism — because Phase 5D's four-state model didn't exist yet. Sections 4, 12, and 13 below fill exactly those gaps.

## 2. Vendor Universe

$$V = \{v_1, v_2, \dots, v_n\}$$

For group formation specifically, only the following attributes are used — no personal or unnecessary vendor information is added:

| Field | Meaning | Evidence status |
|---|---|---|
| `vendor_id` | Anonymous identifier | Real (assigned at collection) |
| `commodity_requirement` (which $c$, and $q_i$ for it) | What and how much this vendor is estimated to need | User-provided (survey/diary) or **Estimated** (cold-start peer average) — reusing Phase 5D Section 3's hierarchy exactly, never Simulated in a real evaluation |
| $L_i$ (location) | Approximate coordinates, tied only to `vendor_id` | User-provided |
| `data_status` | Which tier of Phase 5D's demand hierarchy $q_i$ came from, and whether $L_i$/$H_{i,c}$ are present | Structural metadata, not a numeric input |

**Nothing else is added.** No vendor name, phone number, exact address, category-as-a-social-signal, or any attribute not directly required by Stage 1's compatibility and eligibility logic is part of this universe — consistent with this phase's explicit instruction not to add unnecessary personal/vendor information, and with Phase 1C's original privacy design (approximate coordinates tied only to an anonymous ID, never a name).

## 3. Procurement Context

**A group is never formed in the abstract — it is always formed for a specific (commodity, date) pair, exactly as Phase 2A/2B already fixed.** The procurement context is the triple:

$$(c,\ t,\ V_c)$$

where $c$ is the commodity, $t$ is the date, and $V_c = \{i \in V : q_i \text{ is defined and } q_i>0 \text{ for } c\}$ is the commodity-relevant vendor subset for that day (Phase 2B, Part 6C, unchanged).

**Grouping occurs separately for each commodity — vendors requiring different commodities are never merged into one optimization problem.** This is not a new decision; it is Phase 1D's already-approved single-commodity experimental unit (Phase 2A, Part 12) restated here because this phase's Step 3 explicitly asks for it to be confirmed, not assumed. A vendor needing both Potato and Tomato is evaluated in **two independent** procurement contexts, $(\text{Potato}, t, V_{\text{Potato}})$ and $(\text{Tomato}, t, V_{\text{Tomato}})$ — and, per Phase 2B Part 12's own clarification, that same vendor can validly end up in a selected group for one commodity and a different selected group (or no group) for the other, on the same day.

**Procurement horizon:** $k$, Phase 2A's own order-horizon decision variable, bounded by $\min(F_c, \min_{i\in G} H_{i,c})$ — reused exactly, never redefined (per this phase's explicit instruction).

## 4. Eligibility Filter (New — Fills the Gap Section 1 Identified)

**Before a vendor enters compatibility determination at all**, Stage 1 must check that the minimum information required to evaluate them exists. A vendor fails eligibility for procurement context $(c,t)$ if **any** of the following holds:

| Missing/invalid field | Consequence |
|---|---|
| $q_i$ undefined, or defined but negative, for commodity $c$ | Cannot compute $Q_G$ — ineligible |
| $L_i$ missing or unusable (no coordinate recorded) | Cannot evaluate geographic compatibility — ineligible |
| $H_{i,c}$ undefined **and** no purchase-frequency proxy available (Phase 2A, Part 31's own rule, reused here at Stage 1 rather than only at Stage 2) | Cannot bound the order horizon for any group containing this vendor — ineligible |

**A vendor failing this filter is never passed into compatibility determination or candidate generation at all** — they are not silently dropped without explanation, and no missing value is fabricated to let them proceed (per this phase's explicit instruction). Instead, they are immediately routed to:

$$\text{vendor } i \to \text{ABSTAIN for } (c,t), \text{ reason: named missing field}$$

**This is the direct connection between Stage 1 and Phase 5D's `ABSTAIN` state (Section 13 formalizes this further)** — ABSTAIN is not something that can only happen deep inside Stage 2's cost evaluation; it is checked as early as possible, before any compatibility or generation work is wasted on a vendor the system cannot evaluate.

**Vendors who pass this filter form $V_c^{elig} \subseteq V_c$** — the actual population entering Section 5's compatibility model.

## 5. Compatibility Model

**Pairwise compatibility**, reusing Phase 2B's existing geographic rule exactly (Part 6B):

$$\text{Compatible}(i,j) \iff \text{Haversine}(L_i, L_j) \le 2D_{max}$$

— the proven necessary condition for $i$ and $j$ to possibly co-occur in a centroid-feasible group. **No social similarity, reputation, demographic factor, or ML-based similarity is introduced** — none of these exist in this project's data, and per this phase's explicit instruction, none is added without existing justification. Commodity compatibility is already handled at Section 4 (both $i,j \in V_c^{elig}$ by construction, since they are only ever compared within one procurement context).

**Pairwise compatibility is explicitly not the same thing as group-level feasibility, and this document does not conflate them:**

| | Pairwise compatibility | Group-level feasibility |
|---|---|---|
| What it checks | Whether two vendors *could possibly* co-exist in some feasible group | Whether a *specific, fully-formed* group $G$ actually satisfies every hard constraint (Section 8) |
| Necessary or sufficient? | Necessary only (Phase 2B, Part 6B's own chain caveat: $A$–$B$–$C$ can be pairwise-connected while $\{A,B,C\}$ still fails the true centroid constraint) | The actual, sufficient determination — decided once, exactly, by Phase 5D's Stage 2 model |
| Where it's used | Building the compatibility graph (Section 6) to prune the search space cheaply | Evaluating each candidate group that survives generation |

## 6. Candidate Group Generation

**Evaluated against the five listed options, per this phase's explicit instruction not to choose an algorithm because it sounds advanced:**

| Option | Verdict |
|---|---|
| A. Exhaustive search (unscoped, over all of $V$) | Rejected as the *sole* strategy — correct but wasteful and non-scalable if not pruned first (Phase 2B, Part 5) |
| B. Compatibility graph | **Adopted**, as the pruning mechanism |
| C. Connected components/clusters | **Adopted**, as the pool-decomposition mechanism — not a statistical clustering algorithm, an exact graph-theoretic partition |
| D. Greedy expansion | Rejected — no efficiency reason to accept approximation error at this scale (Phase 2B, Part 7, Row 6) |
| **E. Existing Phase 2B method** | **Selected** — B + C combined, feeding exhaustive within-pool subset enumeration |

**Selected method, unchanged from Phase 2B Part 15 Steps 0–3:**
1. Filter to $V_c^{elig}$ (Section 4, extending Phase 2B's original commodity-only filter with the new eligibility check).
2. Build the compatibility graph (Section 5) over $V_c^{elig}$.
3. Decompose into connected components — independent candidate pools, no feasible candidate lost across pools (Phase 2B, Part 6B, proven).
4. Within each pool, enumerate subsets of size $\ge 2$ (full enumeration by default; clique-restriction as a documented refinement if a pool grows large — Phase 2B, Part 15 Step 3).

**Why this remains the right choice for this mini-project, not merely the path of least resistance:** it is mathematically understandable (every step is an exact geometric or logical rule, no black box), computationally reasonable at the expected scale (Section 7), reproducible (deterministic, no randomness anywhere), directly compatible with Phase 5D (candidates feed Stage 2 unchanged), and implementable with standard, well-documented library support (graph connected-components, subset enumeration) — exactly the criteria this phase's Step 6 requires.

## 7. Group Size and Combinatorial Control

For $n$ vendors, the nominal non-empty size-$\ge2$ subset count is $2^n - n - 1$ — unchanged, restated from Phase 2B Part 5: $n{=}10 \to 1{,}013$; $n{=}15 \to 32{,}752$; $n{=}20 \to 1{,}048{,}555$.

**This is controlled, not avoided by assertion, by one exact result:** the $2D_{max}$ triangle-inequality pruning (Section 5) partitions $V_c^{elig}$ into independent geographic pools *before* any subset is generated — combinatorial growth then applies only *within* each small pool, not across the whole vendor set. At V1's realistic scale (10–20 vendors, one locality — Phase 1C), pools are expected to be small (a handful to a dozen or so vendors), keeping within-pool enumeration cheap. **No new scalability claim is made here** — this restates Phase 2B's own analysis (Part 5, Part 14) exactly, per this phase's instruction not to invent one.

## 8. Group-Level Feasibility — Connection to Phase 5D

**Phase 5D's mathematical decision model is the sole authority for evaluating any candidate group $G$ — nothing here redefines or duplicates its formulas.** For every candidate $G$ surviving generation, Stage 2 is invoked exactly as Phase 5D Sections 3–9 specify:

1. Aggregate demand: $Q_G(k) = k\sum_{i\in G} q_i$ (Phase 5D, Section 3).
2. MOQ condition: $Q_G(k) \ge MOQ_c$, conditional (Phase 5D, Section 5).
3. Geographic/logistics feasibility: $d(G) \le D_{max}$ (Phase 5D, Section 7).
4. Freshness/perishability: $k \le \min(F_c, \min_{i\in G} H_{i,c})$ (Phase 5D, Section 6).
5. Individual procurement cost: $C^{ind}_{total,G}(k)$ (Phase 5D, Section 4A).
6. Collaborative procurement cost: $C^{collab}_{G,c}(k)$ (Phase 5D, Section 4B).
7. Savings: $Savings_G(k) = C^{ind}_{total,G}(k) - C^{collab}_{G,c}(k)$ (Phase 5D, Section 4C).
8. Required data availability: already checked at Section 4 above, before $G$ was ever generated — a candidate reaching this step has, by construction, no missing required field.

**The output of this call is one of Phase 5D's four decision states** (Section 13 there) — `BUY_TOGETHER`, `WAIT_OR_EXPAND_GROUP`, `DO_NOT_BUY_TOGETHER`, or (in principle, though pre-empted by Section 4's earlier check for any candidate that reaches this point) `ABSTAIN`.

## 9. Optimization Objective

**Identified exactly from Phase 2B (Part 11), not reinvented:**

$$\text{Primary: } \max \sum_{G \in \text{Selected}} Savings_G(k_G^*) \qquad \text{Secondary (tie-break only): } \max |\{i : i \in \bigcup_{G\in\text{Selected}} G\}|$$

**No demonstrable problem with this objective was found in the Section 1 audit**, so per this phase's explicit instruction, no new objective is invented. It remains a **lexicographic** pair, not a weighted composite — the tie-break only ever activates among selections of equal or near-equal total savings, and never overrides the primary economic objective, exactly as Phase 2B originally specified.

## 10. Overlapping Groups

**Worked exactly as Phase 2B already resolves it (Part 11–12), now stated with the explicit inequality this phase's Step 10 requests.** Let $x_G \in \{0,1\}$ indicate whether candidate group $G$ is *selected* (not merely generated). For a fixed procurement context $(c,t)$:

$$\forall i \in V_c^{elig}: \quad \sum_{G \ni i,\ G \in \text{FeasibleCandidates}} x_G \le 1$$

— no vendor may be part of more than one *selected* group for the same commodity on the same day. **During generation, overlap is expected and unconstrained** — $G_1=\{A,B,C\}$ and $G_2=\{A,D,E\}$ (this phase's own example) are both proposed and both independently evaluated via Section 8; the constraint above is enforced **only** at final selection (Section 11), which is exactly why Phase 2B insists generation and selection remain separate steps (Part 2). **A vendor can appear in two selected groups if they are for different commodities on the same day** — the constraint above is scoped to one $(c,t)$ pair, unchanged from Phase 2B Part 12's clarification.

## 11. Final Group Selection

$$\text{Eligible Vendors} \to \text{Eligibility Filter (§4)} \to \text{Compatibility Filtering (§5)} \to \text{Candidate Generation (§6)} \to \text{Phase 5D Evaluation (§8)} \to \text{Feasible (BUY\_TOGETHER) Candidates} \to \text{Objective-Based Selection (§9–10)} \to \text{Final Recommendation}$$

**Selection criteria:** exact weighted set packing over the `BUY_TOGETHER`-eligible candidate pool, maximizing total savings subject to the disjointness constraint (Section 10); vendor coverage breaks ties (Section 9). **At V1's expected candidate-pool sizes, this is solved by brute-force enumeration over combinations of non-overlapping feasible candidates** — unchanged from Phase 2B Part 15 Step 6; a small ILP remains the documented, not-yet-needed fallback if pool sizes grow.

**Handling equally-good groups:** if two disjoint selections tie exactly on total savings *and* vendor coverage, no further tie-break is invented (per this phase's standing rule against unjustified weighted scoring) — either is reported, with both alternatives shown in the reasoning trace so a human can decide if it matters in practice.

**Handling vendors left ungrouped: this is a normal, expected, valid output, never forced.** A vendor with no eligible geographic pool-mate, or whose every candidate group resolved to `DO_NOT_BUY_TOGETHER` or was excluded by set-packing conflict resolution in favor of a higher-value alternative, simply receives no group recommendation for that commodity that day — restated from Phase 2B Part 15 Step 7, not changed.

## 12. WAIT_OR_EXPAND_GROUP Logic (New Mechanism)

**Trigger condition** (Phase 5D, Section 5, restated at the group-formation level): candidate $G$ fails Section 8's MOQ check for every tested $k$, **and** at least one tested $k$ would have produced $Savings_G(k) > 0$ had $MOQ_c$ been met.

**The key design insight that keeps this bounded and simple: no new search loop is needed.** Because Section 6's within-pool generation step already enumerates **every** subset of the pool — including every proper superset of $G$ — **every possible expansion of $G$ has already been generated and evaluated by the time $G$'s own result is known.** `WAIT_OR_EXPAND_GROUP` is therefore not a new algorithm; it is a **reporting rule** applied to results the existing pipeline already computed:

$$\text{WAIT\_OR\_EXPAND\_GROUP for } G \iff G \text{ trigger holds, and } \exists\, G' \supset G,\ G' \subseteq \text{pool}(G): \text{Stage 2}(G') = \texttt{BUY\_TOGETHER}$$

**Which vendors can be considered for expansion:** only vendors already inside $G$'s own geographic pool (Section 6) — never a vendor outside the $2D_{max}$ compatibility graph, since that would violate the already-proven geographic necessary condition. **This is exactly "reuse Phase 2B logic if it already handles this,"** per this phase's instruction — it does, once the connection is made explicit.

**Stopping condition (no infinite search, by construction):** the search space is the pool, which is finite and already fully enumerated in Section 6 — there is nothing left to try beyond what generation already tried. If **no** superset of $G$ within its pool achieves `BUY_TOGETHER`, then:

$$\text{If } \nexists\, G' \supset G \text{ with Stage 2}(G')=\texttt{BUY\_TOGETHER}: \quad \text{report } \texttt{DO\_NOT\_BUY\_TOGETHER} \text{ for } G, \text{ not an open-ended "keep waiting."}$$

This is the honest resolution this phase's Step 12 explicitly requires — the system never promises an indefinite wait with no evidence a path exists; it checks the entire realistically-available pool exactly once (already done as a side effect of generation) and reports accordingly.

## 13. ABSTAIN in Group Formation

**`ABSTAIN` is returned at exactly one point in this pipeline: Section 4's eligibility filter, before compatibility or generation ever runs for the affected vendor.** Concretely:

- Missing critical vendor data ($q_i$ undefined or negative) → `ABSTAIN`, reason: "demand estimate unavailable."
- Insufficient location information ($L_i$ missing) → `ABSTAIN`, reason: "location unavailable — cannot evaluate geographic compatibility."
- Undefined $H_{i,c}$ with no purchase-frequency proxy → `ABSTAIN`, reason: "practical procurement horizon unavailable."

**`ABSTAIN` does not mean the algorithm failed.** Restated directly from Phase 5A's own framing, applied here at the group-formation stage: it means *the system has correctly recognized it lacks the evidence needed to make a reliable decision for this specific vendor, in this specific context, and is saying so explicitly rather than guessing.* A vendor's `ABSTAIN` status for commodity $c$ does not affect their evaluation for a different commodity $c'$ where their data is complete — abstention is scoped to the specific $(c,t)$ context that triggered it, not a global vendor status.

## 14. Computational Complexity and Scalability

**Restated from Phase 2B (Parts 5, 14), not re-derived:**

| Vendor count | Regime |
|---|---|
| ~5–20 (this mini-project's realistic scale) | Compatibility graph has few, small connected components for a realistic single-locality distribution; within-pool exhaustive enumeration and final set-packing selection are both cheap | **This design's actual, honestly-scoped range** |
| ~50 | Borderline — individual pools may approach a size where enumeration starts to slow; monitor pool size, not just total vendor count |
| ~100 | Individual pools could plausibly need a greedy/ILP fallback *within that pool only* — not a redesign of the whole architecture |
| ~1,000 | A genuinely different regime (spatial indexing, hierarchical decomposition) — clearly out of scope for a mini-project, stated honestly rather than implied to already work |

**This design is appropriate for approximately 5–20 vendors, stated honestly, not exaggerated.** The `WAIT_OR_EXPAND_GROUP` mechanism (Section 12) adds zero additional complexity, since it reuses already-enumerated candidates rather than searching further — this is confirmed here as a complexity fact, not merely a design convenience.

## 15. Worked Illustrative Example

**SIMULATED ILLUSTRATIVE SCENARIO — NOT REAL DATA.** All vendor IDs, coordinates, quantities, and prices below are invented for demonstration only.

**Setup:** Commodity = Potato (illustrative), $D_{max}=2$ km, $TC(\text{small})=₹800$/trip, $p^{wh}=₹15/\text{kg}$, $m=0.10 \Rightarrow p^{eff}=₹16.50/\text{kg}$, $MOQ_{\text{potato}}=200$ kg, $H_{i,c}=5$ days for every vendor below, $F_{\text{potato}}$ = several weeks (never binds).

**1. Vendor universe (7 vendors):**

| Vendor | $q_i$ (kg/day) | $p^{ind}_i$ (₹/kg) | Location (illustrative km-offset) | Notes |
|---|---|---|---|---|
| V1 | 10 | 30 | (0, 0) | |
| V2 | 8 | 28 | (0.5, 0.3) | |
| V3 | 6 | 32 | (1.0, 0.5) | |
| V4 | 12 | 29 | (1.5, 1.0) | |
| V5 | 9 | 31 | (10, 10) | Far from all others |
| V6 | — | — | **missing** | No recorded location |
| V7 | 4 | 31 | (0.8, −0.5) | |

**2. Eligibility filtering (§4):** V6 has no recorded location → **`ABSTAIN`** ("location unavailable"). V1–V5, V7 pass (all fields present, $q_i>0$). $V_c^{elig} = \{V1,\dots,V5,V7\}$.

**3. Compatibility filtering (§5):** V5 is $>13$ km from every other vendor ($\gg 2D_{max}=4$ km) — isolated, its own pool of size 1. $\{V1,V2,V3,V4,V7\}$ are all pairwise within 4 km — one connected pool of size 5.

**4–5. Candidate groups, including overlap:** within the 5-vendor pool, candidates $G_1=\{V1,V2,V3,V4\}$ and $G_2=\{V1,V2,V7\}$ **overlap** on V1, V2 — both are generated and evaluated independently, per Section 6/10.

**6–7. Group-level evaluation and MOQ outcome** (full arithmetic; $C^{ind}_{total,G}(k) = k\sum_i q_i p^{ind}_i$, $C^{collab}_G(k)=Q_G(k)\times16.5+800$):

| Candidate | $\sum q_i$ | $Savings_G(k)$ formula | Max feasible $k$ | $Q_G(k{=}5)$ | MOQ met? | Best $Savings_G$ | Outcome |
|---|---|---|---|---|---|---|---|
| $G_1=\{1,2,3,4\}$ | 36 | $470k-800$ | 5 | 180 kg | ❌ (180<200) | +₹1,550 (at $k$=5, MOQ ignored) | **`WAIT_OR_EXPAND_GROUP`** |
| $G_2=\{1,2,7\}$ | 22 | $285k-800$ | 5 | 110 kg | ❌ | +₹625 | **`WAIT_OR_EXPAND_GROUP`** |
| $G_3=\{3,4\}$ | 18 | $243k-800$ | 5 | 90 kg | ❌ | +₹415 | **`WAIT_OR_EXPAND_GROUP`** |
| $G_4=\{3,7\}$ | 10 | $151k-800$ | 5 | 50 kg | ❌ | **−₹45** (never positive) | **`DO_NOT_BUY_TOGETHER`** (economics never work, independent of MOQ) |
| $G_{all}=\{1,2,3,4,7\}$ | 40 | $528k-800$ | 5 | **200 kg** | ✅ (200≥200) | **+₹1,840** | **`BUY_TOGETHER`**, $k^*=5$ |

**Per §12: $G_1$, $G_2$, and $G_3$ all trigger `WAIT_OR_EXPAND_GROUP`, and all resolve via the same already-enumerated superset $G_{all}$**, which is the only candidate in this pool reaching `BUY_TOGETHER` — its aggregate quantity clears $MOQ_{\text{potato}}$ at exactly $k=5$ (200 kg, precisely at the threshold) with positive net savings. $G_4$ is a genuine `DO_NOT_BUY_TOGETHER` — its economics never turn positive at any tested $k$, independent of MOQ, so no amount of "waiting" would be honestly promised.

**8. Savings comparison and per-vendor allocation for the selected group $G_{all}$** (quantity-proportional, Phase 5D Section 4):

| Vendor | $q_i$ | Share of $C^{collab}$ | $C^{ind}_i(5)$ | Individual savings |
|---|---|---|---|---|
| V1 | 10 | ₹1,025 | ₹1,500 | ₹475 |
| V2 | 8 | ₹820 | ₹1,120 | ₹300 |
| V3 | 6 | ₹615 | ₹960 | ₹345 |
| V4 | 12 | ₹1,230 | ₹1,740 | ₹510 |
| V7 | 4 | ₹410 | ₹620 | ₹210 |
| **Total** | 40 | ₹4,100 | ₹5,940 | **₹1,840** ✅ matches $Savings_{G_{all}}$ |

**9. Final group selection:** $G_{all}$ is the only `BUY_TOGETHER` candidate in this pool and is selected outright (no competing disjoint alternative exists to conflict with it). $G_1$, $G_2$, $G_3$, $G_4$ are all subsumed/superseded — their members are already covered by $G_{all}$.

**10. Vendor/group not selected:** **V5** — isolated, no compatible pool-mate for Potato that day, receives "no recommendation: no compatible geographic partner." **V6** — `ABSTAIN`, as established at Step 2 above. Neither is forced into a group.

**No number in this section represents real vendor data.**

## 16. Stage 1 → Stage 2 Final Architecture

```
STAGE 1 — GROUP FORMATION
  Input vendors (V)
        |
        v
  Eligibility filter (§4) -------------------> [missing data] --> ABSTAIN
        |  (passes)
        v
  Compatibility determination (§5, graph over 2*D_max)
        |
        v
  Candidate group generation (§6: connected components -> within-pool subset enumeration)
        |
        v
  Candidate groups (may overlap freely at this point)


STAGE 2 — DECISION MODEL (Phase 5D, called once per candidate, unmodified)
  Candidate group G
        |
        v
  Aggregate demand Q_G(k)
        |
        v
  Geographic check d(G) <= D_max? ------------> [fail] --> DO_NOT_BUY_TOGETHER
        |  (pass)
        v
  Freshness/horizon bound k in {1..min(F_c,H_i,c)}
        |
        v
  MOQ check Q_G(k) >= MOQ_c (if MOQ_c known)
        |                        \
        | (met, or N/A)           \--[not met for any k]--> is Savings_G(k)>0 achievable
        v                                                     once MOQ is met?
  Cost / Savings comparison                                      |            |
        |                                                      yes            no
        v                                                        |            |
  Savings_G(k) > 0 for some k? --[no]--> DO_NOT_BUY_TOGETHER      v            v
        |                                              WAIT_OR_EXPAND_GROUP   DO_NOT_BUY_TOGETHER
        v (yes)                                        (resolved via an
  BUY_TOGETHER, k* = argmax Savings_G(k)                 already-enumerated
                                                          superset, §12)

  Selected BUY_TOGETHER candidates only -> Final Selection (§9-11, weighted set packing)
                                              -> Final Recommendation
```

**Where each of the four decision states occurs, stated once more for clarity:** `ABSTAIN` — Stage 1's eligibility filter, before any group is even proposed. `DO_NOT_BUY_TOGETHER` — Stage 2, either at the geographic check (immediate stop) or when no tested $k$ achieves positive savings even with MOQ satisfied/inapplicable, or when MOQ fails and no pool superset rescues it. `WAIT_OR_EXPAND_GROUP` — Stage 2, specifically when MOQ is the sole blocker and a pool superset achieves `BUY_TOGETHER`. `BUY_TOGETHER` — Stage 2, when all constraints pass and $Savings_G(k)>0$ for some $k$, then confirmed as part of the final non-overlapping selection.

## 17. Final Consistency Audit

| # | Check | Result |
|---|---|---|
| 1 | Phase 2B valid logic preserved | ✅ Graph generation, geographic pruning, objective, overlap resolution, complexity analysis — all reused unchanged (Sections 1, 6, 7, 9, 10, 14) |
| 2 | Compatible with Phase 5D notation | ✅ Section 8 calls Phase 5D's Sections 3–9 directly, no re-derivation |
| 3 | No dependency on unavailable ML | ✅ $q_i$ remains an `ESTIMATE` throughout (Phase 5D Section 3); no ML appears anywhere in Sections 4–13 |
| 4 | No synthetic data represented as real | ✅ Section 15 is explicitly labeled `SIMULATED ILLUSTRATIVE SCENARIO`; no other section introduces numeric data |
| 5 | Commodity grouping unambiguous | ✅ Section 3 fixes one $(c,t)$ pair per optimization run; no cross-commodity merging occurs anywhere |
| 6 | Candidate generation defined | ✅ Section 6, reusing Phase 2B Part 15 Steps 0–3 exactly |
| 7 | Group-level feasibility separated from pairwise compatibility | ✅ Section 5's explicit table distinguishes necessary (pairwise) from sufficient (group-level, Phase 5D) |
| 8 | Overlapping groups resolved | ✅ Section 10's explicit inequality, demonstrated concretely in Section 15 ($G_1$/$G_2$ overlap, both subsumed by $G_{all}$) |
| 9 | Objective function explicit | ✅ Section 9, lexicographic, no invented weights |
| 10 | No forced grouping | ✅ Section 11, V5 in Section 15 explicitly left ungrouped |
| 11 | WAIT/EXPAND logic terminates | ✅ Section 12 — bounded by the already-finite, already-enumerated pool; no new search loop introduced |
| 12 | ABSTAIN is evidence-based | ✅ Section 13 — triggered only by a named missing field, never by "the algorithm couldn't decide" |
| 13 | Computational limitations honestly stated | ✅ Section 14 — 5–20 vendor range stated as the actual scope, not exaggerated |
| 14 | No unnecessary algorithmic complexity | ✅ Section 6 explicitly rejected greedy/metaheuristic alternatives for adding complexity without benefit at this scale; `WAIT_OR_EXPAND_GROUP` was designed specifically to avoid adding a new search algorithm (Section 12) |

**No inconsistency was found requiring a structural change.**

## 18. Exact Recommendations for the Next Phase

- **Implement Sections 4–13 as actual backend logic** — still not done, per this phase's own scope limits; this document is the specification, not the implementation.
- **Verify the eligibility filter (Section 4) against however Phase 1C's survey/diary data ends up actually structured**, if and when that data collection is executed — the field-name mapping (`q_i`, $L_i$, $H_{i,c}$) should be checked against the real collection template (`reports/vendor_data_collection_template.md`) rather than assumed to match exactly.
- **Implement the `WAIT_OR_EXPAND_GROUP` reporting rule (Section 12) as a post-processing step over Section 6's already-computed candidate results** — explicitly not as a new search procedure, to preserve the complexity guarantees of Section 14.
- **Extend Phase 5A's module specification** (Data Quality Auditor, Granularity Validator, Model/Method Selector, Abstention Engine, Explanation Generator) to explicitly reference this document's eligibility filter and decision-state routing as their group-formation-stage implementation.
- **Re-run this design's worked-example arithmetic (Section 15) as an actual unit test once implemented**, to confirm the real code reproduces the same numbers before trusting it on any future real vendor data.

---

**Files produced by this phase:**
- This report.
- `reports/phase5e_phase2b_reconciliation.md`.

**Files read but not modified:** `research/phase2a_mathematical_model.md`, `research/phase2b_algorithm_selection.md`, `reports/phase5d_mathematical_decision_model.md`, `reports/phase5d_phase2_reconciliation.md`, `reports/phase5a_research_findings_and_system_policy.md`. No dataset was modified. No model was trained. The Potato forecasting experiment was not reopened.
