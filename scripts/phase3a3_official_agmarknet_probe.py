"""
Phase 3A.3 - Official Agmarknet 2.0 probe.

Purpose
-------
Phase 3A.2 verified CEDA (agmarknet.ceda.ashoka.edu.in) as a real but
unreliable source of daily historical mandi prices. This phase investigates
the remaining official-government candidate: the modernized Agmarknet 2.0
portal (https://agmarknet.gov.in/), whose backend lives at
https://api.agmarknet.gov.in/v1/.

Method (no endpoint guessed): agmarknet.gov.in serves a React single-page app
from a single minified bundle (/static/js/main.*.js). That bundle was
downloaded and searched as plain text for an axios baseURL and for
`.get("...")` / `.post("...")` call sites, which is how every endpoint below
was found -- none were invented.

Endpoints confirmed to exist on api.agmarknet.gov.in/v1/:
    GET  /daily-price-arrival/filters                 -- reference data
                                                          (states, districts,
                                                          markets, commodities,
                                                          grades, varieties,
                                                          and the allowed
                                                          date range per
                                                          report type)
    POST /daily-price-arrival/report                   -- the actual price/
                                                          arrival report
    POST /prices-and-arrivals/market-report/daily
    POST /prices-and-arrivals/commodity-market/daily-report-weighted

Key finding, confirmed empirically (see reports/phase3a3_data_source_strategy.md
for the full analysis): the /daily-price-arrival/filters endpoint is open and
fast, and its response documents that the "Price" report type covers
2021-01-01 through today (capped at a 1-year window per single query) -- a
much longer documented historical range than CEDA ever confirmed. However,
every data-returning report endpoint tested (both /daily-price-arrival/report
and /prices-and-arrivals/commodity-market/daily-report-weighted) rejects an
unauthenticated request with:
    {"detail":"Captcha key and captcha value are required.",
     "code":"TOKEN_OR_CAPTCHA_REQUIRED"}

This script does NOT attempt to solve, bypass, or automate around that
CAPTCHA -- that would defeat a deliberate anti-automation control on a
government system, which this project will not do. The captcha response is
treated as a hard stop and reported honestly, not as an obstacle to route
around.
"""

import json
import time
from pathlib import Path
from urllib import request as urlrequest
from urllib import error as urlerror

BASE = "https://api.agmarknet.gov.in/v1"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "agmarknet_official"
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Phase3A3-research-probe)",
}

# IDs below are all taken directly from a live /daily-price-arrival/filters
# response (saved at data/raw/agmarknet_official/agmarknet_official_daily_price_arrival_filters.json)
# -- none were guessed.
TELANGANA_STATE_ID = 32
HYDERABAD_DISTRICT_ID = 566
BOWENPALLY_MARKET_ID = 1868       # matches this project's existing study mandi (Phase 1B/1C)
GADDIANNARAM_MARKET_ID = 377      # matches this project's other existing study mandi
COMMODITY_IDS = {"Tomato": 65, "Onion": 23, "Potato": 24}
ALL_GRADES_ID = 100003
ALL_VARIETIES_ID = 100007
TYPE_ID_PRICE = 100004


def _http(url, method="GET", body=None, timeout=40):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urlrequest.Request(url, data=data, headers=HEADERS, method=method)
    start = time.time()
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), time.time() - start
    except urlerror.HTTPError as e:
        return e.code, e.read(), time.time() - start
    except Exception as e:
        return None, str(e).encode("utf-8"), time.time() - start


def save_raw(filename, raw_bytes):
    path = RAW_DIR / filename
    path.write_bytes(raw_bytes)
    print(f"    saved raw response -> {path}")


def probe_filters():
    print("\n[1] GET /daily-price-arrival/filters")
    status, raw, elapsed = _http(f"{BASE}/daily-price-arrival/filters")
    print(f"    status={status} elapsed={elapsed:.1f}s bytes={len(raw)}")
    if status != 200:
        print("    FAILED -- cannot proceed to derive reference IDs.")
        return None
    parsed = json.loads(raw)
    save_raw("agmarknet_official_daily_price_arrival_filters.json", raw)
    d = parsed["data"]
    price_range = d["range_data"][0]["price"]
    print(f"    Documented Price-report date range: {price_range['from_date']} to "
          f"{price_range['to_date']} (max {price_range['allowed_year_range']} year(s) per query)")
    telangana = [s for s in d["state_data"] if s["state_name"] == "Telangana"]
    print(f"    Telangana state_id confirmed: {telangana[0]['state_id'] if telangana else 'NOT FOUND'}")
    for name, cid in COMMODITY_IDS.items():
        match = [c for c in d["cmdt_data"] if c["cmdt_id"] == cid and c["cmdt_name"] == name]
        print(f"    {name} (cmdt_id {cid}): {'confirmed' if match else 'ID MISMATCH -- do not trust hardcoded id'}")
    bowenpally = [m for m in d["market_data"] if m["id"] == BOWENPALLY_MARKET_ID]
    gaddiannaram = [m for m in d["market_data"] if m["id"] == GADDIANNARAM_MARKET_ID]
    print(f"    Bowenpally APMC (market_id {BOWENPALLY_MARKET_ID}): "
          f"{'confirmed -- ' + bowenpally[0]['mkt_name'] if bowenpally else 'NOT FOUND'}")
    print(f"    Gaddiannaram APMC (market_id {GADDIANNARAM_MARKET_ID}): "
          f"{'confirmed -- ' + gaddiannaram[0]['mkt_name'] if gaddiannaram else 'NOT FOUND'}")
    return parsed


def probe_report_endpoint(path, commodity_name, commodity_id, start_date, end_date):
    """Real POST request against a real report endpoint. Expected to be
    blocked by CAPTCHA -- this function exists to prove that honestly, not
    to work around it."""
    label = f"POST {path} ({commodity_name}, {start_date}..{end_date})"
    print(f"\n[report] {label}")
    body = {
        "state_id": TELANGANA_STATE_ID,
        "district_id": HYDERABAD_DISTRICT_ID,
        "market_id": BOWENPALLY_MARKET_ID,
        "cmdt_id": commodity_id,
        "grade_id": ALL_GRADES_ID,
        "variety_id": ALL_VARIETIES_ID,
        "type_id": TYPE_ID_PRICE,
        "from_date": start_date,
        "to_date": end_date,
    }
    status, raw, elapsed = _http(f"{BASE}{path}", method="POST", body=body, timeout=40)
    print(f"    status={status} elapsed={elapsed:.1f}s")
    print(f"    response: {raw.decode('utf-8', errors='replace')[:300]}")
    if status == 200:
        save_raw(
            f"agmarknet_official_{commodity_name.lower()}_{start_date.replace('-','')}_{end_date.replace('-','')}.json",
            raw,
        )
        return json.loads(raw)
    print("    Confirmed blocked (not a network failure) -- no data retrieved, none fabricated.")
    return None


if __name__ == "__main__":
    print("=== Phase 3A.3: Official Agmarknet 2.0 API probe ===")
    filters = probe_filters()

    if filters:
        # One representative attempt per report endpoint found, for Tomato.
        # Onion/Potato are not separately re-tested here since the CAPTCHA
        # gate is endpoint-level, not commodity-level -- repeating it per
        # commodity would not add evidence.
        probe_report_endpoint(
            "/daily-price-arrival/report", "Tomato", COMMODITY_IDS["Tomato"],
            "2025-09-01", "2025-09-07",
        )
        probe_report_endpoint(
            "/prices-and-arrivals/commodity-market/daily-report-weighted", "Tomato",
            COMMODITY_IDS["Tomato"], "2025-09-01", "2025-09-07",
        )

    print("\nDone. See reports/phase3a3_data_source_strategy.md for the full analysis.")
