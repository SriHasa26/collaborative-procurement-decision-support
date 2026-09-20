// UI-7 -- Section 5: Savings Overview. "Expected" is used throughout,
// deliberately never "money saved"/"profit"/"realized savings" -- this
// system never tracks whether a recommended collaborative purchase was
// actually carried out, only what the decision engine computed it WOULD
// save (backend/models/decision_contracts.py's FinalSelectionResult.
// total_savings_rs). With exactly one analyzed run, Total/Average/Highest
// would all be the identical number restated three times -- Rule 5
// explicitly asks for a single value with "1 analyzed run" context
// instead of implying a comparison that does not exist yet.

import Card from "../common/Card";
import MetricCard from "../results/MetricCard";
import LimitedDataState from "./LimitedDataState";
import { formatCurrency } from "../results/resultHelpers";

function SavingsOverview({ savingsSummary }) {
  return (
    <section className="page-section" aria-labelledby="savings-overview-heading">
      <h2 id="savings-overview-heading" className="section-title">
        Expected Savings Overview
      </h2>

      {!savingsSummary && (
        <LimitedDataState
          title="Not enough historical data"
          description="Expected savings analytics require at least one analyzed run with a selected collaborative procurement group."
          availableCount={0}
        />
      )}

      {savingsSummary && savingsSummary.count === 1 && (
        <Card className="insights-savings-single">
          <span className="text-label">Expected savings (1 analyzed run)</span>
          <p className="text-metric insights-savings-single-value">{formatCurrency(savingsSummary.total)}</p>
          <p className="text-small text-muted">
            More historical runs are needed before a total, average, or highest figure would be meaningful.
          </p>
        </Card>
      )}

      {savingsSummary && savingsSummary.count >= 2 && (
        <div className="metrics-grid">
          <MetricCard label="Total Expected Savings" value={formatCurrency(savingsSummary.total)} tone="emphasis" />
          <MetricCard label="Average Expected Savings" value={formatCurrency(savingsSummary.average)} />
          <MetricCard label="Highest Expected Savings" value={formatCurrency(savingsSummary.highest)} />
        </div>
      )}
    </section>
  );
}

export default SavingsOverview;
