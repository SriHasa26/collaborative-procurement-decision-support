"""
Phase 3A.7 - Forecasting task and experimental definition audit.

Purpose
-------
Phase 3A.6 decided Potato (Hyderabad district-level, CEDA) is the READY-WITH-
LIMITATIONS primary ML dataset, and Tomato is NOT READY for full-window
forecasting (66-day blackout). This script does NOT train anything and does
NOT engineer features. It only inspects the actual processed Potato dataset
and computes the descriptive evidence this phase's report (Sections 2-9) is
built on:

  - schema, row count, missing-value check within existing rows
  - chronological ordering and duplicate check
  - per-field descriptive statistics (mean, stdev, coefficient of variation,
    day-over-day volatility) for min/max/modal price, used to justify the
    target-variable decision on evidence rather than convention alone
  - the calendar-day gap distribution between CONSECUTIVE OBSERVATIONS (not
    consecutive calendar dates), which is exactly the fact needed to
    distinguish "next calendar day" from "next available observation" when
    defining the forecasting horizon

Reminder of what this script deliberately does NOT do: it does not modify
data/raw/ or data/processed/, does not create any lag/rolling/derived
feature, and does not fit or evaluate any model. It is read-only analysis
in support of a written problem definition.
"""

import csv
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POTATO_CSV = PROJECT_ROOT / "data" / "processed" / "potato_hyderabad_daily.csv"

PRICE_FIELDS = ["min_price_rs_quintal", "max_price_rs_quintal", "modal_price_rs_quintal"]


def load(path):
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["_date"] = datetime.strptime(r["date"], "%Y-%m-%d").date()
        for f in PRICE_FIELDS:
            r[f"_{f}"] = float(r[f])
    return rows


def inspect_schema(rows):
    print("=== Schema and basic inspection ===")
    print(f"Columns: {list(rows[0].keys() - {'_date', *[f'_{f}' for f in PRICE_FIELDS]})}")
    print(f"Row count: {len(rows)}")
    missing_fields = [
        r["date"] for r in rows
        if any(r[f].strip() == "" for f in PRICE_FIELDS)
    ]
    print(f"Rows with an empty price field (among the 178 that exist): {len(missing_fields)}")
    distinct = {col: set(r[col] for r in rows) for col in ("commodity", "geographic_level", "district", "state", "source")}
    for col, vals in distinct.items():
        print(f"  {col}: {vals}")


def check_chronology_and_duplicates(rows):
    print("\n=== Chronological ordering and duplicates ===")
    dates = [r["_date"] for r in rows]
    ascending = all(dates[i] <= dates[i + 1] for i in range(len(dates) - 1))
    counts = Counter(dates)
    dups = [d.isoformat() for d, c in counts.items() if c > 1]
    print(f"Strictly ascending by row order: {ascending}")
    print(f"Duplicate dates: {dups}")
    print(f"First date: {dates[0]} | Last date: {dates[-1]}")
    return dates


def price_field_statistics(rows):
    print("\n=== Price field descriptive statistics (evidence for target selection) ===")
    for field in PRICE_FIELDS:
        series = [r[f"_{field}"] for r in rows]
        mean = statistics.mean(series)
        stdev = statistics.stdev(series)
        cv = stdev / mean
        deltas = [abs(series[i + 1] - series[i]) for i in range(len(series) - 1)]
        mean_abs_delta = statistics.mean(deltas)
        print(f"  {field}: mean={mean:.1f} stdev={stdev:.1f} coefficient_of_variation={cv:.3f} "
              f"min={min(series):.1f} max={max(series):.1f} n_unique={len(set(series))} "
              f"mean_abs_day-over-day_delta={mean_abs_delta:.1f}")

    violations = sum(
        1 for r in rows
        if not (r["_min_price_rs_quintal"] <= r["_modal_price_rs_quintal"] <= r["_max_price_rs_quintal"])
    )
    negatives = sum(
        1 for r in rows if any(r[f"_{f}"] <= 0 for f in PRICE_FIELDS)
    )
    print(f"  min<=modal<=max violations: {violations}")
    print(f"  zero-or-negative price rows: {negatives}")


def observation_gap_distribution(dates):
    print("\n=== Gap between CONSECUTIVE OBSERVATIONS (not consecutive calendar dates) ===")
    gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    dist = Counter(gaps)
    print(f"Total consecutive observation pairs: {len(gaps)}")
    print(f"Distribution of day-gaps: {dict(sorted(dist.items()))}")
    same_day_next = sum(1 for g in gaps if g == 1)
    skipped = sum(1 for g in gaps if g > 1)
    print(f"Pairs where the next OBSERVATION is also the next CALENDAR day: {same_day_next} "
          f"({same_day_next / len(gaps):.1%})")
    print(f"Pairs where the next OBSERVATION skips at least one calendar day: {skipped} "
          f"({skipped / len(gaps):.1%})")
    return dist


if __name__ == "__main__":
    print("=== Phase 3A.7: Forecasting Task Audit (inspection only, no modeling) ===\n")
    rows = load(POTATO_CSV)
    inspect_schema(rows)
    dates = check_chronology_and_duplicates(rows)
    price_field_statistics(rows)
    observation_gap_distribution(dates)
    print("\n=== Done. No file was modified. No feature was engineered. No model was trained. ===")
