"""
Phase 3A.4 - Controlled CEDA historical acquisition.

Purpose
-------
Phase 3A.2/3A.3 established that CEDA (agmarknet.ceda.ashoka.edu.in) is the
only source that has ever returned real, verifiable daily mandi price
records to an automated request for this project's target commodities
(Tomato, Potato), but that its /api/prices endpoint is intermittently
unreliable (HTTP 500 / nginx 504). This script attempts a CONTROLLED,
polite, small-chunk acquisition of a longer historical window for Tomato
and Potato at Telangana/Hyderabad (district-level -- see geographic-
granularity note below), logging every attempt honestly.

Geographic granularity (confirmed, not assumed)
------------------------------------------------
CEDA's /api/prices request body accepts only state_id, commodity_id,
district_id (confirmed from the portal's own client-side filter UI in
Phase 3A.2/3A.3 -- there is no market/mandi_id parameter anywhere in that
UI or in the request/response schema). Every response record carries
`district_id` and `district`, never a market or mandi name. This is
therefore DISTRICT-LEVEL data (classification B), used here as an explicit
geographic proxy for Bowenpally/Gaddiannaram (Phase 1B/1C's actual study
mandis, both of which sit inside Hyderabad district) -- NOT mandi-level
data. This proxy relationship is a real limitation, stated here and in the
report, not hidden.

Politeness / anti-hammering policy (all limits enforced in code, not just
described)
------------------------------------------------------------------------
- Each chunk gets at most MAX_RETRIES_PER_CHUNK attempts (default 3).
- Retries use exponential backoff (BASE_BACKOFF_SECONDS * 2**attempt),
  not immediate re-fire.
- A fixed DELAY_BETWEEN_CHUNKS_SECONDS pause is taken between chunks
  regardless of outcome.
- If CONSECUTIVE_FAILURE_STOP chunks in a row fully exhaust their retries
  for a given commodity, that commodity's remaining chunks are skipped
  entirely and the run moves on -- this script does not keep hammering a
  commodity that has demonstrated it is currently unreachable.
- Nothing is fabricated on failure. A failed chunk produces no file and is
  logged as a failure, full stop.
"""

import json
import time
from datetime import date, timedelta
from pathlib import Path
from urllib import request as urlrequest
from urllib import error as urlerror

BASE = "https://agmarknet.ceda.ashoka.edu.in"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "ceda"
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Phase3A4-controlled-acquisition)",
}

# IDs confirmed live in Phase 3A.2 (never guessed): Telangana state, Hyderabad
# district. No market/mandi parameter exists on this endpoint (see module
# docstring).
TELANGANA_STATE_ID = 36
HYDERABAD_DISTRICT_ID = 536
DISTRICT_NAME = "hyderabad"
COMMODITY_IDS = {"tomato": 78, "potato": 24}  # Onion excluded per Phase 3A.4 scope

MAX_RETRIES_PER_CHUNK = 3
BASE_BACKOFF_SECONDS = 10
DELAY_BETWEEN_CHUNKS_SECONDS = 6
CONSECUTIVE_FAILURE_STOP = 2
REQUEST_TIMEOUT_SECONDS = 65


def _http_post(url, body, timeout):
    data = json.dumps(body).encode("utf-8")
    req = urlrequest.Request(url, data=data, headers=HEADERS, method="POST")
    start = time.time()
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), time.time() - start
    except urlerror.HTTPError as e:
        return e.code, e.read(), time.time() - start
    except Exception as e:  # timeout, connection reset, etc.
        return None, str(e).encode("utf-8"), time.time() - start


def fetch_chunk(commodity_name, commodity_id, start_date, end_date, log):
    """Attempts one date-range chunk with limited retries and exponential
    backoff. Returns (True, parsed_dict) on success, (False, None) on
    exhausted failure. Every attempt is appended to `log`."""
    body = {
        "state_id": TELANGANA_STATE_ID,
        "commodity_id": commodity_id,
        "district_id": HYDERABAD_DISTRICT_ID,
        "calculation_type": "d",
        "start_date": start_date,
        "end_date": end_date,
    }
    for attempt in range(1, MAX_RETRIES_PER_CHUNK + 1):
        status, raw, elapsed = _http_post(f"{BASE}/api/prices", body, REQUEST_TIMEOUT_SECONDS)
        entry = {
            "commodity": commodity_name,
            "start_date": start_date,
            "end_date": end_date,
            "attempt": attempt,
            "status": status,
            "elapsed_seconds": round(elapsed, 1),
            "bytes": len(raw),
        }
        ok = False
        if status == 200:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "data" in parsed and parsed["data"]:
                    ok = True
            except json.JSONDecodeError:
                pass
        entry["outcome"] = "success" if ok else "failed"
        if not ok:
            entry["error_body"] = raw.decode("utf-8", errors="replace")[:200]
        log.append(entry)
        print(f"    [{commodity_name}] {start_date}..{end_date} attempt {attempt}/{MAX_RETRIES_PER_CHUNK}: "
              f"status={status} elapsed={elapsed:.1f}s -> {entry['outcome']}")
        if ok:
            return True, parsed
        if attempt < MAX_RETRIES_PER_CHUNK:
            backoff = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            print(f"      backing off {backoff}s before retry...")
            time.sleep(backoff)
    return False, None


def save_raw(commodity_name, start_date, end_date, parsed):
    fname = f"{commodity_name}_{DISTRICT_NAME}_{start_date}_{end_date}.json"
    path = RAW_DIR / fname
    path.write_text(json.dumps(parsed), encoding="utf-8")
    print(f"      saved -> {path}")
    return path


def build_chunks():
    """Small test chunk first, then 30-day chunks walking backward from
    2025-09-01 (the last date already confirmed good in Phase 3A.2), so
    any early failure still preserves the most recent, most relevant
    history rather than losing it to a later, more speculative chunk."""
    chunks = [("test", date(2025, 9, 1), date(2025, 9, 7))]
    cursor_end = date(2025, 8, 31)
    for i in range(6):  # 6 x 30-day chunks -> ~180 additional days
        cursor_start = cursor_end - timedelta(days=29)
        chunks.append((f"30d-{i+1}", cursor_start, cursor_end))
        cursor_end = cursor_start - timedelta(days=1)
    return chunks


def run_acquisition():
    chunks = build_chunks()
    log = []
    results = {name: [] for name in COMMODITY_IDS}

    for commodity_name, commodity_id in COMMODITY_IDS.items():
        print(f"\n=== Acquiring {commodity_name.capitalize()} ===")
        consecutive_failures = 0
        for label, start_d, end_d in chunks:
            start_s, end_s = start_d.isoformat(), end_d.isoformat()
            print(f"  Chunk [{label}] {start_s}..{end_s}")
            ok, parsed = fetch_chunk(commodity_name, commodity_id, start_s, end_s, log)
            if ok:
                path = save_raw(commodity_name, start_s, end_s, parsed)
                results[commodity_name].append({
                    "label": label, "start": start_s, "end": end_s,
                    "records": len(parsed["data"]), "file": str(path),
                })
                consecutive_failures = 0
            else:
                results[commodity_name].append({
                    "label": label, "start": start_s, "end": end_s,
                    "records": 0, "file": None,
                })
                consecutive_failures += 1
                if consecutive_failures >= CONSECUTIVE_FAILURE_STOP:
                    print(f"  STOPPING {commodity_name}: {consecutive_failures} consecutive full-chunk "
                          f"failures -- further requests would just be hammering an unreliable endpoint.")
                    break
            time.sleep(DELAY_BETWEEN_CHUNKS_SECONDS)

    print("\n=== Acquisition summary ===")
    for commodity_name, chunk_results in results.items():
        succeeded = [c for c in chunk_results if c["records"] > 0]
        total_records = sum(c["records"] for c in succeeded)
        print(f"  {commodity_name}: {len(succeeded)}/{len(chunk_results)} chunks succeeded, "
              f"{total_records} total records")

    log_path = RAW_DIR / "_acquisition_attempt_log.json"
    log_path.write_text(json.dumps({"log": log, "results": results}, indent=2), encoding="utf-8")
    print(f"\nFull attempt log (all attempts, including failures) saved -> {log_path}")
    print("(This log file is acquisition metadata, not a price-data response; "
          "it is kept alongside the raw responses for audit purposes only.)")
    return results, log


if __name__ == "__main__":
    run_acquisition()
