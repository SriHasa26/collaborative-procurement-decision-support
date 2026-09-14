"""
Phase 3A.5 - Raw dataset validation and consolidation.

Purpose
-------
Phase 3A.4 acquired real historical Potato data from CEDA (district-level,
Hyderabad) and specified a manual acquisition requirement for Tomato from
the official Agmarknet 2.0 portal. That manual export has now been done by
a human (monthly CSV files, March-August 2025, under
data/raw/agmarknet_official/). This script:

  1. Reads both raw sources AS-IS -- it never writes to anything under
     data/raw/. Raw files are read-only inputs.
  2. Parses the Agmarknet monthly CSV format (multi-market file, one
     "Market Name : X" section per market, no repeated header per section)
     and extracts ONLY the Bowenpally APMC rows.
  3. Validates both datasets against real, checkable criteria (duplicates,
     chronology, missing dates, min<=modal<=max, negative values, unit/
     commodity/market consistency) -- and reports violations rather than
     silently fixing them.
  4. Writes two processed CSVs under data/processed/, restricted to the
     common study window 2025-03-05 to 2025-09-07, with no invented values
     and no interpolated missing dates.
  5. Prints a validation summary covering both datasets.

Safe to re-run: every run reads the same immutable raw files and
deterministically overwrites only the two processed CSVs under
data/processed/ -- it never appends, never mutates raw inputs, and never
depends on its own previous output.
"""

import csv
import glob
import json
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_AGMARKNET_DIR = PROJECT_ROOT / "data" / "raw" / "agmarknet_official"
RAW_CEDA_DIR = PROJECT_ROOT / "data" / "raw" / "ceda"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

STUDY_START = date(2025, 3, 5)
STUDY_END = date(2025, 9, 7)
TARGET_MARKET = "Bowenpally"  # substring match against "Market Name : ..." lines
TARGET_DISTRICT = "Hyderabad"
TARGET_STATE = "Telangana"


# ---------------------------------------------------------------------------
# TOMATO -- Agmarknet official monthly CSV parsing
# ---------------------------------------------------------------------------

def parse_agmarknet_tomato_files():
    """Reads every tomato_2025_*.csv* file under data/raw/agmarknet_official/
    (read-only), extracts the Bowenpally APMC block from each, and returns
    (rows, per_file_report) without modifying any raw file."""
    files = sorted(glob.glob(str(RAW_AGMARKNET_DIR / "tomato_2025_*.csv*")))
    rows = []
    per_file_report = []

    for fpath in files:
        with open(fpath, encoding="utf-8-sig") as fh:
            lines = fh.readlines()

        header_idx = next((i for i, l in enumerate(lines) if l.startswith("Arrival Date")), None)
        header = [h.strip() for h in lines[header_idx].strip().split(",")] if header_idx is not None else None

        market_indices = [i for i, l in enumerate(lines)
                           if l.startswith("Market Name") or l.startswith('"Market Name')]
        markets_found = []
        for idx in market_indices:
            m = lines[idx].split(":", 1)[1].strip().strip('"').rstrip('"')
            markets_found.append(m)

        bow_idx = next((idx for idx in market_indices if TARGET_MARKET in lines[idx]), None)

        report = {
            "file": Path(fpath).name,
            "header": header,
            "markets_in_file": len(market_indices),
            "bowenpally_present": bow_idx is not None,
            "rows_extracted": 0,
        }

        if bow_idx is not None:
            later = [i for i in market_indices if i > bow_idx]
            end_idx = later[0] if later else len(lines)
            block = [l.strip() for l in lines[bow_idx + 1:end_idx] if l.strip()]
            for raw_line in block:
                parts = next(csv.reader([raw_line]))
                rows.append({"raw_line": raw_line, "fields": parts, "file": Path(fpath).name})
            report["rows_extracted"] = len(block)

        per_file_report.append(report)

    return rows, per_file_report


def validate_and_build_tomato(rows):
    """Parses raw field lists into typed records, validates them, and
    returns (valid_records, validation_notes) -- validation issues are
    reported, not silently dropped or fixed, except where a record cannot
    be parsed at all (which is itself reported as a count, not hidden)."""
    notes = {
        "column_count_anomalies": [],
        "invalid_dates": [],
        "duplicate_dates": [],
        "min_modal_max_violations": [],
        "negative_values": [],
        "variety_values": Counter(),
    }
    parsed = []
    for r in rows:
        fields = r["fields"]
        if len(fields) != 6:
            notes["column_count_anomalies"].append({"file": r["file"], "raw": r["raw_line"]})
            continue
        date_str, arrival, variety, pmin, pmax, pmodal = fields
        try:
            d = datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            notes["invalid_dates"].append({"file": r["file"], "raw": r["raw_line"]})
            continue
        try:
            arrival_f, pmin_f, pmax_f, pmodal_f = float(arrival), float(pmin), float(pmax), float(pmodal)
        except ValueError:
            notes["column_count_anomalies"].append({"file": r["file"], "raw": r["raw_line"]})
            continue
        notes["variety_values"][variety] += 1
        if pmin_f < 0 or pmax_f < 0 or pmodal_f < 0 or arrival_f < 0:
            notes["negative_values"].append({"date": d.isoformat(), "file": r["file"]})
        if not (pmin_f <= pmodal_f <= pmax_f):
            notes["min_modal_max_violations"].append(
                {"date": d.isoformat(), "min": pmin_f, "modal": pmodal_f, "max": pmax_f, "file": r["file"]}
            )
        parsed.append({
            "date": d, "arrival_mt": arrival_f, "variety": variety,
            "min_price": pmin_f, "max_price": pmax_f, "modal_price": pmodal_f,
            "file": r["file"],
        })

    date_counts = Counter(p["date"] for p in parsed)
    notes["duplicate_dates"] = [d.isoformat() for d, c in date_counts.items() if c > 1]

    return parsed, notes


# ---------------------------------------------------------------------------
# POTATO -- CEDA raw JSON parsing
# ---------------------------------------------------------------------------

def parse_ceda_potato_files():
    files = sorted(glob.glob(str(RAW_CEDA_DIR / "potato_hyderabad_*.json")))
    records = []
    per_file_report = []
    for fpath in files:
        with open(fpath, encoding="utf-8") as fh:
            parsed = json.load(fh)
        recs = parsed.get("data", [])
        per_file_report.append({"file": Path(fpath).name, "records": len(recs)})
        for r in recs:
            records.append({**r, "file": Path(fpath).name})
    return records, per_file_report


def validate_potato(records):
    notes = {
        "duplicate_dates": [],
        "commodity_values": Counter(),
        "district_values": Counter(),
        "negative_values": [],
        "min_modal_max_violations": [],
    }
    date_counts = Counter(r["t"] for r in records)
    notes["duplicate_dates"] = [d for d, c in date_counts.items() if c > 1]
    for r in records:
        notes["commodity_values"][r["cmdty"]] += 1
        notes["district_values"][r["district"]] += 1
        if r["p_min"] < 0 or r["p_max"] < 0 or r["p_modal"] < 0:
            notes["negative_values"].append(r["t"])
        if not (r["p_min"] <= r["p_modal"] <= r["p_max"]):
            notes["min_modal_max_violations"].append(r["t"])
    return notes


# ---------------------------------------------------------------------------
# Missing-date analysis (reporting only -- no filling)
# ---------------------------------------------------------------------------

def missing_dates_in_window(present_dates, start, end):
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
    for m in missing_dates:
        if prev is None or (m - prev).days > 1:
            if prev is not None:
                gaps.append((gap_start, prev))
            gap_start = m
        prev = m
    if prev is not None:
        gaps.append((gap_start, prev))
    return gaps


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_tomato_csv(parsed_records):
    out_path = PROCESSED_DIR / "tomato_bowenpally_daily.csv"
    in_window = sorted(
        (r for r in parsed_records if STUDY_START <= r["date"] <= STUDY_END),
        key=lambda r: r["date"],
    )
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "date", "commodity", "market", "district", "state", "variety",
            "arrival_mt", "min_price_rs_quintal", "max_price_rs_quintal",
            "modal_price_rs_quintal", "source",
        ])
        for r in in_window:
            writer.writerow([
                r["date"].isoformat(), "Tomato", "Bowenpally APMC", TARGET_DISTRICT, TARGET_STATE,
                r["variety"], r["arrival_mt"], r["min_price"], r["max_price"], r["modal_price"],
                "agmarknet_official",
            ])
    return out_path, in_window


def write_potato_csv(records):
    out_path = PROCESSED_DIR / "potato_hyderabad_daily.csv"
    in_window = sorted(
        (r for r in records if STUDY_START <= datetime.strptime(r["t"], "%Y-%m-%d").date() <= STUDY_END),
        key=lambda r: r["t"],
    )
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "date", "commodity", "geographic_level", "district", "state",
            "min_price_rs_quintal", "max_price_rs_quintal", "modal_price_rs_quintal", "source",
        ])
        for r in in_window:
            writer.writerow([
                r["t"], "Potato", "district", TARGET_DISTRICT, TARGET_STATE,
                r["p_min"], r["p_max"], r["p_modal"], "CEDA",
            ])
    return out_path, in_window


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Phase 3A.5: Raw dataset validation and consolidation ===")
    print(f"Study window: {STUDY_START} to {STUDY_END}\n")

    print("--- TOMATO (Bowenpally APMC, from official Agmarknet monthly CSVs) ---")
    raw_rows, file_report = parse_agmarknet_tomato_files()
    for r in file_report:
        print(f"  {r['file']}: markets_in_file={r['markets_in_file']} "
              f"bowenpally_present={r['bowenpally_present']} rows_extracted={r['rows_extracted']}")

    tomato_parsed, tomato_notes = validate_and_build_tomato(raw_rows)
    print(f"\n  Total Bowenpally rows parsed (all months, unrestricted): {len(tomato_parsed)}")
    print(f"  Column-count anomalies: {len(tomato_notes['column_count_anomalies'])}")
    print(f"  Invalid dates: {len(tomato_notes['invalid_dates'])}")
    print(f"  Duplicate dates: {tomato_notes['duplicate_dates']}")
    print(f"  min<=modal<=max violations: {len(tomato_notes['min_modal_max_violations'])}")
    print(f"  Negative values: {len(tomato_notes['negative_values'])}")
    print(f"  Variety values seen: {dict(tomato_notes['variety_values'])}")

    tomato_dates_all = [r["date"] for r in tomato_parsed]
    tomato_missing_window = missing_dates_in_window(
        [d for d in tomato_dates_all if STUDY_START <= d <= STUDY_END], STUDY_START, STUDY_END
    )
    print(f"\n  Missing dates within study window ({STUDY_START}..{STUDY_END}): "
          f"{len(tomato_missing_window)} of {(STUDY_END - STUDY_START).days + 1} calendar days")
    print("  Contiguous missing-date gaps:")
    for g_start, g_end in contiguous_gaps(tomato_missing_window):
        print(f"    {g_start} to {g_end} ({(g_end - g_start).days + 1} days)")

    tomato_out_path, tomato_in_window = write_tomato_csv(tomato_parsed)
    print(f"\n  Wrote {len(tomato_in_window)} records to {tomato_out_path}")

    print("\n--- POTATO (Hyderabad district-level proxy, from CEDA raw JSON) ---")
    print("  NOTE: this is DISTRICT-LEVEL data, used as a geographic proxy for Bowenpally/"
          "Gaddiannaram. It is NOT Bowenpally-mandi-level data and is not described as such.")
    potato_records, potato_file_report = parse_ceda_potato_files()
    for r in potato_file_report:
        print(f"  {r['file']}: records={r['records']}")

    potato_notes = validate_potato(potato_records)
    print(f"\n  Total records (all files): {len(potato_records)}")
    print(f"  Duplicate dates: {potato_notes['duplicate_dates']}")
    print(f"  Commodity values seen: {dict(potato_notes['commodity_values'])}")
    print(f"  District values seen: {dict(potato_notes['district_values'])}")
    print(f"  min<=modal<=max violations: {len(potato_notes['min_modal_max_violations'])}")
    print(f"  Negative values: {len(potato_notes['negative_values'])}")

    potato_dates_all = [datetime.strptime(r["t"], "%Y-%m-%d").date() for r in potato_records]
    potato_missing_window = missing_dates_in_window(
        [d for d in potato_dates_all if STUDY_START <= d <= STUDY_END], STUDY_START, STUDY_END
    )
    print(f"\n  Missing dates within study window: {len(potato_missing_window)} of "
          f"{(STUDY_END - STUDY_START).days + 1} calendar days")
    print(f"  Missing dates: {[d.isoformat() for d in potato_missing_window]}")

    potato_out_path, potato_in_window = write_potato_csv(potato_records)
    print(f"\n  Wrote {len(potato_in_window)} records to {potato_out_path}")

    print("\n=== Done. Raw files under data/raw/ were only read, never modified. ===")
