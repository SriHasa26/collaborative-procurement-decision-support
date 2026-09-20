// UI-5 -- Section 3: "Key Decision Metrics". Replaces ResultsSummary.jsx
// (Phase 7E) -- the run-status Card that component used to show now lives
// in DecisionHero.jsx (the decision itself is the first thing the page
// should show, per this phase's own explicit brief), so this component is
// now purely the metric grid. Every value is a top-level
// ProcurementRunResult field (backend/models/run_contracts.py) or
// final_selection.total_savings_rs -- none is recalculated here.

import MetricCard from "./MetricCard";
import { formatCurrency, formatNumber } from "./resultHelpers";

function ResultMetricGrid({ result }) {
  const finalSelection = result.final_selection;
  const hasSelection = Boolean(finalSelection) && finalSelection.selected_results.length > 0;

  return (
    <section className="page-section" aria-labelledby="metrics-heading">
      <h2 id="metrics-heading" className="section-title">
        Key Decision Metrics
      </h2>
      <div className="metrics-grid">
        <MetricCard
          label="Expected Savings"
          value={hasSelection ? formatCurrency(finalSelection.total_savings_rs) : "—"}
          tone="emphasis"
          hint={hasSelection ? undefined : "Available after a group is selected"}
        />
        <MetricCard label="Vendors Submitted" value={formatNumber(result.total_vendors_submitted)} />
        <MetricCard label="Eligible Vendors" value={formatNumber(result.eligible_vendor_count)} />
        <MetricCard label="Abstained Vendors" value={formatNumber(result.abstained_vendor_count)} />
        <MetricCard label="Candidate Groups" value={formatNumber(result.candidate_group_count)} />
        <MetricCard label="Selected Groups" value={formatNumber(result.selected_group_count)} />
      </div>
    </section>
  );
}

export default ResultMetricGrid;
