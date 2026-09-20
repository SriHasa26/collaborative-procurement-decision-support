// UI-7 -- Section 4: Decision Distribution. Reuses the exact proportional
// -bar CSS results/VendorEconomics.jsx (UI-5) already established
// (.vendor-economics-bar-row/-track/-fill/-label/-value) -- a labeled
// proportional bar is a labeled proportional bar regardless of what it
// measures, so no second bar implementation was created. Percentages are
// only ever computed from the real counts below (count / consideredCount
// * 100) -- never invented.
//
// With fewer than MIN_RUNS_FOR_DISTRIBUTION_VISUAL considered runs, a
// segmented distribution would visually overstate what 0-1 data points
// can support (Rule 4) -- a single plain fact or a LimitedDataState is
// shown instead.

import Card from "../common/Card";
import LimitedDataState from "./LimitedDataState";
import { getDecisionDistributionLabel, MIN_RUNS_FOR_DISTRIBUTION_VISUAL } from "./insightsMetrics";

function DecisionDistribution({ decisionDistribution }) {
  const { counts, consideredCount } = decisionDistribution;

  return (
    <section className="page-section" aria-labelledby="decision-distribution-heading">
      <h2 id="decision-distribution-heading" className="section-title">
        Decision Distribution
      </h2>

      {consideredCount === 0 && (
        <LimitedDataState
          title="Not enough historical data"
          description="This insight requires at least one analyzed run with detailed result data."
          availableCount={0}
        />
      )}

      {consideredCount === 1 && (
        <LimitedDataState
          title="Limited data"
          description={`This insight requires more historical runs to show a real distribution. The one analyzed run was classified as ${getDecisionDistributionLabel(Object.keys(counts)[0])}.`}
          availableCount={1}
        />
      )}

      {consideredCount >= MIN_RUNS_FOR_DISTRIBUTION_VISUAL && (
        <Card>
          <p className="text-small text-muted">
            {consideredCount} analyzed run{consideredCount === 1 ? "" : "s"} with available detail.
          </p>
          <div
            className="vendor-economics-bars"
            role="img"
            aria-label={Object.entries(counts)
              .map(([value, count]) => `${getDecisionDistributionLabel(value)}: ${count} of ${consideredCount} runs`)
              .join(", ")}
          >
            {Object.entries(counts)
              .sort((a, b) => b[1] - a[1])
              .map(([value, count]) => {
                const percent = Math.round((count / consideredCount) * 100);
                return (
                  <div key={value} className="vendor-economics-bar-row" aria-hidden="true">
                    <span className="vendor-economics-bar-label text-small">{getDecisionDistributionLabel(value)}</span>
                    <div className="vendor-economics-bar-track">
                      <div className="vendor-economics-bar-fill bar-grow-horizontal" style={{ width: `${percent}%` }} />
                    </div>
                    <span className="vendor-economics-bar-value text-small">
                      {count} ({percent}%)
                    </span>
                  </div>
                );
              })}
          </div>
        </Card>
      )}
    </section>
  );
}

export default DecisionDistribution;
