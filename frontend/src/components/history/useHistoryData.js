// UI-6 -- fetches the authenticated user's run history through the
// EXISTING, centralized API client (api/procurementApi.js) -- no new
// endpoint, no raw fetch() call, no user_id ever read/passed here (both
// GET /procurement/runs and GET /procurement/runs/{run_id} are already
// scoped to the caller by the backend itself, Phase 8F/8G, unchanged).
//
// FETCH STRATEGY (same shape as UI-3's useDashboardData.js, adapted for
// History's different purpose): GET /procurement/runs always returns
// EVERY one of the user's runs -- its length is the true, authoritative
// total (backend/persistence/repository.py's RunSummary carries no
// savings/vendor/decision fields at all -- "lightweight run history
// only," confirmed by reading the repository contract directly).
// Reusing the exact existing detail-retrieval mechanism
// (getProcurementRun, already used by the pre-UI-6 HistoryPage.jsx and by
// UI-3's dashboard) rather than inventing a second one, full detail is
// fetched for the most recent HISTORY_DETAIL_FETCH_LIMIT runs only, to
// avoid one History page load firing an unbounded number of requests --
// the backend itself has no pagination/limit on this list endpoint
// (confirmed by reading backend/api/routes/procurement.py's list_runs
// handler, which passes no limit), so an unbounded history would
// otherwise fetch detail for every run that has ever existed. Every run
// beyond the cap still appears in the list with its real, always-
// available summary fields (commodity/created_at/run_status) -- only its
// decision/vendor-count/savings honestly show "—" rather than being
// fabricated or silently hidden. A single failed detail fetch (e.g. a
// transient network blip on one row) is caught per-run and does not fail
// the whole page -- that one run simply falls back to "detail
// unavailable" alongside any run past the cap.
//
// `fetchData` never calls setState synchronously at its own top level --
// only inside its .then()/.catch(), matching useDashboardData.js's own
// documented oxlint(set-state-in-effect)-safe pattern; `reload()` (called
// only from the retry button's onClick, a real user event) is the one
// place that resets to "loading" synchronously.

import { useCallback, useEffect, useState } from "react";
import { getProcurementRun, getProcurementRuns } from "../../api/procurementApi";
import { describeHistoryLoadError } from "./historyHelpers";

export const HISTORY_DETAIL_FETCH_LIMIT = 30;

export function useHistoryData() {
  const [state, setState] = useState({
    status: "loading",
    entries: [],
    totalCount: 0,
    enrichedCount: 0,
    error: "",
  });

  const fetchData = useCallback(() => {
    let cancelled = false;

    getProcurementRuns()
      .then(async (summaries) => {
        const toEnrich = summaries.slice(0, HISTORY_DETAIL_FETCH_LIMIT);
        const details = await Promise.all(
          toEnrich.map((summary) => getProcurementRun(summary.run_id).catch(() => null))
        );
        const detailByRunId = new Map(details.filter(Boolean).map((detail) => [detail.run_id, detail]));
        const entries = summaries.map((summary) => ({
          ...summary,
          detail: detailByRunId.get(summary.run_id) ?? null,
        }));

        if (!cancelled) {
          setState({
            status: "success",
            entries,
            totalCount: summaries.length,
            enrichedCount: detailByRunId.size,
            error: "",
          });
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setState({ status: "error", entries: [], totalCount: 0, enrichedCount: 0, error: describeHistoryLoadError(error) });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => fetchData(), [fetchData]);

  const reload = useCallback(() => {
    setState((prev) => ({ ...prev, status: "loading", error: "" }));
    fetchData();
  }, [fetchData]);

  return { ...state, reload };
}
