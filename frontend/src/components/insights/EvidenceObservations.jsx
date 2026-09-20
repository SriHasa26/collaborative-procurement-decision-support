// UI-7 -- Section 10: Evidence-Based Observations. Reuses UI-5's
// `.diagnostics-list`/`.diagnostic-item-info` classes (results.css) --
// the visual language of "a list of real, individually-verified facts"
// already exists on this page's sibling (Results), so it is reused
// rather than re-invented here. Every sentence is produced by
// insightsMetrics.js's buildEvidenceObservations() -- this component
// only renders whatever that pure function returned, adding no wording
// of its own.

import LimitedDataState from "./LimitedDataState";

function EvidenceObservations({ observations }) {
  return (
    <section className="page-section" aria-labelledby="evidence-observations-heading">
      <h2 id="evidence-observations-heading" className="section-title">
        Evidence-Based Observations
      </h2>

      {observations.length === 0 ? (
        <LimitedDataState
          title="Not enough historical data"
          description="Observations require more analyzed run history before a real pattern can be described."
        />
      ) : (
        <ul className="diagnostics-list">
          {observations.map((observation) => (
            <li key={observation} className="diagnostic-item diagnostic-item-info">
              {observation}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default EvidenceObservations;
