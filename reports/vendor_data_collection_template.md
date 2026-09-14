# Vendor Data Collection Template

**Companion to:** `reports/phase5c_demand_data_and_ml_feasibility.md`
**Status:** Template only — no data has been collected using this template. Nothing in this document is real vendor data.
**Basis:** This template operationalizes the collection plan already designed in `research/phase1c_data_feasibility_audit.md` (Section 5–6 there); it does not redesign that plan. It restricts itself to the fields Phase 5C's feasibility audit judged actually necessary for demand estimation specifically — not every field Phase 1C's fuller vendor-profile survey could in principle collect.

---

## 1. Two Separate Instruments, Not One Form

Consistent with Phase 1C's hybrid design, this is **two** short instruments, not one long one:

1. **A one-time Vendor Profile Survey** (all participating vendors, ~5–10 minutes, spoken conversationally).
2. **A short Daily Demand Diary** (only the willing subset, one line per day, ~1 minute).

Combining these into a single long form would raise the burden on every vendor for the sake of the few who would complete a diary — Phase 1C already rejected that approach for exactly this reason.

## 2. Vendor Profile Survey (One-Time, All Vendors)

| Field | Purpose | Required? |
|---|---|---|
| `vendor_id` | Anonymous identifier, assigned at collection — never a name | Required |
| `vendor_category` | Cold-start peer grouping (tea stall / chaat / fruit cart / etc. — use a short fixed list, not free text, so categories are comparable across vendors) | Required |
| `commodities_used` | Which of this project's studied commodities (Tomato, Potato) this vendor buys | Required |
| `typical_quantity` (per commodity, in the vendor's own unit — bags, crates, "₹X worth") | The cold-start estimate input | Required |
| `purchase_frequency` | Daily / every 2–3 days / weekly — needed to interpret `typical_quantity` correctly | Required |
| `approximate_location` (coordinates, tied only to `vendor_id`) | Geographic grouping — not used for demand estimation itself | Required for the grouping engine, optional for demand estimation alone |

**Deliberately excluded from this template**, per Phase 5C's own critical-necessity review: `quantity_remaining` (unsold stock) and `payment_method`. Both are legitimate fields Phase 1C's broader survey could ask, but neither is required for a demand *estimate* specifically, and adding them here would lengthen the form without improving what this template exists to produce.

## 3. Daily Demand Diary (Willing Subset Only, 7 Days)

One row per commodity per day. A vendor who buys two studied commodities fills two rows per day.

| `date` | `vendor_id` | `commodity` | `quantity_purchased` | `quantity_used` |
|---|---|---|---|---|

**Column notes:**
- `date` — the actual calendar date of the entry. If a vendor skips a day, **leave that date's row absent** — do not backfill or estimate it. This directly follows this project's own standing rule (established for the Potato/Tomato price data and restated here): missing observations are recorded as missing, never silently filled.
- `quantity_purchased` and `quantity_used` — recorded in the vendor's own unit at the time of entry; converted to a common unit (kg) afterward using a documented conversion table, per Phase 1C's recommendation — the vendor is never asked to do this conversion themselves.

**`quantity_remaining` is optional, not required**, consistent with Section 2's necessity review — a diary-keeping vendor under time pressure should not be blocked from participating over an optional field.

## 4. Example Structure (Illustrative Only — Not Real Data)

```
date,vendor_id,commodity,quantity_purchased,quantity_used
2026-XX-XX,V001,Tomato,<vendor's own unit>,<vendor's own unit>
2026-XX-XX,V001,Potato,<vendor's own unit>,<vendor's own unit>
```

**This is a structural illustration, not a filled-in example with plausible-looking numbers.** No placeholder numeric value is given here, deliberately — a filled-in "example" with invented quantities risks being mistaken for, or copy-pasted into, a real dataset. Anyone using this template should populate it only with genuinely collected values.

## 5. What This Template Does Not Do

- It does not estimate sample size sufficiency for ML — see `phase5c_demand_data_and_ml_feasibility.md`, Section 5, for that analysis.
- It does not itself produce a demand prediction — collected data from this template feeds the estimation methods described in that report's Sections 6–7 (cold-start category averages, last-observed-value, short moving average), not a trained model.
- It is not, itself, a dataset. It is a blank structure. Any populated version of this template must be clearly separated from this document and labeled with its own collection date, vendor count, and completeness rate (per-vendor missing-day count), exactly as this project's price-data phases (3A.5/3A.6) labeled their own real datasets.

---

**Referenced by:** `reports/phase5c_demand_data_and_ml_feasibility.md`, Section 4.
**Built on:** `research/phase1c_data_feasibility_audit.md`, Sections 5–6 (survey/diary design) and Section 13 (K1–K7, known biases and mitigations — recall bias, unit inconsistency, missing data, small-sample bias, social-desirability bias, location privacy — all of which apply to any future use of this template and are not re-derived here).
