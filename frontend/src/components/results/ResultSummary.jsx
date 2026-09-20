// UI-5 -- Section 10: a compact, scannable "executive summary" near the
// bottom of the page, for a reader who wants the headline facts again
// without re-reading every section above. Reads the exact same real
// fields DecisionHero.jsx already reads -- this is a second, shorter
// PRESENTATION of the same data, never a second source of truth.

import Card from "../common/Card";
import DecisionStateBadge from "../common/DecisionStateBadge";
import { formatCurrency } from "./resultHelpers";
import { getRunStatusMeta } from "./runStatusMeta";

function ResultSummary({ result }) {
  const finalSelection = result.final_selection;
  const selectedResults = finalSelection?.selected_results ?? [];
  const hasSelection = selectedResults.length > 0;
  const runStatusMeta = getRunStatusMeta(result.run_status);

  return (
    <section className="page-section" aria-labelledby="result-summary-heading">
      <h2 id="result-summary-heading" className="section-title">
        Decision Summary
      </h2>
      <Card className="result-summary-card">
        <dl className="result-summary-grid">
          <div>
            <dt className="text-label">Decision</dt>
            <dd>
              {hasSelection ? (
                <DecisionStateBadge state={selectedResults[0].final_decision_state} />
              ) : (
                <span className="text-small">{runStatusMeta.label}</span>
              )}
            </dd>
          </div>
          <div>
            <dt className="text-label">Selected group(s)</dt>
            <dd className="text-small">
              {hasSelection ? `${selectedResults.length} (${finalSelection.total_vendor_coverage} vendors)` : "None"}
            </dd>
          </div>
          <div>
            <dt className="text-label">Expected savings</dt>
            <dd className="text-small">{hasSelection ? formatCurrency(finalSelection.total_savings_rs) : "—"}</dd>
          </div>
          <div>
            <dt className="text-label">Why</dt>
            <dd className="text-small">
              {hasSelection ? selectedResults[0].decision.reason : runStatusMeta.description}
            </dd>
          </div>
        </dl>
      </Card>
    </section>
  );
}

export default ResultSummary;
