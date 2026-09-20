// UI-3 -- reuses the EXISTING MetricCard (results/MetricCard.jsx,
// unmodified) rather than a new KPI-card component -- exactly the "reuse
// where appropriate" instruction. Every value here comes from
// dashboardMetrics.js's buildDashboardMetrics(), itself built only from
// real, already-fetched run data -- no field is ever fabricated. A metric
// that cannot be reliably computed yet (no run has produced a selected
// group so far) shows "—" with an explanatory hint, never a misleading
// "₹0.00".

import MetricCard from "../results/MetricCard";
import { formatCurrency } from "../results/resultHelpers";

function KPISection({ metrics }) {
  return (
    <div className="value-grid">
      <MetricCard label="Total Analyses" value={String(metrics.totalAnalyses)} />
      <MetricCard
        label="Total Expected Savings"
        value={metrics.hasSavingsData ? formatCurrency(metrics.totalSavings) : "—"}
        tone={metrics.hasSavingsData ? "emphasis" : "default"}
        hint={metrics.hasSavingsData ? undefined : "Available after a group is selected"}
      />
      <MetricCard label="Vendors Evaluated" value={String(metrics.totalVendorsEvaluated)} />
      <MetricCard label="Collaborative Groups" value={String(metrics.totalSelectedGroups)} />
    </div>
  );
}

export default KPISection;
