"""
Phase 3A.8 - Feature engineering and ML dataset construction (Potato only).

Purpose
-------
Phase 3A.7 formally defined the forecasting task: predict y(t+1) -- the
modal price at the NEXT AVAILABLE observation -- using only information
available at or before observation t, where observations are indexed by
their position in the chronologically-ordered dataset, not by calendar
date (178 observations, 2025-03-05 to 2025-09-07, 9 isolated missing
calendar dates never filled).

This script builds exactly two feature datasets on top of that definition:
  - a MINIMAL set (lag_1 only)
  - an EXTENDED set (lag_1, lag_2, lag_3, rolling_mean_3, rolling_std_3,
    day_of_week -- deliberately excluding "month", justified in the report)

It does NOT train any model. It does NOT touch Tomato data at all. It does
NOT modify data/raw/ or the existing data/processed/potato_hyderabad_daily.csv
-- it only reads that file and writes two NEW files.

Leakage discipline enforced by construction (not just by description):
  - every lag/rolling feature for predicting y(t+1) is computed using only
    y(1..t), i.e. observation indices at or before t -- never t+1 or later.
  - calendar features are derived from the CURRENT observation's date d_t
    (always known), never from the target's date d_(t+1) (which, in a real
    forward-looking deployment, is not knowable in advance given irregular
    reporting -- see the report's Section 6/8 discussion).
  - min_price/max_price on the TARGET row are never used as features for
    that row's target; any min/max-derived feature must itself be lagged.
"""

import csv
import statistics
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "potato_hyderabad_daily.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MINIMAL_OUT = PROCESSED_DIR / "potato_ml_minimal.csv"
EXTENDED_OUT = PROCESSED_DIR / "potato_ml_extended.csv"

ROLLING_WINDOW = 3  # justified in the report: larger windows cost more
                     # rows and smooth away exactly the volatility Phase
                     # 3A.7 already found meaningful (Section 4 there)


def load_dataset(path):
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["_date"] = datetime.strptime(r["date"], "%Y-%m-%d").date()
        r["_modal"] = float(r["modal_price_rs_quintal"])
        r["_min"] = float(r["min_price_rs_quintal"])
        r["_max"] = float(r["max_price_rs_quintal"])
    # Verify ordering rather than assume it -- this script refuses to
    # proceed on unordered input rather than silently re-sorting (re-
    # sorting would hide a real data problem instead of surfacing it).
    dates = [r["_date"] for r in rows]
    if not all(dates[i] <= dates[i + 1] for i in range(len(dates) - 1)):
        raise ValueError("Input dataset is not chronologically ordered -- refusing to proceed.")
    if len(set(dates)) != len(dates):
        raise ValueError("Duplicate dates detected in input dataset -- refusing to proceed.")
    return rows


def build_minimal_rows(rows):
    """X(t) -> y(t+1), features = {lag_1 = modal price at t}.
    t ranges 1..N-1 (0-indexed: i ranges 0..N-2), so every row uses only
    observation i (<= t) to predict observation i+1 (t+1). Zero look-ahead."""
    out = []
    for i in range(len(rows) - 1):
        cur, nxt = rows[i], rows[i + 1]
        out.append({
            "date": cur["date"],                     # the date the FEATURES are observed at (t)
            "target_date": nxt["date"],               # the date being predicted (t+1) -- kept for audit only
            "lag_1_modal_price": cur["_modal"],
            "target_modal_price_next_observation": nxt["_modal"],
        })
    return out


def build_extended_rows(rows):
    """X(t) -> y(t+1), features = {lag_1, lag_2, lag_3, rolling_mean_3,
    rolling_std_3, day_of_week_at_t}. Requires at least 3 prior observations
    (indices t-2, t-1, t) to exist before a row can be built, so the first
    usable t is index 2 (0-indexed), predicting index 3."""
    out = []
    for i in range(ROLLING_WINDOW - 1, len(rows) - 1):
        window = rows[i - ROLLING_WINDOW + 1: i + 1]  # observations (t-2, t-1, t) -- inclusive of t, never t+1
        assert len(window) == ROLLING_WINDOW
        window_modals = [r["_modal"] for r in window]
        cur, nxt = rows[i], rows[i + 1]

        # Explicit leakage guard: the rolling window's most recent member
        # must be `cur` (index t) and must never include `nxt` (index t+1).
        assert window[-1] is cur
        assert nxt not in window

        out.append({
            "date": cur["date"],
            "target_date": nxt["date"],
            "lag_1_modal_price": rows[i]["_modal"],
            "lag_2_modal_price": rows[i - 1]["_modal"],
            "lag_3_modal_price": rows[i - 2]["_modal"],
            "rolling_mean_3_modal_price": statistics.mean(window_modals),
            "rolling_std_3_modal_price": statistics.pstdev(window_modals),
            "day_of_week": cur["_date"].strftime("%A"),
            "target_modal_price_next_observation": nxt["_modal"],
        })
    return out


def verify_alignment(feature_rows, raw_rows, feature_key):
    """Explicit target-alignment audit: for each generated row, re-derive
    what the target SHOULD be by looking up the raw dataset directly, and
    confirm it matches exactly. This is not a style check -- it is a direct
    re-verification against the source rows, independent of the row-
    building logic above."""
    by_date = {r["date"]: r["_modal"] for r in raw_rows}
    date_list = [r["date"] for r in raw_rows]
    mismatches = []
    for row in feature_rows:
        t_date = row["date"]
        target_date = row["target_date"]
        t_idx = date_list.index(t_date)
        expected_target_date = date_list[t_idx + 1]
        expected_target_value = by_date[expected_target_date]
        if target_date != expected_target_date or row["target_modal_price_next_observation"] != expected_target_value:
            mismatches.append(row)
    return mismatches


def print_examples(feature_rows, n=3, label=""):
    print(f"  Example alignment rows ({label}):")
    for row in feature_rows[:n]:
        feat_str = {k: v for k, v in row.items() if k not in ("target_modal_price_next_observation",)}
        print(f"    X(t)@{row['date']} = {feat_str}  ->  y(t+1)@{row['target_date']} = "
              f"{row['target_modal_price_next_observation']}")


def correlation_matrix(feature_rows, fields):
    print("\n  Pairwise Pearson correlation (extended numeric features):")
    series = {f: [r[f] for r in feature_rows] for f in fields}
    for i, f1 in enumerate(fields):
        for f2 in fields[i + 1:]:
            r = pearson(series[f1], series[f2])
            print(f"    corr({f1}, {f2}) = {r:.3f}")


def pearson(a, b):
    n = len(a)
    ma, mb = statistics.mean(a), statistics.mean(b)
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    sa = (sum((x - ma) ** 2 for x in a)) ** 0.5
    sb = (sum((x - mb) ** 2 for x in b)) ** 0.5
    return cov / (sa * sb) if sa > 0 and sb > 0 else float("nan")


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})


if __name__ == "__main__":
    print("=== Phase 3A.8: Feature Engineering (Potato only, no modeling) ===\n")

    raw_rows = load_dataset(INPUT_CSV)
    print(f"Loaded {len(raw_rows)} raw observations from {INPUT_CSV.name} "
          f"({raw_rows[0]['date']} to {raw_rows[-1]['date']})")

    print("\n--- MINIMAL feature set (lag_1 only) ---")
    minimal_rows = build_minimal_rows(raw_rows)
    print(f"  Original observations: {len(raw_rows)}")
    print(f"  Rows lost to feature construction: {len(raw_rows) - 1 - len(minimal_rows)} "
          f"(expected 0 beyond the mandatory 1 lost to needing a 'next observation')")
    print(f"  Usable rows: {len(minimal_rows)}")
    mismatches = verify_alignment(minimal_rows, raw_rows, "minimal")
    print(f"  Target-alignment mismatches found: {len(mismatches)}")
    print_examples(minimal_rows, label="minimal")
    write_csv(
        MINIMAL_OUT, minimal_rows,
        ["date", "lag_1_modal_price", "target_modal_price_next_observation"],
    )
    print(f"  Wrote {len(minimal_rows)} rows -> {MINIMAL_OUT}")

    print("\n--- EXTENDED feature set (lag_1/2/3, rolling_mean_3, rolling_std_3, day_of_week) ---")
    extended_rows = build_extended_rows(raw_rows)
    rows_lost_to_lag_and_rolling = (len(raw_rows) - 1) - len(extended_rows)
    print(f"  Original observations: {len(raw_rows)}")
    print(f"  Rows lost to needing a 'next observation': 1")
    print(f"  Rows additionally lost to needing {ROLLING_WINDOW} prior observations "
          f"for lag_3/rolling window: {rows_lost_to_lag_and_rolling - 1}")
    print(f"  Usable rows: {len(extended_rows)}")
    mismatches = verify_alignment(extended_rows, raw_rows, "extended")
    print(f"  Target-alignment mismatches found: {len(mismatches)}")
    print_examples(extended_rows, label="extended")
    correlation_matrix(
        extended_rows,
        ["lag_1_modal_price", "lag_2_modal_price", "lag_3_modal_price",
         "rolling_mean_3_modal_price", "rolling_std_3_modal_price",
         "target_modal_price_next_observation"],
    )
    write_csv(
        EXTENDED_OUT, extended_rows,
        ["date", "lag_1_modal_price", "lag_2_modal_price", "lag_3_modal_price",
         "rolling_mean_3_modal_price", "rolling_std_3_modal_price", "day_of_week",
         "target_modal_price_next_observation"],
    )
    print(f"  Wrote {len(extended_rows)} rows -> {EXTENDED_OUT}")

    print("\n=== Done. potato_hyderabad_daily.csv was only read, never modified. "
          "Tomato data was never loaded. ===")
