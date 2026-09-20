// UI-7 -- Section 9: Group Size / Collaboration Pattern. Reuses the same
// proportional-bar classes as DecisionDistribution.jsx (results/
// VendorEconomics.jsx's own .vendor-economics-bar-* pattern) -- a third
// reuse of the one bar implementation this phase relies on throughout.
// Purely descriptive: nowhere claims a larger or smaller group is
// "better" -- the system defines no such relationship.

import Card from "../common/Card";
import LimitedDataState from "./LimitedDataState";
import { MIN_RUNS_FOR_DISTRIBUTION_VISUAL } from "./insightsMetrics";

function GroupSizeAnalysis({ groupSizeDistribution }) {
  const { sizeCounts, totalSelectedGroups } = groupSizeDistribution;
  const sortedSizes = Object.entries(sizeCounts).sort((a, b) => Number(a[0]) - Number(b[0]));

  return (
    <section className="page-section" aria-labelledby="group-size-heading">
      <h2 id="group-size-heading" className="section-title">
        Collaboration Group Size
      </h2>

      {totalSelectedGroups < MIN_RUNS_FOR_DISTRIBUTION_VISUAL ? (
        <LimitedDataState
          title="Not enough historical data"
          description="Group size analysis requires more analyzed runs with a selected collaborative procurement group."
          availableCount={totalSelectedGroups}
        />
      ) : (
        <Card>
          <p className="text-small text-muted">
            Size of every selected procurement group across {totalSelectedGroups} analyzed selection(s).
          </p>
          <div
            className="vendor-economics-bars"
            role="img"
            aria-label={sortedSizes
              .map(([size, count]) => `${size} vendors: ${count} selected group(s)`)
              .join(", ")}
          >
            {sortedSizes.map(([size, count]) => {
              const percent = Math.round((count / totalSelectedGroups) * 100);
              return (
                <div key={size} className="vendor-economics-bar-row" aria-hidden="true">
                  <span className="vendor-economics-bar-label text-small">{size} vendors</span>
                  <div className="vendor-economics-bar-track">
                    <div className="vendor-economics-bar-fill bar-grow-horizontal" style={{ width: `${percent}%` }} />
                  </div>
                  <span className="vendor-economics-bar-value text-small">{count} group(s)</span>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </section>
  );
}

export default GroupSizeAnalysis;
