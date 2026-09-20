// UI-3 -- real per-run savings history (dashboardMetrics.js's
// buildSavingsSeries -- only runs with an actual selected group, oldest
// first). With zero data points: an empty state, never a fabricated
// trend. With exactly one: a single meaningful figure ("no trend is
// manufactured from one point," per this phase's own instruction). With
// two or more: a small inline SVG bar chart -- no chart library added.

import Card from "../common/Card";
import EmptyState from "../common/EmptyState";
import { formatCurrency } from "../results/resultHelpers";

function SavingsAnalytics({ savingsSeries }) {
  if (savingsSeries.length === 0) {
    return (
      <Card className="dashboard-panel">
        <p className="text-label">Savings Analytics</p>
        <EmptyState
          icon="₹"
          title="No savings data yet"
          description="Expected savings from your analyses will be charted here once a group is selected."
        />
      </Card>
    );
  }

  if (savingsSeries.length === 1) {
    const only = savingsSeries[0];
    return (
      <Card className="dashboard-panel">
        <p className="text-label">Savings Analytics</p>
        <p className="text-small text-muted">One completed analysis with a selected group</p>
        <p className="metric-card-value dashboard-savings-single">{formatCurrency(only.savings)}</p>
        <p className="text-small">{only.commodity}</p>
      </Card>
    );
  }

  const max = Math.max(...savingsSeries.map((point) => point.savings), 1);

  return (
    <Card className="dashboard-panel">
      <p className="text-label">Savings Analytics</p>
      <p className="text-small text-muted">Expected savings across your {savingsSeries.length} most recent selected groups</p>
      <div className="savings-chart" role="img" aria-label={`Bar chart of savings across ${savingsSeries.length} analyses, ranging up to ${formatCurrency(max)}`}>
        {savingsSeries.map((point) => (
          <div key={point.runId} className="savings-chart-bar-wrapper">
            <div
              className="savings-chart-bar bar-grow-vertical"
              style={{ height: `${Math.max(6, Math.round((point.savings / max) * 100))}%` }}
              title={`${point.commodity}: ${formatCurrency(point.savings)}`}
            />
          </div>
        ))}
      </div>
      <p className="text-small text-muted">
        Latest: {formatCurrency(savingsSeries[savingsSeries.length - 1].savings)}
      </p>
    </Card>
  );
}

export default SavingsAnalytics;
