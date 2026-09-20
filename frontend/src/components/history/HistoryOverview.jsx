// UI-6 -- Section 2: "History Overview". Deliberately minimal: only two
// facts are shown, and both are trivially real regardless of the
// enrichment cap (useHistoryData.js's HISTORY_DETAIL_FETCH_LIMIT) --
// `totalCount` is the length of the FULL, unbounded GET /procurement/runs
// response (never affected by how many runs got full detail), and the
// most recent run's commodity/date come from that same always-complete
// summary list. No decision/savings/vendor breakdown is shown here: any
// such aggregate would only be honestly computable across every run, and
// since detail is only fetched for a bounded subset, a partial breakdown
// would risk quietly misrepresenting the true totals -- a plain, correct
// count beats an impressive-looking but potentially incomplete one.

import { formatRunTimestamp } from "./historyHelpers";

function HistoryOverview({ totalCount, mostRecentEntry }) {
  return (
    <div className="history-overview">
      <div className="history-overview-stat">
        <span className="text-label">Total runs</span>
        <p className="text-metric">{totalCount}</p>
      </div>
      {mostRecentEntry && (
        <div className="history-overview-stat">
          <span className="text-label">Most recent</span>
          <p className="text-small">
            {mostRecentEntry.commodity} · {formatRunTimestamp(mostRecentEntry.created_at)}
          </p>
        </div>
      )}
    </div>
  );
}

export default HistoryOverview;
