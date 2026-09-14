# Phase 5A — Research Findings Consolidation and System Decision Logic

**Date:** 2026-09-14
**Scope:** Convert the verified experimental findings from Phases 3A.1–4C into research-backed system requirements — a conceptual decision framework, not an implementation. No model is trained, tuned, or re-evaluated in this phase. No dataset is modified. No new forecasting experiment is run.
**Rule followed throughout:** every claim below traces to a specific, already-completed phase. Where this document proposes a numeric threshold for future implementation, it is explicitly marked as a **configurable policy parameter**, not a scientifically derived universal constant — because none of the prior phases derived one statistically, and this phase does not invent one now.

---

## 1. Consolidated Research Findings

### 1.1 Data Source Findings

| Source | Finding | Phase |
|---|---|---|
| data.gov.in "Current Daily Price" | Confirmed a same-day snapshot (1 unique date, 9,298 rows) — structurally incapable of supporting time-series work | 3A.2 |
| CEDA Agri-Market Data | Real, legitimate republisher of official mandi data; genuine daily historical records exist; backend intermittently returned HTTP 500/504 errors even on identical repeated requests | 3A.2, 3A.3 |
| Official Agmarknet 2.0 | Real official government mandi-level data; historical range documented back to 2021-01-01; automated report-generation endpoints are CAPTCHA-gated by design — this project did not attempt to bypass that control | 3A.3 |

### 1.2 Acquisition Failures (reported, not hidden)

- **CEDA Onion acquisition failed on every one of 7 attempts** (daily and monthly, district- and state-level) across two separate phases (3A.2, 3A.3) — a reproducible failure, not a fluke.
- **CEDA Tomato acquisition failed completely in the Phase 3A.4 controlled acquisition run** (6/6 real attempts: 5× HTTP 504, 1× connection failure), triggering the project's own anti-hammering stop rule.
- **CEDA Potato acquisition succeeded** in that same run: 7/7 chunks, 178 records, 2025-03-05 to 2025-09-07.
- Because CEDA failed for Tomato, **a human manually exported Tomato data from official Agmarknet** (solving the CAPTCHA themselves, as this project's own policy requires — no automated bypass was ever attempted).

### 1.3 Tomato Data-Quality Failure

- Market: **Bowenpally APMC** (genuine mandi-level data, matching this project's original Phase 1B/1C study site).
- Coverage: 2025-03-05 to 2025-08-31, **99 records**.
- **A 66-day consecutive blackout (2025-06-04 to 2025-08-08)** — Bowenpally is entirely absent from the source's July export and nearly absent from June's.
- Overall missing rate in the 187-day target window: **47.1%**.
- Decision (Phase 3A.6): **NOT READY** for full-window ML forecasting. Tomato was explicitly not treated as an equal ML experiment — it was carried forward instead as a **data-quality abstention case** (Section 2 below operationalizes this).

### 1.4 Potato Dataset Limitations

- Geographic level: **Hyderabad district-level — a geographic proxy, never Bowenpally-mandi-level.** This distinction is restated in every phase from 3A.5 onward and is restated again here.
- **178 real observations**, 2025-03-05 to 2025-09-07, **9 isolated single-day missing dates** (4.8%), **0 duplicates**.
- Decision (Phase 3A.6): **READY WITH LIMITATIONS.**

### 1.5 Forecasting Experiment Definition

- Target: `modal_price_rs_quintal`.
- Horizon: **next available observation**, not necessarily the next calendar day — formally $X(t) \to y(t+1)$, where $t+1$ is the next *recorded* observation index, not a calendar-date assumption (Phase 3A.7).
- Missing dates were **never interpolated, forward-filled, or fabricated** at any point in this project.

### 1.6 Feature Engineering

- Minimal: `lag_1_modal_price`. Extended: `lag_1`, `lag_2`, `lag_3`, `rolling_mean_3`, `rolling_std_3`, `day_of_week` (Phase 3A.8).
- Feature/target alignment was **independently re-verified twice** — once in Phase 3A.8 (against the row-construction logic) and again in Phase 4B (an independent recomputation from the raw source, 0 mismatches out of 175 rows).
- **No data leakage was detected** at any audited point (Phases 3A.8, 3A.9, 4A, 4B, 4C all re-confirmed this independently).

### 1.7 Baseline Results (validation)

Chronological 5-fold expanding-window validation (Phase 3A.9): **Persistence MAE = 241.43; Moving-Average-3 MAE = 189.84.** Moving-average-3 was the best baseline at validation, beating persistence in every one of 5 folds.

### 1.8 ML Validation Result

Three low-complexity model families were tested (Linear Regression, Ridge, shallow Decision Tree — Phase 4A). **Best validation configuration: Extended features + plain Linear Regression, mean MAE ≈ 147.54** — a ~22% improvement over moving-average-3's 189.84. Phase 4A/4B's own coefficient-stability audit found this improvement was **not** simply "the model learned strong market structure" — it reflected a **combination** of (a) partial regression toward the training-period mean (a sound strategy on a weakly-autocorrelated series), (b) a genuinely stable contribution from `lag_3` and `rolling_mean_3`, and (c) an **unstable, small-sample-driven `day_of_week` effect** (the `Sunday` coefficient shrank from +76 to +42–45 as more data was added across folds; `Thursday`'s coefficient outright flipped sign).

### 1.9 Final Test Result

The 35-row test set (2025-08-02 to 2025-09-06), untouched since Phase 3A.9, was evaluated **exactly once** in Phase 4C: **Persistence MAE = 89.76; Moving-Average-3 MAE = 73.17; Linear Regression MAE = 91.06.** Linear Regression was the **worst** of the three methods on test — even behind plain persistence.

### 1.10 Generalization Failure

The validation-stage ranking (LR ahead of moving-average-3 by +42.30 MAE) **reversed** on test (moving-average-3 ahead of LR by −17.88 MAE) — not a shrinking advantage, a sign flip. Error analysis (Phase 4C) found a clear **overprediction bias**: 28 of 35 predictions too high, only 7 too low, traced to a concrete, verified cause — the training-period target mean (₹1769.85) exceeded the test-period target mean (₹1711.79) by ₹58, and the model's mean-anchored predictions carried that stale, higher level into a test window where prices had actually settled lower.

### 1.11 Final Research Conclusion

> **"Simple baselines performed as well as or better than the selected ML model on the final test period."**

This is the project's honest, evidence-based conclusion. The final test set is now consumed and will not be re-evaluated. No further tuning of this model is permitted (Phase 4C, and reaffirmed here).

**Nothing in this consolidation hides a failure.** Onion's total acquisition failure, Tomato's 66-day blackout, and Linear Regression's generalization failure are all restated above exactly as the source phases reported them.

---

## 2. Data Quality Gate (Conceptual Design)

**Purpose:** before any forecast is attempted for a given commodity/geography series, the system must evaluate whether the available historical data actually supports forecasting — using the same dimensions Phase 3A.6 already applied by hand to Tomato and Potato.

**Conceptual output: `FORECAST_ALLOWED` or `FORECAST_ABSTAIN`.**

**Factors the gate must evaluate** (each grounded in a factor this project actually measured, not a new invention):

| Factor | What it measures | Evidence this project produced |
|---|---|---|
| Coverage | Fraction of the intended study window with a real observation | Tomato 52.9% vs. Potato 95.2% (Phase 3A.5/3A.6) |
| Longest consecutive gap | Length of the single worst missing-data blackout | Tomato 66 days vs. Potato 1 day (Phase 3A.6/3A.7) |
| Sufficient observations | Whether enough real rows exist for a chronological split with a meaningful held-out test window | Potato's 175-row common window supported a 105/35/35 split; Tomato's Segment A/B (82 and 17 observations respectively) did not (Phase 3A.6) |
| Geographic granularity | Whether the data's actual geographic level matches or can be honestly reconciled with the intended study site | Potato is district-level, a proxy for Bowenpally/Gaddiannaram, never equivalent to them (Section 3 below) |
| Source reliability | Whether the acquisition method itself is reproducible and consistent, not just whether data exists | CEDA's intermittent 500/504 failures (Phase 3A.2–3A.4) are a reliability signal distinct from data *content* quality |

**Tomato as the abstention illustration:** applying this gate's factors to Tomato's actual numbers (52.9% coverage, a 66-day consecutive gap, no single contiguous segment reaching a defensible size — Phase 3A.6, Section 5) would return `FORECAST_ABSTAIN`. This is not a hypothetical — it is a direct restatement of the decision Phase 3A.6 already made by manual analysis, now framed as what a systematic gate would have concluded automatically.

**On thresholds:** this project never derived a statistically validated numeric cutoff for "how much coverage is enough" or "how long a gap is too long." Phase 3A.7's own 90-calendar-day floor was itself explicitly borrowed, not derived, from Phase 3A.3's earlier informal judgment. **Any numeric threshold used in a future implementation of this gate (e.g., "abstain if coverage < X%" or "abstain if the longest gap exceeds Y days") must be marked as a configurable policy parameter, subject to revision, not a scientifically proven constant.** This document does not propose specific values for X or Y — doing so here would repeat the exact mistake this project has avoided throughout (Phase 3A.1 onward): stating a number with more confidence than the evidence supports.

## 3. Data Granularity Rule

**The system must represent every dataset's geographic level using exactly one of three states, and must never silently narrow `DISTRICT_LEVEL_PROXY` into a mandi-level claim:**

| State | Definition | Example from this project |
|---|---|---|
| `MANDI_LEVEL` | Data resolves to one specific, named market | Tomato — Bowenpally APMC (official Agmarknet manual export) |
| `DISTRICT_LEVEL_PROXY` | Data is an aggregate/average across an unspecified set of markets within a district, used as a stand-in for a specific mandi it cannot actually resolve to | Potato — Hyderabad district (CEDA) |
| `UNKNOWN_GRANULARITY` | The system cannot determine which of the above applies (e.g., an undocumented or newly-integrated source) | Not encountered in this project's actual data, but must exist as a state so an unverified future source is never defaulted into `MANDI_LEVEL` by omission |

**Binding rule, restated without exception: any forecast output derived from `DISTRICT_LEVEL_PROXY` data must carry that label explicitly in its output metadata (Section 6) — the system must never present a Hyderabad-district-level Potato forecast as if it described Bowenpally or Gaddiannaram prices.** This is not a stylistic preference; Phase 3A.5 through 4C each independently re-affirmed this exact distinction, and this document's job is to make it a structural rule the system cannot bypass, not merely a note a report-writer must remember to add.

## 4. Forecast Model Policy

**ML is not automatically preferred over simpler methods.** The policy is a decision among three conceptual outcomes:

- **`BASELINE`** — use a simple, parameter-free method (persistence or moving-average).
- **`ML_MODEL`** — use a trained model, only if it has cleared the evidence rule (Section 5).
- **`NO_FORECAST`** — equivalent to the Data Quality Gate's `FORECAST_ABSTAIN` (Section 2); no method is used because the data does not support one.

**For the current validated experiment (Potato, Hyderabad district-level, the exact scope of Phases 3A.7–4C): the preferred method is `BASELINE`, specifically Moving-Average-3.** Reason, stated exactly as the evidence supports and no further: **it achieved the best performance on the final, untouched test set (MAE 73.17, versus persistence's 89.76 and Linear Regression's 91.06 — Phase 4C).**

**This is not a universal claim.** Moving-Average-3 is the best *currently evidenced* method for *this* commodity, *this* geography, *this* six-month window, *this* feature set, and *this* test split. This document does not claim, and no prior phase supports claiming, that moving-average-3 is optimal for potato prices in general, for any other commodity, for a different time period, or for a different geographic level. A different dataset or a longer study window could change this conclusion, and any future re-evaluation must run as a **new**, independently-designed experiment — not a reopening of the Phase 4C test result, which is consumed.

## 5. Model Evidence Rule

**An ML model may only be promoted to `ML_MODEL` status if it satisfies both of the following, in order:**

1. **Validation improvement:** it must beat the strongest available baseline's mean MAE under chronological expanding-window validation (never a random split).
2. **Generalization:** it must then also demonstrate acceptable performance on a final, previously untouched test partition — evaluated exactly once, with no re-tuning permitted after that evaluation.

**Both conditions are necessary; neither alone is sufficient.** The current Linear Regression experiment satisfied condition 1 (147.54 vs. 189.84 at validation) but **failed condition 2** (91.06 vs. moving-average-3's 73.17 at test — Phase 4C, Section 12). **Therefore, per this rule applied honestly: current dataset → `BASELINE`.**

**No arbitrary improvement percentage is defined here as a passing threshold** (e.g., "ML must beat the baseline by at least N%") — Phase 3A.9/4A already declined to invent such a number, distinguishing *statistical* improvement (beating the baseline's MAE at all) from *practical* improvement (whether the margin matters for a real decision), and this document does not manufacture one retroactively. The rule above is a **procedure** (validate, then test, then decide), not a numeric bar.

## 6. Forecast Output Definition (Conceptual `ForecastResult`)

Every forecast — or abstention — the system produces should carry a structured result with these fields, populated honestly rather than optimistically:

| Field | Purpose | Example (Potato, current experiment) |
|---|---|---|
| `commodity` | What is being forecast | `"Potato"` |
| `geographic_level` | One of `MANDI_LEVEL` / `DISTRICT_LEVEL_PROXY` / `UNKNOWN_GRANULARITY` (Section 3) | `"DISTRICT_LEVEL_PROXY"` |
| `location` | The specific place the data actually describes | `"Hyderabad district, Telangana"` |
| `source` | Where the underlying data came from | `"CEDA"` |
| `historical_data_status` | A summary of coverage/gap findings (Section 2's gate inputs) | `"178/187 days (95.2%), max gap 1 day"` |
| `forecast_status` | `FORECAST_ALLOWED` or `ABSTAIN` | `"FORECAST_ALLOWED"` (Potato passed the gate) |
| `selected_method` | Which policy outcome was used (Section 4) | `"BASELINE — Moving-Average-3"` |
| `predicted_value` | The actual numeric forecast, **only if `forecast_status = FORECAST_ALLOWED`** | e.g. a ₹/quintal figure — **never fabricated if abstaining** |
| `confidence/uncertainty status` | An honest statement of how much to trust the number — this project's evidence supports only a qualitative statement (e.g., "validated against a single 35-observation test window; MAE ≈₹73/quintal historically"), not a calibrated probability interval, since none was derived in any phase | `"Point estimate only; historical test MAE ≈₹73/quintal; no calibrated confidence interval available"` |
| `limitations` | Carried forward, not omitted | `"District-level proxy, not mandi-specific; ~6 months of history; single 35-day test window"` |

**If `forecast_status = ABSTAIN`, `predicted_value` must be absent or null — never a fabricated number presented as a real estimate.** This directly operationalizes this project's strictest rule, carried through every phase since 3A.2.

## 7. Abstention Explanation

When the Data Quality Gate returns `FORECAST_ABSTAIN`, the system must state a concrete, evidence-based reason — not a generic "insufficient data" message. **Tomato is the documented example:**

> `forecast_status: ABSTAIN`
> `reason: "Insufficient temporal continuity — a 66-day consecutive data gap (2025-06-04 to 2025-08-08) affects the most relevant recent history; overall coverage is 52.9% of the intended study window, below what this project's own experiments (Potato, at 95.2% coverage) demonstrated was usable. Source: official Agmarknet manual export, Bowenpally APMC, Phase 3A.4/3A.5/3A.6."`

Other conceptual reasons this same structure should support, drawn directly from this project's own encountered failure modes (not hypothetical):
- **Insufficient historical coverage** (Tomato's 52.9%).
- **Long consecutive data gap** (Tomato's 66 days).
- **Unreliable source** (CEDA's intermittent 500/504 failures — relevant if a future commodity's *only* available source behaves this way consistently enough to undermine trust in what data it does return).
- **Insufficient observations for a chronological split** (Tomato's Segment A/B, 82 and 17 observations respectively — neither alone supported a defensible train/validation/test split).
- **Incompatible geographic granularity** (a hypothetical future case where only `UNKNOWN_GRANULARITY` data exists for a requested mandi, with no district-level fallback even available).

## 8. Current System Policy Table

| Condition | System Action |
|---|---|
| Coverage/continuity fails the Data Quality Gate (e.g., Tomato's 66-day blackout) | `ABSTAIN` |
| Data passes the gate but is `DISTRICT_LEVEL_PROXY`, not `MANDI_LEVEL` | Forecast, but label output explicitly as district-level and carry that limitation into every downstream use |
| A validated baseline outperforms every tested ML model on the final test | Use the baseline (`BASELINE`), not ML |
| An ML model beats validation but fails final-test generalization | Do not select ML for this dataset; revert to `BASELINE` |
| An ML model beats validation *and* final test (not yet observed in this project) | Would be eligible for `ML_MODEL` — no such case currently exists to point to |
| Source is real but access is CAPTCHA-gated for automation | Do not bypass; use manual, human-driven acquisition as a documented, non-automated fallback (as done for Tomato) |

**These are project-specific engineering policies derived from one set of experiments on one commodity pair over one six-month window — not universal scientific laws.** A different dataset, a different season, or a richer feature set could produce different evidence, and this table would then need to be re-derived from that new evidence, not assumed to still hold.

## 9. Research Contribution

**This project's legitimate contribution is not "we built an accurate price-forecasting AI."** It explicitly is not that — Phase 4C's own conclusion forecloses that claim.

**The legitimate contribution is: a research-backed decision framework that evaluates data quality and empirical forecasting performance *before* deciding whether to forecast, abstain, or select a baseline versus an ML method — and that, when tested end-to-end on real government/CEDA data for a real commodity, correctly identified a case (Tomato) where it should refuse to forecast, and correctly demonstrated, through a disciplined validation/test protocol, that a simple baseline should be preferred over a plausible-looking ML model whose validation-stage improvement did not survive contact with unseen data.**

**Distinguishing what belongs to each category, explicitly:**

| Category | What it is | Example from this project |
|---|---|---|
| **Experimental finding** | A specific, dataset-bound empirical result | "Moving-average-3 beat Linear Regression on this 35-row Potato test" |
| **Engineering design** | A general decision procedure motivated by, but not limited to, that finding | The Data Quality Gate, the Model Evidence Rule (validate-then-test), the abstention mechanism |
| **Future research** | Open questions this project surfaced but did not answer | Whether the `day_of_week` effect is real (never independently validated — Phase 3A.8/4B); whether a longer study window or true mandi-level data would change the model-vs-baseline ranking; whether CEDA's reliability improves over time |

## 10. Architecture Implications (Requirements Only — Not Implemented)

Translating the above into conceptual system modules — definitions only, per this phase's explicit scope:

1. **Data Acquisition Module** — must record, per source, its reliability history (e.g., CEDA's observed intermittent failures) and support both automated pulls and a documented manual-fallback path (as used for Tomato), never silently substituting one for the other without labeling which occurred.
2. **Data Quality Auditor** — implements the Data Quality Gate (Section 2): computes coverage, longest consecutive gap, and observation count against configurable policy parameters, and outputs `FORECAST_ALLOWED`/`FORECAST_ABSTAIN`.
3. **Granularity Validator** — implements the Data Granularity Rule (Section 3): tags every dataset `MANDI_LEVEL` / `DISTRICT_LEVEL_PROXY` / `UNKNOWN_GRANULARITY` and refuses to let that tag be dropped or upgraded downstream without new evidence.
4. **Forecasting Engine** — executes whichever method the Model/Method Selector chooses (baseline or ML), using the leakage-safe, chronologically-ordered feature construction this project's own scripts (Phase 3A.8 onward) already demonstrate is required.
5. **Model/Method Selector** — implements the Forecast Model Policy and Model Evidence Rule (Sections 4–5): runs the validate-then-test procedure and defaults to `BASELINE` unless both conditions are met.
6. **Abstention Engine** — triggered when the Data Quality Auditor returns `FORECAST_ABSTAIN`; ensures no `predicted_value` is ever produced in this state.
7. **Explanation Generator** — produces the human-readable reason accompanying every `ForecastResult`, whether allowed or abstained (Sections 6–7), always citing the specific factor(s) that drove the decision rather than a generic message.

**None of these modules is implemented in this phase.** This section defines what each must do, based on evidence this project actually produced, so that whichever phase eventually builds them is building to a specification grounded in real experimental results rather than an assumed "add ML here" design.

---

**Files produced by this phase:**
- This report.
- `reports/final_research_findings_summary.md` (companion summary document).

**Files read but not modified:** every report and script from Phases 3A.1 through 4C, and the research audits in `research/`. No dataset was modified. No model was trained, tuned, or re-evaluated.
