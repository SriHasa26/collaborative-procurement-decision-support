# Final Research Findings Summary

**Project:** AI/ML-assisted bulk-buying coordination platform for Indian street vendors — the ML/forecasting research track
**Date:** 2026-09-14
**Status:** Research and experimentation complete through Phase 4C; this document is the project's consolidated, honest record of what was found, and Phase 5A's translation of those findings into system policy.

This document is intentionally short. It exists so a reader who reads nothing else in this project still gets the complete, undiluted picture — including the findings that did not go the way a "successful AI project" narrative would prefer.

---

## What Was Investigated

Whether real, verifiable historical mandi price data for Tomato, Onion, and Potato in Telangana could support a genuine, validated machine-learning forecasting component for this platform — and, if so, whether an ML model could actually outperform simple statistical baselines once tested honestly on data it had never seen.

## What Was Found, Commodity by Commodity

**Onion:** Never acquired. CEDA's API failed on all 7 attempts made across two phases, in every configuration tried (daily/monthly, district/state-level). Out of scope for all modeling work.

**Tomato:** Acquired manually from official Agmarknet (Bowenpally APMC — genuine mandi-level data) after CEDA's automated acquisition failed completely. The result contains a **66-day consecutive data blackout** (2025-06-04 to 2025-08-08) and 47.1% overall missing coverage. **Determined not ready for forecasting.** Retained instead as a worked example of when a system should refuse to forecast.

**Potato:** Acquired successfully from CEDA — but only at **Hyderabad district level**, an aggregate proxy, never equivalent to Bowenpally or Gaddiannaram mandi prices specifically. 178 real observations, 2025-03-05 to 2025-09-07, only 9 missing dates (all isolated single days). **Determined ready, with limitations, for a forecasting experiment.**

## The Forecasting Experiment and Its Result

A one-step-ahead forecast of Potato's modal price (predicting the *next available* observation, not necessarily the next calendar day) was built and evaluated through a disciplined pipeline: leakage-audited features, chronological expanding-window validation (never random splitting), two mandatory simple baselines, three low-complexity ML model families, and a single, final, untouched-until-the-end test evaluation.

| Stage | Best baseline (Moving-Average-3) | Best ML model (Linear Regression, extended features) |
|---|---|---|
| Validation (5-fold expanding window) | MAE 189.84 | **MAE 147.54** (≈22% better) |
| **Final untouched test** | **MAE 73.17** | MAE 91.06 (worse than the baseline, and worse than even naive persistence) |

**The ranking reversed between validation and the final test.** Diagnosis (not speculation — verified directly): the model's predictions were anchored toward the training period's average price (₹1769.85), which sat ₹58 above the test period's actual average (₹1711.79) — so the model systematically overpredicted 28 of 35 test observations.

## The Honest Conclusion

> **Simple baselines performed as well as or better than the selected ML model on the final test period.**

This is not a failure of the research process — it is the process working correctly. The entire point of holding out an untouched final test set was to find out whether the validation-stage improvement was real or illusory. It found out. The answer, on this data, is that it was not robust enough to survive contact with unseen observations.

## What This Project Actually Contributes

**Not:** "an accurate AI price-forecasting model." That claim is explicitly not supported by the evidence above, and this document does not make it.

**Instead:** a demonstrated, evidence-based decision framework — grounded in real acquisition attempts, real data-quality failures, and a real validate-then-test ML evaluation — for deciding, per commodity and per geography, whether a system should forecast, abstain, or fall back to a simple baseline. Tomato's blackout is a genuine, worked abstention case. Potato's validation-vs-test reversal is a genuine, worked case for why "beats a baseline in validation" must never be trusted alone.

## System Policy Derived From These Findings (see Phase 5A for full detail)

- **Data Quality Gate:** a series must show adequate coverage, no severe consecutive gap, and enough observations for a real chronological split before forecasting is attempted — otherwise the system must `ABSTAIN`, as it would for Tomato.
- **Geographic Granularity Rule:** every output must be labeled `MANDI_LEVEL`, `DISTRICT_LEVEL_PROXY`, or `UNKNOWN_GRANULARITY` — Potato is permanently `DISTRICT_LEVEL_PROXY`, never relabeled as Bowenpally-specific.
- **Model Evidence Rule:** an ML model is only used in place of a baseline if it beats the baseline in chronological validation **and** in a final, untouched test. Potato's Linear Regression failed the second condition, so the current policy is: **use Moving-Average-3, not ML, for this dataset.**
- **No fabrication under abstention:** when the system abstains, it produces no predicted value — only a stated, evidence-based reason.

**None of these policies is claimed as a universal law.** They are engineering decisions this project's own evidence currently supports, for this commodity, this geography, and this time window — explicitly open to revision if new evidence (a longer study period, true mandi-level Potato data, a different model class) changes the picture.

## What Remains Open

- Whether CEDA's reliability or Agmarknet's CAPTCHA situation changes over time (both were snapshots of one investigation period).
- Whether a longer historical window or genuine mandi-level Potato data would change the baseline-vs-ML ranking.
- Whether the `day_of_week` effect flagged (and never independently validated) in the Linear Regression model reflects anything real.
- Whether Tomato's 66-day blackout has a knowable cause, and whether a future manual acquisition could close it.

None of these questions is answered here. They are named so a future phase does not have to rediscover them.

---

**Companion document:** `reports/phase5a_research_findings_and_system_policy.md` (full findings consolidation, Data Quality Gate design, granularity rule, forecast model policy, model evidence rule, forecast output specification, abstention explanation design, system policy table, research contribution framing, and architecture implications).
