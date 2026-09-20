// UI-9 -- Section F: a compact, real-data visual bridge between
// "Candidate Groups Evaluated" and the "Selected Procurement Group"
// shown earlier on this page. `evaluatedCount`/`selectedCount` are the
// SAME two already-backend-computed numbers ResultMetricGrid.jsx already
// displays (result.candidate_group_count/result.selected_group_count) --
// this is a second, visual presentation of numbers already on the page,
// never a new count or a fabricated ranking. Renders nothing when there
// is nothing to evaluate (candidate_group_count === 0) -- never an empty
// or misleading flow.

function DecisionFlowVisual({ evaluatedCount, selectedCount }) {
  if (!evaluatedCount) return null;

  return (
    <div
      className="decision-flow-visual"
      role="img"
      aria-label={`${evaluatedCount} candidate group${evaluatedCount === 1 ? "" : "s"} evaluated; ${selectedCount} selected.`}
    >
      <div className="decision-flow-stage" aria-hidden="true">
        <span className="text-metric">{evaluatedCount}</span>
        <span className="text-small text-muted">Evaluated</span>
      </div>
      <span className="decision-flow-arrow" aria-hidden="true">
        →
      </span>
      <div className="decision-flow-stage decision-flow-stage-selected" aria-hidden="true">
        <span className="text-metric">{selectedCount}</span>
        <span className="text-small text-muted">Selected</span>
      </div>
    </div>
  );
}

export default DecisionFlowVisual;
