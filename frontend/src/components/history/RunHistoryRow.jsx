// UI-6 -- Section 6/7/8/9/10/11: one procurement run, presented as a
// polished row/card hybrid rather than a spreadsheet row. The ENTIRE row
// is one real, keyboard-accessible <button> (Section 20's "make the whole
// item comfortably tappable" -- no hover-only affordance, no dead click
// target). Every value comes from either the always-real RunSummary
// fields (commodity/created_at/run_status/run_id) or, when this run's
// full detail was actually fetched (useHistoryData.js's bounded
// enrichment), the real ProcurementRunResult -- decision, vendor count,
// and savings all honestly show "—" when detail is unavailable, never a
// guess.

import Badge from "../common/Badge";
import DecisionStateBadge from "../common/DecisionStateBadge";
import { formatCurrency, getPrimaryDecisionState } from "../results/resultHelpers";
import { getRunStatusMeta } from "../results/runStatusMeta";
import { formatRunTimestamp, shortenRunId } from "./historyHelpers";

function RunHistoryRow({ entry, onViewResults, isPending, isDisabled }) {
  const statusMeta = getRunStatusMeta(entry.run_status);
  const result = entry.detail?.result;
  const primaryDecisionState = result ? getPrimaryDecisionState(result) : null;
  const vendorCount = result?.total_vendors_submitted;
  const savings = primaryDecisionState ? result.final_selection.total_savings_rs : null;
  const detailUnavailable = !entry.detail;

  return (
    <li className={`run-history-row${isPending ? " is-pending" : ""}`}>
      <button
        type="button"
        className="card card-interactive run-history-row-button"
        onClick={() => onViewResults(entry)}
        disabled={isDisabled}
        aria-busy={isPending}
        aria-label={`View results for ${entry.commodity}, run on ${formatRunTimestamp(entry.created_at)}`}
      >
        <div className="run-history-row-primary">
          <p className="card-title">{entry.commodity}</p>
          <p className="text-small text-muted">
            {formatRunTimestamp(entry.created_at)}
            {entry.run_id && <span title={entry.run_id}> · {shortenRunId(entry.run_id)}</span>}
          </p>
        </div>

        <div className="run-history-row-decision">
          {primaryDecisionState ? (
            <DecisionStateBadge state={primaryDecisionState} />
          ) : (
            <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>
          )}
        </div>

        <div className="run-history-row-metric">
          <span className="text-small text-muted">Vendors</span>
          <span className="text-small">{vendorCount ?? "—"}</span>
        </div>

        <div className="run-history-row-metric run-history-row-savings-block">
          <span className="text-small text-muted">Expected savings</span>
          <span className={savings != null ? "run-history-row-savings" : "text-small text-muted"}>
            {savings != null ? formatCurrency(savings) : "—"}
          </span>
        </div>

        <span className="run-history-row-action" aria-hidden="true">
          {isPending ? "Loading…" : "View Decision →"}
        </span>
      </button>

      {detailUnavailable && (
        <p className="text-small text-muted run-history-row-note">Full detail not loaded for this run yet.</p>
      )}
    </li>
  );
}

export default RunHistoryRow;
