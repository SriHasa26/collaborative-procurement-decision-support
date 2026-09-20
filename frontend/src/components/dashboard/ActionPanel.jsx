// UI-3 -- a legitimate CTA panel, not a fabricated alert/recommendation.
// UI-7 -- adds one more legitimate, real link ("View Insights", now that
// /insights is a real working page) alongside the existing primary CTA --
// completing this phase's own "Dashboard -> Insights -> History ->
// Results" coherent-flow requirement without redesigning this panel.

import Button from "../common/Button";
import Card from "../common/Card";

function ActionPanel() {
  return (
    <Card variant="highlighted" className="dashboard-panel dashboard-action-panel">
      <p className="card-title">Find your next procurement opportunity</p>
      <p className="text-small">
        Compare vendors, identify compatible groups, and quantify the value of collaboration.
      </p>
      <div className="dashboard-action-panel-actions">
        <Button to="/analyze" variant="primary">
          Start New Analysis
        </Button>
        <Button to="/insights" variant="ghost">
          View Insights →
        </Button>
      </div>
    </Card>
  );
}

export default ActionPanel;
