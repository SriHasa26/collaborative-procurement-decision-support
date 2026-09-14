"""
Phase 3A.2 - CEDA Agri-Market Data Portal probe.

Purpose
-------
data.gov.in's "Current Daily Price of Various Commodities from Various Markets
(Mandi)" dataset was already verified (see verify_datagovin_snapshot below) to
contain only ONE unique Arrival_Date -- it is a same-day snapshot, not a time
series, and cannot be used for ML forecasting/trend-classification work.

This script probes the CEDA Agri-Market Data portal (Ashoka University),
https://agmarknet.ceda.ashoka.edu.in/, for a genuine daily historical
alternative. The portal's web UI hangs when loaded in a browser, so its
client-side JavaScript bundles were downloaded and inspected by hand to
recover the *real* endpoints the page itself calls (no endpoint below was
guessed):

    GET  /api/states
    GET  /api/commodities
    GET  /api/districts?state_id=<id>
    POST /api/prices      body: {state_id, commodity_id, district_id,
                                  calculation_type, start_date, end_date}
    POST /api/quantities  (same body shape as /api/prices)

`calculation_type` accepts "d" (daily), "m" (monthly) or "y" (yearly) --
confirmed from the same client bundle (options list: Daily/Monthly/Yearly).

Every call this script makes is a real HTTP request against the live portal.
Nothing below fabricates, simulates, or fills in data on failure -- a failed
request is reported as a failure, not papered over.

Empirical reliability note (see reports/phase3a2_historical_data_verification.md
for the full log): across manual testing on 2026-09-13, this backend answered
some requests in ~10-13s and failed others (HTTP 500 "Error accessing the
prices from the database", or an nginx 504 Gateway Time-out at ~60s) for the
exact same payload retried moments later. Onion (commodity_id=23) for
Telangana/Hyderabad failed on every one of 7 attempts (daily and monthly,
district-level and state-level). Tomato and Potato each succeeded once out of
several attempts. This script's retry logic and result reporting reflect that
reality rather than hiding it.
"""

import csv
import json
import sys
import time
from pathlib import Path
from urllib import request as urlrequest
from urllib import error as urlerror

BASE = "https://agmarknet.ceda.ashoka.edu.in"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "ceda"
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Phase3A2-research-probe)",
}

# IDs confirmed live from /api/states, /api/districts, /api/commodities --
# not guessed.
TELANGANA_STATE_ID = 36
HYDERABAD_DISTRICT_ID = 536
COMMODITY_IDS = {"Tomato": 78, "Onion": 23, "Potato": 24}


def _http(url, method="GET", body=None, timeout=65):
    """Single real HTTP call. Returns (status_code, raw_bytes, elapsed_seconds)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urlrequest.Request(url, data=data, headers=HEADERS, method=method)
    start = time.time()
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), time.time() - start
    except urlerror.HTTPError as e:
        return e.code, e.read(), time.time() - start
    except Exception as e:  # timeout, connection reset, etc.
        return None, str(e).encode("utf-8"), time.time() - start


def fetch_with_retries(url, method="GET", body=None, attempts=3, timeout=65):
    """Retries a real request up to `attempts` times. Never invents a result;
    returns the last failure verbatim if every attempt fails."""
    last = None
    for i in range(1, attempts + 1):
        status, raw, elapsed = _http(url, method=method, body=body, timeout=timeout)
        print(f"    attempt {i}/{attempts}: status={status} elapsed={elapsed:.1f}s bytes={len(raw)}")
        if status == 200:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "data" in parsed:
                    return True, raw, parsed
            except json.JSONDecodeError:
                pass
        last = (status, raw)
    return False, last[1], None


def save_raw(filename, raw_bytes):
    path = RAW_DIR / filename
    path.write_bytes(raw_bytes)
    print(f"    saved raw response -> {path}")
    return path


def probe_reference_data():
    """Fetch states / districts / commodities. Confirms IDs used below are real."""
    results = {}

    print("\n[1] GET /api/states")
    ok, raw, parsed = fetch_with_retries(f"{BASE}/api/states")
    if ok:
        save_raw("ceda_states_reference.json", raw)
        results["states"] = parsed["data"]
        telangana = [s for s in parsed["data"] if s["census_state_name"] == "Telangana"]
        print(f"    Telangana census_state_id = {telangana[0]['census_state_id'] if telangana else 'NOT FOUND'}")
    else:
        print("    FAILED -- all attempts errored. See raw bytes above.")
        results["states"] = None

    print("\n[2] GET /api/commodities")
    ok, raw, parsed = fetch_with_retries(f"{BASE}/api/commodities")
    if ok:
        save_raw("ceda_commodities_reference_full.json", raw)
        results["commodities"] = parsed["data"]
        for name, cid in COMMODITY_IDS.items():
            match = [c for c in parsed["data"] if c["commodity_id"] == cid and c["commodity_disp_name"] == name]
            print(f"    {name} (id {cid}): {'confirmed' if match else 'ID MISMATCH -- do not trust hardcoded id'}")
    else:
        print("    FAILED -- all attempts errored.")
        results["commodities"] = None

    print(f"\n[3] GET /api/districts?state_id={TELANGANA_STATE_ID} (Telangana)")
    ok, raw, parsed = fetch_with_retries(f"{BASE}/api/districts?state_id={TELANGANA_STATE_ID}")
    if ok:
        save_raw("ceda_telangana_districts_reference.json", raw)
        results["districts"] = parsed["data"]
        hyd = [d for d in parsed["data"] if d["census_district_id"] == HYDERABAD_DISTRICT_ID]
        print(f"    Hyderabad district_id {HYDERABAD_DISTRICT_ID}: {'confirmed' if hyd else 'MISMATCH'}")
    else:
        print("    FAILED -- all attempts errored.")
        results["districts"] = None

    return results


def probe_price_history(commodity_name, commodity_id, start_date, end_date, calculation_type="d"):
    """POST /api/prices for one commodity at Telangana/Hyderabad. Real request,
    no synthetic fallback. Returns parsed dict on success, None on failure."""
    label = f"{commodity_name} ({calculation_type}, {start_date}..{end_date})"
    print(f"\n[prices] {label}")
    body = {
        "state_id": TELANGANA_STATE_ID,
        "commodity_id": commodity_id,
        "district_id": HYDERABAD_DISTRICT_ID,
        "calculation_type": calculation_type,
        "start_date": start_date,
        "end_date": end_date,
    }
    ok, raw, parsed = fetch_with_retries(f"{BASE}/api/prices", method="POST", body=body, attempts=3)
    if ok:
        fname = f"ceda_telangana_hyderabad_{commodity_name.lower()}_{calculation_type}_{start_date.replace('-','')}_{end_date.replace('-','')}.json"
        save_raw(fname, raw)
        return parsed
    print(f"    FAILED for {label} after retries -- reporting as unavailable, NOT fabricating data.")
    return None


def verify_datagovin_snapshot():
    """Re-verifies the already-downloaded data.gov.in snapshot's unique-date
    count, so this report's headline claim is checked against the file, not
    just repeated from memory."""
    path = Path(__file__).resolve().parent.parent / "data" / "raw" / "agmarknet_current_snapshot_2026-09-13.csv.csv"
    if not path.exists():
        print(f"data.gov.in snapshot not found at {path}")
        return None
    dates, rows = set(), 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows += 1
            dates.add(row.get("Arrival_Date"))
    print(f"data.gov.in snapshot: {rows} rows, unique Arrival_Date values = {sorted(dates)}")
    return {"rows": rows, "unique_dates": sorted(dates)}


def summarize(parsed, label):
    if not parsed or not parsed.get("data"):
        print(f"  {label}: NO DATA")
        return
    records = parsed["data"]
    dates = sorted({r["t"] for r in records})
    markets = sorted({r.get("district") for r in records})
    print(f"  {label}: {len(records)} records | date range {dates[0]}..{dates[-1]} | "
          f"{len(dates)} unique dates | markets/districts: {markets} | "
          f"fields: {sorted(records[0].keys())}")


if __name__ == "__main__":
    print("=== Phase 3A.2: data.gov.in snapshot re-check ===")
    verify_datagovin_snapshot()

    print("\n=== Phase 3A.2: CEDA portal endpoint probe (Telangana / Tomato, Onion, Potato) ===")
    probe_reference_data()

    sample_range = ("2025-09-01", "2025-09-07")
    results = {}
    for name, cid in COMMODITY_IDS.items():
        results[name] = probe_price_history(name, cid, *sample_range, calculation_type="d")

    print("\n=== Summary ===")
    for name, parsed in results.items():
        summarize(parsed, name)

    print("\nDone. Raw responses saved under data/raw/ceda/. "
          "See reports/phase3a2_historical_data_verification.md for the full analysis.")
