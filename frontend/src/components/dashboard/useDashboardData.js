// UI-3 -- fetches the authenticated user's own run history through the
// EXISTING, centralized API client (api/procurementApi.js) -- no second
// fetch implementation, no raw fetch() call here. The browser continues
// sending the existing Authorization header exactly as client.js already
// does; this hook never reads, stores, or passes a user_id anywhere --
// GET /procurement/runs and GET /procurement/runs/{run_id} are both
// already scoped to the authenticated caller by the backend itself
// (Phase 8F/8G, unchanged), and are consumed here exactly as any other
// caller would.
//
// FETCH STRATEGY: one GET /procurement/runs call always happens first --
// its length is the true, authoritative "Total Analyses" count regardless
// of anything below. RunSummary (that list response) intentionally
// excludes input/result_json ("lightweight run history only" --
// backend/persistence/repository.py's own docstring), so it alone cannot
// produce savings/vendor/decision metrics. Rather than fetching every
// historical run individually (unbounded, and explicitly discouraged by
// this phase's own "avoid excessive API requests" instruction), full
// detail is fetched only for the MOST RECENT `MAX_DETAIL_FETCH` runs
// (the list is already newest-first) -- everything on this dashboard that
// depends on those details (KPIs, latest decision, network overview,
// savings analytics, recent analyses) is honestly derived from that
// bounded set, and DashboardPage.jsx labels aggregates accordingly
// whenever the true total exceeds the cap (see its own comment).
//
// `fetchData` never calls setState synchronously at its own top level --
// only inside its .then()/.catch() (the actual external-system-sync
// moment an effect is for). The initial useState value is already
// "loading", so the mount-triggered effect needs no separate synchronous
// reset; `reload()` (called from the retry button's onClick, a real user
// event) is the one place that resets to "loading" synchronously, per
// oxlint's react(set-state-in-effect) rule's own suggested fix.

import { useCallback, useEffect, useState } from "react";
import { getProcurementRun, getProcurementRuns } from "../../api/procurementApi";

export const MAX_DETAIL_FETCH = 20;

function describeError(error) {
  const message = error instanceof Error ? error.message : String(error);
  return message.startsWith("Unable to reach the backend")
    ? "Unable to connect to the analysis service. Please check that the backend is running and try again."
    : "We couldn't load your procurement data. Please try again.";
}

export function useDashboardData() {
  const [state, setState] = useState({
    status: "loading",
    summaries: [],
    storedRuns: [],
    error: "",
  });

  const fetchData = useCallback(() => {
    let cancelled = false;

    getProcurementRuns()
      .then(async (summaries) => {
        const toFetch = summaries.slice(0, MAX_DETAIL_FETCH);
        const storedRuns = await Promise.all(toFetch.map((summary) => getProcurementRun(summary.run_id)));
        if (!cancelled) {
          setState({ status: "success", summaries, storedRuns, error: "" });
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setState({ status: "error", summaries: [], storedRuns: [], error: describeError(error) });
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
