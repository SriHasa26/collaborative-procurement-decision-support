// Phase 7B -- page header (unchanged in substance).
// Phase 7F -- real run history: loads GET /procurement/runs on entry,
// lets the user retrieve one stored run's full result via
// GET /procurement/runs/{run_id}, and hands it to the EXISTING
// ResultsPage/dashboard (Phase 7E, redesigned in UI-5) via the SAME React
// Router navigation state mechanism Phase 7D already established for
// newly-created results -- no second results UI is created.
//
// UI-6 -- redesigned into a premium "Procurement Run History / Activity
// Center": a History Overview (real, always-accurate total-run-count +
// most-recent-run facts), a search/decision-filter toolbar, and a
// polished run list -- each run enriched with its real decision/vendor
// count/savings via useHistoryData.js's bounded detail-fetch strategy
// (see that file's own comment for exactly why and how it is bounded).
// The on-demand single-run fetch this page has always supported (Phase
// 7F) is preserved unchanged as the fallback for any run whose detail
// was not part of that bounded set.

import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getProcurementRun } from "../api/procurementApi";
import Button from "../components/common/Button";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import PageHeader from "../components/common/PageHeader";
import HistoryOverview from "../components/history/HistoryOverview";
import HistorySkeleton from "../components/history/HistorySkeleton";
import HistoryToolbar from "../components/history/HistoryToolbar";
import RunHistoryList from "../components/history/RunHistoryList";
import { filterHistoryEntries } from "../components/history/historyFilters";
import { describeRunRetrievalError } from "../components/history/historyHelpers";
import { useHistoryData } from "../components/history/useHistoryData";

function HistoryPage() {
  const { status, entries, totalCount, error, reload } = useHistoryData();
  const [searchQuery, setSearchQuery] = useState("");
  const [decisionFilter, setDecisionFilter] = useState("ALL");
  const [selection, setSelection] = useState({ runId: null, status: "idle", error: "" });
  const navigate = useNavigate();

  const hasActiveFilters = searchQuery.trim() !== "" || decisionFilter !== "ALL";

  const filteredEntries = useMemo(
    () => filterHistoryEntries(entries, { searchQuery, decisionFilter }),
    [entries, searchQuery, decisionFilter]
  );

  function handleClearFilters() {
    setSearchQuery("");
    setDecisionFilter("ALL");
  }

  async function handleViewResults(entry) {
    // Duplicate-click guard: while one run's detail is being fetched, no
    // other row can start a second request (every row is disabled while
    // isSelecting is true) -- unchanged from Phase 7F's own guard.
    if (selection.status === "loading") return;

    // UI-6 -- reuse detail already fetched by useHistoryData.js when
    // available, rather than re-requesting it (this run was almost
    // certainly enriched already, since History fetches detail for its
    // most recent HISTORY_DETAIL_FETCH_LIMIT runs) -- avoids a redundant
    // network round-trip and the loading flicker that would come with it.
    if (entry.detail) {
      navigate("/results", {
        state: { result: entry.detail.result, runId: entry.detail.run_id, createdAt: entry.detail.created_at },
      });
      return;
    }

    // Fallback: the exact, unchanged Phase 7F/UI-5 on-demand fetch, for a
    // run beyond the enrichment cap (or whose own detail fetch failed).
    setSelection({ runId: entry.run_id, status: "loading", error: "" });
    try {
      const stored = await getProcurementRun(entry.run_id);

      if (!stored || !stored.result || typeof stored.result.run_status !== "string") {
        throw new Error("The stored run response was missing expected data.");
      }

      navigate("/results", { state: { result: stored.result, runId: stored.run_id, createdAt: stored.created_at } });
    } catch (err) {
      setSelection({ runId: entry.run_id, status: "error", error: describeRunRetrievalError(err) });
    }
  }

  return (
    <>
      <PageHeader
        title="Procurement History"
        description="Review previous procurement analyses, decisions, and outcomes."
        actions={
          <Button to="/analyze" variant="primary">
            + New Analysis
          </Button>
        }
      />

      {status === "loading" && <HistorySkeleton />}

      {status === "error" && (
        <ErrorState
          title="Unable to load procurement history"
          description={error}
          actions={
            <>
              <Button type="button" variant="primary" onClick={reload}>
                Retry
              </Button>
              <Button to="/dashboard" variant="secondary">
                Back to Dashboard
              </Button>
            </>
          }
        />
      )}

      {status === "success" && totalCount === 0 && (
        <EmptyState
          icon="≡"
          title="No procurement runs yet"
          description="Your completed analyses will appear here."
          actions={
            <Button to="/analyze" variant="primary">
              Start Your First Analysis
            </Button>
          }
        />
      )}

      {status === "success" && totalCount > 0 && (
        <>
          <HistoryOverview totalCount={totalCount} mostRecentEntry={entries[0]} />

          <HistoryToolbar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            decisionFilter={decisionFilter}
            onDecisionFilterChange={setDecisionFilter}
            onClear={handleClearFilters}
            hasActiveFilters={hasActiveFilters}
          />

          {selection.status === "error" && (
            <ErrorState title="Unable to load this run" description={selection.error} />
          )}

          <RunHistoryList
            entries={filteredEntries}
            onViewResults={handleViewResults}
            pendingRunId={selection.runId}
            isSelecting={selection.status === "loading"}
            onClearFilters={handleClearFilters}
          />
        </>
      )}
    </>
  );
}

export default HistoryPage;
