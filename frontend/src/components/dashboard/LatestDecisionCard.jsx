// UI-3 -- surfaces the user's most recent run with a selected group,
// reusing the EXISTING DecisionStateBadge (unchanged) and reading the
// state directly from that group's own `final_decision_state` (never
// assumed/hardcoded, even though a selected group is always
// BUY_TOGETHER by the selection logic's own definition). Real data only
// -- `latestSelectedRun` is either a real StoredRun-shaped object or
// null (rendered as an empty state, never fabricated).
//
// "View Decision" passes `state={{ result: ... }}` on the Link -- the
// EXACT same router-state hand-off AnalysisForm.jsx/HistoryPage.jsx
// already use to reach ResultsPage.jsx (which reads ONLY
// location.state.result and does not call the API itself). Button's `to`
// path already forwards extra props straight to react-router's <Link>,
// so no change to Button.jsx was needed for this.

import Button from "../common/Button";
import Card from "../common/Card";
import EmptyState from "../common/EmptyState";
import DecisionStateBadge from "../common/DecisionStateBadge";
import { formatCurrency } from "../results/resultHelpers";

function LatestDecisionCard({ latestSelectedRun }) {
  if (!latestSelectedRun) {
    return (
      <Card className="dashboard-panel">
        <p className="text-label">Latest Procurement Decision</p>
        <EmptyState
          icon="◇"
          title="No group has been selected yet"
          description="Once an analysis produces a Buy Together recommendation, it will appear here."
          actions={
            <Button to="/analyze" variant="primary">
              Start an Analysis
            </Button>
          }
        />
      </Card>
    );
  }

  const finalSelection = latestSelectedRun.result.final_selection;
  const primaryGroup = finalSelection.selected_results[0];

  return (
    <Card variant="elevated" className="dashboard-panel dashboard-decision-card">
      <p className="text-label">Latest Procurement Decision</p>
      <DecisionStateBadge state={primaryGroup.final_decision_state} />

      <div className="decision-preview-metrics">
        <div>
          <span className="text-metric">{latestSelectedRun.result.total_vendors_submitted}</span>
          <p className="text-small text-muted">Vendors</p>
        </div>
        <div>
          <span className="text-metric">{finalSelection.selected_results.length}</span>
          <p className="text-small text-muted">Selected group(s)</p>
        </div>
      </div>

      <div>
        <span className="text-label">Expected savings</span>
        <p className="metric-card-value">{formatCurrency(finalSelection.total_savings_rs)}</p>
      </div>

      <Button to="/results" state={{ result: latestSelectedRun.result }} variant="outline">
        View Decision →
      </Button>
    </Card>
  );
}

export default LatestDecisionCard;
