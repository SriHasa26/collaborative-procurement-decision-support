// UI-7 -- Section 2: "Analytics Scope". Honestly states exactly what
// dataset every section below is drawn from -- `totalCount` is the true,
// unbounded GET /procurement/runs count (never affected by the
// enrichment cap); `enrichedCount` is how many of those actually have
// full detail loaded (useHistoryData.js's HISTORY_DETAIL_FETCH_LIMIT,
// UI-6). Never implies access to more history than the API actually
// returned.

import Card from "../common/Card";

function DataScopeBanner({ totalCount, enrichedCount }) {
  const allEnriched = enrichedCount >= totalCount;

  return (
    <Card className="insights-scope-banner">
      <span className="text-label">Analytics scope</span>
      {allEnriched ? (
        <p className="text-small">
          Based on all {totalCount} of your available procurement run{totalCount === 1 ? "" : "s"}.
        </p>
      ) : (
        <p className="text-small">
          Run activity and commodity counts below reflect all {totalCount} of your available procurement runs.
          Decision, savings, and vendor insights are based on your {enrichedCount} most recent runs with detailed
          result data available.
        </p>
      )}
    </Card>
  );
}

export default DataScopeBanner;
