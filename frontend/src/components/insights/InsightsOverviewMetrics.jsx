// UI-7 -- Section 3: Overview Metrics, reusing the existing MetricCard
// (results/MetricCard.jsx, unchanged since UI-1/UI-3). "Total Runs" is
// always the true, unbounded count; the other three are honestly capped
// to whatever the enrichment cap actually covered, each carrying a real
// hint explaining that scope rather than silently presenting a partial
// number as complete.

import MetricCard from "../results/MetricCard";
import { formatCurrency, formatNumber } from "../results/resultHelpers";

function InsightsOverviewMetrics({ totalCount, savingsSummary, buyTogetherCount, consideredCount, vendorCount, vendorConsideredRunCount }) {
  return (
    <section className="page-section" aria-labelledby="insights-overview-heading">
      <h2 id="insights-overview-heading" className="section-title">
        Overview
      </h2>
      <div className="metrics-grid">
        <MetricCard label="Total Runs" value={formatNumber(totalCount)} tone="emphasis" />

        <MetricCard
          label="Expected Savings"
          value={savingsSummary ? formatCurrency(savingsSummary.total) : "—"}
          hint={savingsSummary ? `Across ${savingsSummary.count} analyzed run(s)` : "No analyzed run has a selected group yet"}
        />

        <MetricCard
          label="Buy Together Decisions"
          value={consideredCount > 0 ? formatNumber(buyTogetherCount) : "—"}
          hint={consideredCount > 0 ? `Of ${consideredCount} analyzed run(s)` : "No run detail available yet"}
        />

        <MetricCard
          label="Vendors Observed"
          value={vendorConsideredRunCount > 0 ? formatNumber(vendorCount) : "—"}
          hint={
            vendorConsideredRunCount > 0
              ? `Across ${vendorConsideredRunCount} run(s) with available detail`
              : "No run detail available yet"
          }
        />
      </div>
    </section>
  );
}

export default InsightsOverviewMetrics;
