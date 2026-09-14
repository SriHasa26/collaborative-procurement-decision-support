# Phase 5C — Demand Data Strategy and ML Feasibility Audit

**Date:** 2026-09-14
**Scope:** Determine whether vendor-demand machine learning is scientifically feasible for this project, and what data strategy should be used if not. No application code is built. No model is trained. No synthetic dataset is generated. This is a planning and feasibility audit only.
**Continuity note, stated up front because it matters:** this is not the first time this project has asked whether vendor demand forecasting is ML-feasible. **Phase 1C, Phase 3 (system architecture), and Phase 3A.1 each independently examined this question and reached the same conclusion — traditional supervised ML for vendor demand is not justified at this project's realistic data scale (10–20 vendors, 70–280 vendor-day observations).** This phase is the fourth audit of the same question. As Phase 3A.1 itself noted about its own (third) confirmation: reaching the same conclusion a third or fourth time from independent angles is itself informative — it indicates a real, structural data constraint, not an unlucky or borderline case that a slightly different framing might overturn.

---

## 1. Exact Demand Prediction Problem Definition

### 1.1 Input

What could realistically be known about a vendor at prediction time, drawn only from what Phase 1C's own survey/diary design already identified as collectible (not invented fresh here):

| Candidate input | Realistically available? |
|---|---|
| Vendor category (tea stall, chaat, fruit cart, etc.) | ✅ Yes — a single survey question |
| Commodity | ✅ Yes — vendor names what they buy |
| Historical purchase/usage quantity (per commodity) | ⚠️ Only for vendors who complete a purchase diary — not from a one-time survey |
| Day of week | ✅ Yes, but only meaningful if diary data spans multiple weeks |
| Purchase frequency (daily/every-2-days/weekly) | ✅ Yes — a survey question |
| Approximate location (for grouping, not demand prediction itself) | ✅ Yes — approximate coordinates, per Phase 1C's already-established privacy-preserving method |

### 1.2 Target

**Predicted quantity required for a given commodity, for a given vendor, over a defined horizon.**

### 1.3 Prediction Horizon — defined precisely, not left vague

The only horizon that matches how this platform actually needs a demand number is the **procurement/order-horizon $k$ already defined in Phase 2A's mathematical model** — the number of days of demand a collaborative order is meant to cover. This is not a new invention for this phase; it is reusing an already-approved definition rather than creating a second, competing notion of "the demand forecast." A demand estimate that used a different horizon (e.g., "tomorrow only") would not actually be usable by Phase 2A's cost model without a redefinition this project has not approved.

### 1.4 Individual vs. Category-Level Demand — explicitly not assumed equivalent

| | A. Individual vendor demand prediction | B. Category-level demand estimation |
|---|---|---|
| What it estimates | *This specific vendor's* quantity requirement | The *typical* quantity requirement for vendors of a given category (e.g., "a tea stall typically uses X kg of X per day") |
| Data needed | Multiple historical observations *for that vendor* | A cross-section of *several vendors in the same category* — does not require any single vendor's history to repeat |
| Status in this project | Requires per-vendor time-series history — exactly what Phase 1C already found infeasible at 10–20 vendors | This is what Phase 1C's Layer 1 (similarity-based case reasoning) already relies on, and is realistically collectible from a single survey |

**These are not interchangeable, and this report does not treat them as such anywhere below.** A is the harder, data-hungrier problem; B is the one this project's actual realistic data supports.

## 2. Data Requirements Audit

| Field | Purpose | Required / Optional | Source | Availability (verified, not assumed) | Data quality concerns |
|---|---|---|---|---|---|
| `vendor_id` (anonymous) | Link records across tables without identifying individuals | Required | Assigned at collection | Not yet collected — no vendor dataset currently exists in this project | None if assigned consistently |
| `vendor_category` | Cold-start grouping (Layer 1); category-level estimation | Required | One-time survey | Not yet collected | Vendors' self-described category may not map cleanly to a fixed taxonomy — needs a short, fixed pick-list at collection time |
| `commodity` | What demand is being estimated for | Required | Survey/diary | Not yet collected | Multiple commodities per vendor increases per-cell sparsity (see Section 5) |
| `date` | Needed only for diary-based (time-series) collection | Required for B (limited-history/ML), not for a one-time survey | Diary | Not yet collected | Vendors may skip days — Phase 1C already flagged this (recall bias, missing diary days) |
| `quantity_used_or_purchased` | The actual demand signal | Required | Survey (typical quantity) or diary (actual daily quantity) | Not yet collected | Recall bias for survey-only figures (Phase 1C, K1); unit inconsistency (bags/crates/₹-worth vs. kg — Phase 1C, K2) |
| `location` (approximate coordinates) | Geographic grouping — **not** a demand-prediction input, included for completeness since it appears in the vendor profile | Required for the grouping engine, not for demand itself | Survey | Not yet collected | Privacy — must be tied only to the anonymous ID (Phase 1C, K7), never a name or exact address |
| `purchase_frequency` | Distinguishes daily buyers from weekly/bulk buyers — needed to interpret a raw quantity figure correctly | Required | Survey | Not yet collected | Self-reported, approximate |

**No field in this table is marked "available" without a verified source.** Every row above says, plainly, that the underlying vendor dataset does not yet exist in this project — this is stated as a fact, not softened.

## 3. Real Data Feasibility

**A. Real data already available to this project: none, for vendor-level demand.** Every public/government dataset this project has acquired and verified so far (Phases 3A.2–3A.5) is *commodity price* data — Agmarknet/CEDA wholesale mandi prices for Tomato and Potato. **None of it contains a single street vendor's purchase quantity, purchase frequency, or category.** This is stated explicitly because it would be easy to conflate "we have real price data" with "we have real demand data" — this report does not make that substitution.

**B. Data that can realistically be manually collected:** Phase 1C already designed this in detail — a hybrid survey (15–20 vendors) plus a 7–14 day purchase diary from a willing subset (5–10 vendors). **This plan has been designed but, as of this phase, has not been executed** — no survey or diary data exists in this project's files. Section 4 below restates this plan without re-deriving it from scratch, since Phase 1C already did that work correctly.

**C. Public datasets — investigated and found not genuinely relevant:** No public dataset investigated in this project (data.gov.in, CEDA, Agmarknet, or any source found in Phases 3A.2–3A.4) represents *individual street vendor commodity demand*. These sources describe **wholesale market transactions and prices**, which is a different economic actor (traders, mandis) from the demand side this platform actually needs (individual informal-sector vendors' purchase quantities). **No unrelated dataset is substituted here to manufacture an appearance of data availability.** If a reader were to ask "is there a public street-vendor-demand dataset," the honest answer, based on everything this project has actually checked, is no.

**D. Data unavailable to this project:** any large-N, multi-month, per-vendor transaction log — the kind of dataset that would make individual-vendor ML (Section 1.4, column A) statistically defensible. No realistic path to this data exists within a student mini-project's time and access constraints, as Phase 1C already established.

## 4. Manual Data Collection Plan

**This restates, rather than redesigns, Phase 1C's already-approved plan — because nothing about that plan's realism has changed, and re-deriving it here from scratch would risk silently drifting from decisions already made.**

| Parameter | Recommendation | Source |
|---|---|---|
| Number of vendors | 15–20 (survey), with 5–10 of those also completing a diary | Phase 1C |
| Number of commodities | The 2–3 this project already studies (Tomato, Potato — Onion excluded per Phase 3A.2–3A.4's own findings) | Consistent with existing project scope |
| Collection duration | One-time survey (5–10 minutes per vendor) + 7-day diary for the willing subset | Phase 1C recommends 7 days over 14: meaningfully lower attrition risk for a marginal data gain |
| Collection frequency (diary) | Once per day, one line per commodity | Phase 1C |
| What vendors record | See the companion template, `reports/vendor_data_collection_template.md` | This phase |

**Critical evaluation of which fields are actually necessary — not every plausible field is recommended:**
- `quantity_remaining` (unsold stock) is **useful but not required** for a first cut: it helps distinguish "used because sold" from "used because it spoiled," but adds a field vendors must estimate under time pressure. **Recommended as optional**, not mandatory, consistent with this phase's instruction to critically evaluate necessity rather than default to a longer form.
- `payment_method` (cash/UPI/credit) is valuable per Phase 1B/1C's own payment-trust findings, but **is not needed for a demand estimate specifically** — it belongs in the vendor profile survey, not the daily diary, and is not included in the demand-focused template this phase produces.
- `date` and `quantity_purchased` are the two fields this report treats as truly non-negotiable for any diary-based collection — without them, there is no time series at all.

## 5. ML Feasibility Analysis

| Scenario | Data volume | Appropriate method | Is ML justified? | Limitations |
|---|---|---|---|---|
| **A — Very little data** | A single survey snapshot per vendor (no diary), or a brand-new vendor with zero history | Category-level estimate (Layer 1, case-based reasoning) | **No.** A single cross-sectional number per vendor cannot train or validate anything — there is no time dimension to hold out | Estimate quality depends entirely on how comparable the category peer group actually is; explicitly not a prediction, an estimate (Section 6) |
| **B — Moderate prototype data** | A 7–14 day diary from 5–10 vendors (Phase 1C's realistic ceiling — ~35–140 vendor-day records, thinner still per specific commodity) | Simple statistical baseline (last observed value, short moving average, category-level mean) | **No, not for a trained/validated model.** This is close to the exact scale (70–280 vendor-day records) that Phase 1C, Phase 3, and Phase 3A.1 already independently found too sparse for supervised ML | Enough for descriptive statistics (mean, spread) per vendor or per category; a per-vendor trained model would very likely memorize noise, and this project now has a concrete demonstration (the Potato experiment, Phase 4C) of exactly how a plausible-looking validation result can fail to generalize — on a series with nearly *twice* this data volume (175 observations, one series) and *no* per-entity fragmentation |
| **C — Sufficient historical data** | Months of regular, per-vendor, per-commodity purchase records across many vendors (not currently available or realistically collectible in this project's timeframe) | Candidate ML model, evaluated with the exact validate-then-test discipline used for Potato (Section 8) | **Would need to be tested empirically, not assumed** | Not achievable within this mini-project's realistic scope; named here only to complete the hierarchy, not as a near-term plan |

**Evidence-based hierarchy, exactly as this phase's brief specifies:**

```
NO HISTORY            -> category-level estimate  (Layer 1: case-based reasoning)
LIMITED HISTORY        -> simple statistical baseline
SUFFICIENT VALIDATED DATA -> candidate ML model (only after passing the Section 8 protocol)
```

**On thresholds:** Phase 1C's own numbers (10–20 vendors, 70–280 vendor-day records) are **empirically-grounded observations about this project's realistic collection scale**, not a scientifically derived universal cutoff for "how much data ML needs in general." **Any specific numeric threshold used to decide "limited" vs. "sufficient" in a future implementation (e.g., a minimum vendor-day count before even attempting Scenario C's protocol) must be labeled a configurable experimental policy parameter** — exactly as this phase's instructions require, and consistent with how Phase 3A.7/3A.9 already treated similar thresholds (the 90-day floor, the fold-size choice) as reasoned-but-adjustable design choices, not proven constants.

## 6. Cold-Start Strategy

**For a new vendor with zero history:** the only usable information is `vendor_category`, `commodity`, and, if collected at onboarding, a manually-entered typical daily requirement (the vendor's own estimate, given in their own units and converted afterward — per Phase 1C's unit-handling recommendation).

**Estimation method:** a same-category peer average — take the 2–3 most comparable vendors' reported typical quantities (from the survey) and use their mean or a simple weighted average as the new vendor's starting estimate. This is **case-based/similarity-based reasoning**, the same technique family Phase 1C already named for this exact purpose.

**Explicitly distinguished, per this phase's strict instruction:**

| | Estimation | ML Prediction |
|---|---|---|
| What it is | A rule-based average over a small peer group | A model fit on historical data, validated on unseen data |
| Requires training/validation? | No | Yes |
| What this system does for cold-start | **This** | Not this |
| Correct label | "Category-level estimate" / "case-based estimate" | "ML prediction" — **never used for the cold-start case** |

**A rule-based category average must never be called "AI" or "ML" anywhere in this system's output, documentation, or user-facing text.** This is a direct, binding restatement of Phase 1C's own warning ("a judge who asks 'where is the AI?' after hearing 'our AI model uses category averages' has a fair point") and of this phase's explicit instruction.

## 7. Limited-History Strategy

For a vendor with a small amount of real diary history (say, 3–14 daily records):

| Method | How it works | When preferable |
|---|---|---|
| Last observed demand (persistence) | $\hat{q}_{t+1} = q_t$ | Simplest; a reasonable default when even a moving average's 3-point window isn't yet available |
| Short moving average (e.g., last 3 records) | Mean of the last 3 recorded quantities | Slightly smooths day-to-day noise once at least 3 records exist |
| Category-level estimate | Same as Section 6, used as a floor/fallback | If the vendor's own few records look implausible (e.g., a single unusually large one-off purchase) |

**Why simple methods are preferable here, not just permissible:** this project has direct, recent, first-party evidence for exactly this caution — the Potato price-forecasting experiment (Phase 4A–4C) showed a more complex model (Linear Regression) beat a simple baseline (moving-average-3) during validation, only to perform *worse* than that same simple baseline on a genuinely unseen final test. That happened with 175 real observations on a single continuous series. A vendor with 3–14 diary entries has far less data and far more entity-level fragmentation (many vendors × few days each, rather than one long series) — the same overfitting risk applies with less room to detect it.

**The system must report which method generated the estimate, every time** — a demand figure produced by "last observed value" must be labeled as such, not left ambiguous or implied to be more sophisticated than it is.

## 8. Future ML Strategy (Requirements Only — Not Executed)

**What a genuine vendor-demand ML experiment would require, if this project ever collected sufficient data:**

| Element | Requirement (directly reusing what the Potato experiment demonstrated works) |
|---|---|
| Dataset structure | Per-vendor, per-commodity, chronologically-ordered records — no random shuffling permitted, exactly as Phase 3A.9 established for time-dependent data |
| Chronological validation | Expanding-window validation, never a random train/test split |
| Mandatory baselines | Persistence and a short moving average must be implemented and beaten before any model is considered — exactly the two baselines used for Potato |
| Candidate ML models | Low-complexity only, evaluated the same way Phase 4A restricted itself (e.g., Linear/Ridge Regression, a shallow Decision Tree) — not introduced here as a new list, reused as a policy |
| Evaluation metrics | MAE primary, RMSE secondary — consistent with Phase 3A.7's reasoning (MAPE checked for suitability, not assumed) |
| Final untouched test set | Held out from the start, evaluated exactly once, after model selection is fully closed — exactly the discipline that caught the Potato model's generalization failure |

**Directly reused lessons from the Potato experiment, restated as binding requirements for any future demand-ML work, not as generic best practice:**
- No random shuffling for time-dependent data (Phase 3A.9).
- Baselines are mandatory, not optional (Phase 3A.9/4A).
- Chronological (expanding-window) validation only (Phase 3A.9).
- A final test set must remain untouched until model selection is closed (Phase 4B/4C).
- No test-set-driven tuning, ever (Phase 4C).
- **Negative results must be reported honestly** — the Potato experiment's own conclusion ("simple baselines performed as well as or better than the selected ML model") is the standard this project holds itself to, and any future demand-ML attempt must be reported the same way if it comes out the same way.

**No model is trained under this section. This is a specification for a future phase to follow, contingent on data that does not currently exist.**

## 9. Synthetic Data Policy

**Synthetic/simulated data MAY be used for:**
- Testing the UI.
- Demonstrating group formation logic.
- Testing MOQ constraints.
- Testing freshness constraints.
- Testing logistics/transport-cost calculations.
- Demonstrating decision scenarios (e.g., "if 5 vendors each need X kg, does the system recommend collaboration?").

**Synthetic data MUST NOT be used to claim, imply, or present:**
- "ML accurately predicts real vendor demand" — no such claim is supportable, and none is made anywhere in this project.
- Any performance metric (accuracy, MAE, etc.) computed on synthetic data as if it described real-world vendor behavior.

**Required labeling, applied consistently wherever synthetic data appears in any future artifact:**

> **`SIMULATED PROTOTYPE DATA`** — for synthetic vendor/demand scenarios used to exercise the optimization engine (Phase 2A/2B), grouping logic, or UI.
>
> **`ILLUSTRATIVE TEST SCENARIO`** — for a specific worked example (e.g., a walkthrough of "5 vendors, 2 commodities, here is what the system recommends") used for demonstration or documentation purposes.

**This project's existing standing rule (Phase 1C, Section on synthetic data expansion; reaffirmed in every data-acquisition phase since 3A.2) is carried forward unchanged: every distributional assumption behind synthetic data must be written down explicitly, and synthetic data must never be presented in a way that could be mistaken for an observed result.** **No synthetic dataset is generated in this phase** — this section defines the policy that would govern one if and when it is created.

## 10. Final Demand Intelligence Architecture (Conceptual)

```
NEW VENDOR (no history)
        |
        v
Cold-start estimation (Section 6)
  method: same-category peer average
  label:  "ESTIMATE — category-based"
        |
        v
LIMITED HISTORY (a few diary records accumulate)
        |
        v
Baseline demand estimation (Section 7)
  method: last-observed-value or short moving average
  label:  "ESTIMATE — <method name>"
        |
        v
SUFFICIENT VALIDATED HISTORY (not currently reached by this project)
        |
        v
ML candidate (Section 8), ONLY IF it has passed:
  (a) chronological validation improvement, AND
  (b) generalization on an untouched final test
  label:  "PREDICTION — ML (<model name>), validated <date>"
```

**This architecture does not automatically escalate to ML as more data accumulates.** Escalation from "baseline" to "ML" requires the Section 8 protocol to actually be run and to actually pass — exactly the standard the Potato experiment failed to clear on its final test. Every demand figure the system produces, regardless of which tier generated it, must expose:
- **Estimated demand** (the number itself).
- **Method used** (category-average / last-observed / moving-average / a named validated ML model).
- **Data availability status** (no history / limited history / sufficient validated history).
- **Limitations** (e.g., "based on 3 category peers," "based on 5 days of this vendor's own history," "validated on a single 35-day test period for a different commodity/domain — not yet validated for vendor demand").

## 11. Explicit Limitations

- **No vendor demand data of any kind currently exists in this project.** Every number in this report about "70–280 vendor-day records" describes a *plan's* projected scale, carried over from Phase 1C — not data that has been collected, inspected, or verified in the way this project's own price-data phases (3A.2–3A.6) rigorously required before trusting a number.
- **This is the fourth time this project has examined vendor-demand ML feasibility and reached the same conclusion.** This is reported as a strength of the audit trail, not papered over as redundant — but it also means this phase has not found anything *new* that would change the answer; it has confirmed the answer holds under a fresh, more rigorous lens (informed by the Potato generalization-failure lesson) than the earlier three audits had available.
- **The Section 8 future-ML protocol is untested** — it specifies what a future experiment must do, not what it will find. This report does not predict that a future, larger vendor dataset would or would not support ML; it only specifies the honest procedure for finding out.
- **Category-level estimation (Layer 1) is a real technique family but a weak one at small N** — with 15–20 vendors across several categories, most categories will have only a handful of peers, which is a known, disclosed limitation of the estimate's precision, not a defect unique to this project's execution.

## 12. Final Feasibility Verdict

**C. ML NOT JUSTIFIED FOR CURRENT MINI-PROJECT DATA.**

This is not a new, isolated conclusion — it is the **fourth independent confirmation** of a finding this project has already reached in Phase 1C, Phase 3, and Phase 3A.1, now reinforced by a concrete demonstration (the Potato price-forecasting experiment) of exactly the generalization failure this data scale would risk. No vendor demand dataset currently exists; the realistic collection plan Phase 1C already designed would, even fully executed, produce a dataset (70–280 vendor-day records, fragmented across vendors and commodities) smaller and thinner than the single-series, 175-observation Potato dataset that already demonstrated a validation-stage improvement failing to survive a final test.

**This does not weaken the project.** Per this phase's own instruction, and consistent with Phase 1C's original three-layer framing, the project remains technically strong on the layers that do not depend on vendor-demand ML:

- **Layer 1 — Cold-start/limited-history demand estimation** (Sections 6–7 above): real, useful, honestly labeled as estimation, not ML.
- **Layer 3 — the optimization core** (Phase 2A's mathematical model, Phase 2B's constrained combinatorial optimization): mathematical order sizing, constrained group formation, economic viability calculations, freshness constraints, and MOQ constraints — none of this depends on Layer 2 (predictive ML) existing, and all of it is already validated project work, untouched by this phase.
- **The Potato price-trend work** (Phases 3A.1–4C) remains this project's one genuine, honestly-evaluated ML experiment — its negative-leaning final result is itself a legitimate research finding (Phase 5A), not evidence the project lacks technical substance.

**ML is not forced into this project merely because its name contains "AI."** The system's actual intelligence, as this project has now established across two independent domains (price forecasting and vendor demand), lives in disciplined estimation, honest evaluation, and constrained optimization — not in an assumed ML component.

## 13. Recommendation for the Next Phase

Do not attempt vendor-demand ML. Proceed instead to formalize the **Demand Intelligence Architecture (Section 10)** as an actual system module specification (building on Phase 5A's "Data Quality Auditor" / "Model/Method Selector" module definitions, now extended to cover the cold-start and limited-history estimators this phase defines) — still without writing frontend/backend code, per this project's ongoing scope discipline. If real vendor survey/diary data collection is later attempted (per Section 4's restated plan), a subsequent phase should audit *that* data with the same rigor Phases 3A.5/3A.6 applied to the Potato/Tomato datasets before any estimation method is trusted — not assume the plan's projected scale will materialize as designed.

---

**Files produced by this phase:**
- This report.
- `reports/vendor_data_collection_template.md` (companion collection template).

**Files read but not modified:** `research/phase1c_data_feasibility_audit.md`, `research/phase3_system_architecture.md`, `research/phase3a1_ml_candidate_data_audit.md`, `reports/phase5a_research_findings_and_system_policy.md`, and every prior report/script from Phases 3A.1–4C. No dataset was modified. No model was trained. No synthetic dataset was generated.
