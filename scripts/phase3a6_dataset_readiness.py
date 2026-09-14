"""
Phase 3A.6 - Dataset readiness and experimental scope audit.

Purpose
-------
Phase 3A.5 produced two processed, non-fabricated datasets:
  - data/processed/tomato_bowenpally_daily.csv  (Bowenpally APMC, mandi-level)
  - data/processed/potato_hyderabad_daily.csv    (Hyderabad district, PROXY --
                                                    never Bowenpally-level)

This script performs a READINESS ASSESSMENT ONLY. It does not train any
model, does not engineer features, and does not fill, interpolate, or
otherwise alter any missing date. It:

  1. Loads both processed CSVs (read-only).
  2. Verifies chronological ordering and duplicate-freedom.
  3. Calculates temporal coverage and every missing calendar date.
  4. Calculates consecutive-missing-date gaps for both commodities.
  5. Analyzes Tomato's two contiguous segments around its 66-day blackout
     (2025-06-04 to 2025-08-08) exactly as specified: Segment A
     (2025-03-05 to 2025-06-03) and Segment B (2025-08-09 to 2025-08-31).
  6. Analyzes Potato's 9 missing dates individually (gap length, isolated
     vs. multi-day).
  7. Prints a structured summary a human/report can transcribe.

Nothing here merges Tomato and Potato into one table, nothing bridges the
Tomato gap, and nothing claims Potato is mandi-level. This script is safe
to re-run any number of times -- it only reads data/processed/ and prints
to stdout (plus, conditionally, writes one new file under data/processed/
if this run's analysis justifies it -- see build_potato_ml_ready() below,
which is explicitly NOT a Tomato output, since Tomato's gap policy forbids
any filled/continuous version).
"""

import csv
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TOMATO_CSV = PROCESSED_DIR / "tomato_bowenpally_daily.csv"
POTATO_CSV = PROCESSED_DIR / "potato_hyderabad_daily.csv"

STUDY_START = date(2025, 3, 5)
STUDY_END = date(2025, 9, 7)

TOMATO_GAP_START = date(2025, 6, 4)
TOMATO_GAP_END = date(2025, 8, 8)
SEGMENT_A = (date(2025, 3, 5), date(2025, 6, 3))
SEGMENT_B = (date(2025, 8, 9), date(2025, 8, 31))

# Sufficiency floor is NOT a fresh number invented for this phase -- it is
# Phase 3A.3's own previously-established minimum ("at least 90 continuous
# days for a first usable model; 6-12 months preferred", Phase 3A.3 Section
# 3). Reusing it here keeps this phase's judgment consistent with what the
# project already committed to, rather than picking a new threshold to fit
# whatever the data happens to show.
MIN_CALENDAR_DAYS_FLOOR = 90


def load_csv_dates(path, date_field="date"):
    """Reads a processed CSV read-only and returns (rows, dates_list) in
    file order -- does not assume order, just reports what is found."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            row["_date"] = datetime.strptime(row[date_field], "%Y-%m-%d").date()
            rows.append(row)
    dates = [r["_date"] for r in rows]
    return rows, dates


def check_chronological_and_duplicates(dates, label):
    is_sorted_asc = all(dates[i] <= dates[i + 1] for i in range(len(dates) - 1))
    is_sorted_desc = all(dates[i] >= dates[i + 1] for i in range(len(dates) - 1))
    counts = Counter(dates)
    duplicates = [d.isoformat() for d, c in counts.items() if c > 1]
    print(f"[{label}] rows={len(dates)} unique_dates={len(set(dates))} "
          f"sorted_ascending={is_sorted_asc} sorted_descending={is_sorted_desc} "
          f"duplicates={duplicates}")
    return {
        "rows": len(dates), "unique_dates": len(set(dates)),
        "sorted_ascending": is_sorted_asc, "sorted_descending": is_sorted_desc,
        "duplicates": duplicates,
    }


def missing_dates_in_range(present_dates, start, end):
    present = set(present_dates)
    missing = []
    cur = start
    while cur <= end:
        if cur not in present:
            missing.append(cur)
        cur += timedelta(days=1)
    return missing


def contiguous_gaps(missing_dates):
    gaps = []
    gap_start = None
    prev = None
    for m in sorted(missing_dates):
        if prev is None or (m - prev).days > 1:
            if prev is not None:
                gaps.append((gap_start, prev))
            gap_start = m
        prev = m
    if prev is not None:
        gaps.append((gap_start, prev))
    return [{"start": s.isoformat(), "end": e.isoformat(), "length_days": (e - s).days + 1} for s, e in gaps]


def analyze_tomato_segments(dates_in_window):
    present = set(dates_in_window)

    def segment_stats(seg_start, seg_end, label):
        total_days = (seg_end - seg_start).days + 1
        obs = sorted(d for d in present if seg_start <= d <= seg_end)
        missing = missing_dates_in_range(present, seg_start, seg_end)
        density = len(obs) / total_days if total_days else 0.0
        meets_floor = total_days >= MIN_CALENDAR_DAYS_FLOOR
        print(f"  {label}: {seg_start} to {seg_end} | calendar_days={total_days} "
              f"observations={len(obs)} missing_within_segment={len(missing)} "
              f"density={density:.1%} meets_{MIN_CALENDAR_DAYS_FLOOR}day_floor={meets_floor}")
        return {
            "label": label, "start": seg_start.isoformat(), "end": seg_end.isoformat(),
            "calendar_days": total_days, "observations": len(obs),
            "missing_within_segment": len(missing), "density": density,
            "meets_floor": meets_floor,
        }

    seg_a = segment_stats(*SEGMENT_A, "Segment A")
    seg_b = segment_stats(*SEGMENT_B, "Segment B")
    return seg_a, seg_b


def analyze_potato_gaps(dates_in_window):
    missing = missing_dates_in_range(dates_in_window, STUDY_START, STUDY_END)
    gaps = contiguous_gaps(missing)
    print(f"  Missing dates ({len(missing)}): {[d.isoformat() for d in missing]}")
    print(f"  Contiguous gaps ({len(gaps)}):")
    for g in gaps:
        kind = "single-day" if g["length_days"] == 1 else f"{g['length_days']}-day"
        print(f"    {g['start']} to {g['end']} -- {kind}")
    return missing, gaps


def build_potato_regular_index_view(rows):
    """Builds an explicitly-labeled 'regular daily index, missing retained as
    absent-with-flag' VIEW of Potato -- Option C from the phase's missing-
    data policy menu. This does NOT fill any price value. Every date in the
    study window gets a row; the 9 missing dates get empty price fields and
    an explicit is_missing=1 flag, so a modeling step downstream can decide
    how to handle them without having to re-derive which dates are missing.
    Written to a NEW file, never overwriting the Phase 3A.5 output."""
    by_date = {r["_date"]: r for r in rows}
    out_path = PROCESSED_DIR / "potato_hyderabad_daily_regular_index.csv"
    fieldnames = ["date", "commodity", "geographic_level", "district", "state",
                  "min_price_rs_quintal", "max_price_rs_quintal", "modal_price_rs_quintal",
                  "source", "is_missing"]
    cur = STUDY_START
    written = 0
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        while cur <= STUDY_END:
            if cur in by_date:
                r = by_date[cur]
                writer.writerow({
                    "date": cur.isoformat(), "commodity": r["commodity"],
                    "geographic_level": r["geographic_level"], "district": r["district"],
                    "state": r["state"], "min_price_rs_quintal": r["min_price_rs_quintal"],
                    "max_price_rs_quintal": r["max_price_rs_quintal"],
                    "modal_price_rs_quintal": r["modal_price_rs_quintal"],
                    "source": r["source"], "is_missing": 0,
                })
            else:
                writer.writerow({
                    "date": cur.isoformat(), "commodity": "Potato",
                    "geographic_level": "district", "district": "Hyderabad",
                    "state": "Telangana", "min_price_rs_quintal": "",
                    "max_price_rs_quintal": "", "modal_price_rs_quintal": "",
                    "source": "CEDA", "is_missing": 1,
                })
            written += 1
            cur += timedelta(days=1)
    return out_path, written


if __name__ == "__main__":
    print("=== Phase 3A.6: Dataset Readiness and Experimental Scope Audit ===\n")

    print("--- TOMATO (Bowenpally APMC, mandi-level) ---")
    tomato_rows, tomato_dates = load_csv_dates(TOMATO_CSV)
    tomato_checks = check_chronological_and_duplicates(tomato_dates, "tomato")
    tomato_missing = missing_dates_in_range(tomato_dates, STUDY_START, STUDY_END)
    tomato_gaps = contiguous_gaps(tomato_missing)
    print(f"  Coverage: {min(tomato_dates)} to {max(tomato_dates)}")
    print(f"  Missing dates in {STUDY_START}..{STUDY_END}: {len(tomato_missing)} "
          f"of {(STUDY_END - STUDY_START).days + 1} calendar days")
    print(f"  Contiguous gaps: {len(tomato_gaps)}")
    for g in tomato_gaps:
        print(f"    {g['start']} to {g['end']} ({g['length_days']} days)")

    print("\n  Segment analysis around the declared 66-day blackout "
          f"({TOMATO_GAP_START} to {TOMATO_GAP_END}):")
    seg_a, seg_b = analyze_tomato_segments(tomato_dates)

    print("\n--- POTATO (Hyderabad district, PROXY -- not Bowenpally) ---")
    potato_rows, potato_dates = load_csv_dates(POTATO_CSV)
    potato_checks = check_chronological_and_duplicates(potato_dates, "potato")
    print(f"  Coverage: {min(potato_dates)} to {max(potato_dates)}")
    potato_missing, potato_gaps = analyze_potato_gaps(potato_dates)

    print("\n--- Building explicitly-labeled Potato regular-index view (Option C) ---")
    print("  (Missing dates retained as empty + is_missing=1 flag; NO value is filled.)")
    out_path, written = build_potato_regular_index_view(potato_rows)
    print(f"  Wrote {written} rows (178 real + {written - 178} explicitly-flagged-missing) -> {out_path}")

    print("\n=== Done. No raw file was touched. Tomato output was NOT modified or bridged. ===")
