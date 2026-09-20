// UI-3 -- a richer "Recent Analyses" list than history/RunHistoryTable.jsx
// (left completely unchanged -- HistoryPage's own lightweight-summary-
// then-fetch-on-click flow is untouched). This can show vendor/savings
// figures directly because DashboardPage already fetched full detail for
// these runs (useDashboardData.js) -- no extra request per row. Reuses
// existing helpers (historyHelpers.js, runStatusMeta.js, resultHelpers.js)
// and the existing Badge/Card/Button/EmptyState components -- no
// duplicate formatting logic. Only a "View Analysis" action exists, per
// this phase's own "do not invent CRUD" instruction -- no
// delete/edit/duplicate.

import Badge from "../common/Badge";
import Button from "../common/Button";
import Card from "../common/Card";
import EmptyState from "../common/EmptyState";
import { formatRunTimestamp, shortenRunId } from "../history/historyHelpers";
import { formatCurrency } from "../results/resultHelpers";
import { getRunStatusMeta } from "../results/runStatusMeta";

function RecentAnalyses({ storedRuns, totalAnalyses }) {
  if (storedRuns.length === 0) {
    return (
      <Card className="dashboard-panel">
        <p className="text-label">Recent Analyses</p>
        <EmptyState
          icon="≡"
          title="No procurement analyses yet"
          description="Run your first analysis to start building your procurement intelligence history."
          actions={
            <Button to="/analyze" variant="primary">
              Start an Analysis
            </Button>
          }
        />
      </Card>
    );
  }

  return (
    <Card className="dashboard-panel">
      <div className="card-header-row">
        <p className="text-label">Recent Analyses</p>
        <Button to="/history" variant="ghost">
          View All →
        </Button>
      </div>

      <ul className="recent-analyses-list">
        {storedRuns.slice(0, 6).map((stored) => {
          const statusMeta = getRunStatusMeta(stored.run_status);
          const finalSelection = stored.result?.final_selection;
          const hasSelection = finalSelection && (finalSelection.selected_results?.length ?? 0) > 0;

          return (
            <li key={stored.run_id} className="recent-analysis-row">
              <div className="recent-analysis-main">
                <p className="card-title">{stored.commodity}</p>
                <p className="text-small text-muted" title={stored.run_id}>
                  {formatRunTimestamp(stored.created_at)} · {shortenRunId(stored.run_id)}
                </p>
              </div>

              <div className="recent-analysis-figures">
                <span className="text-small">{stored.result?.total_vendors_submitted ?? "—"} vendors</span>
                <span className="text-small">
                  {hasSelection ? formatCurrency(finalSelection.total_savings_rs) : "—"}
                </span>
                <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>
              </div>

              <Button to="/results" state={{ result: stored.result }} variant="outline">
                View Analysis →
              </Button>
            </li>
          );
        })}
      </ul>

      {totalAnalyses > storedRuns.length && (
        <p className="text-small text-muted">
          Showing your {storedRuns.length} most recent of {totalAnalyses} total analyses.
        </p>
      )}
    </Card>
  );
}

export default RecentAnalyses;
