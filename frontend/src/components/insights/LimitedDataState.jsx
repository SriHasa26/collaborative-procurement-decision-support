// UI-7 -- Section 11: the shared "LIMITED DATA" presentation, reused by
// every analytics section that cannot yet be shown as a real
// distribution/ranking (Rule 3: "do NOT create a dramatic trend chart"
// when only 1-2 runs exist). Deliberately distinct in tone from
// EmptyState (which means "there is nothing here") -- this means "there
// IS something here, just not enough of it yet to show honestly."

function LimitedDataState({ title = "Limited data", description, availableCount }) {
  return (
    <div className="limited-data-state" role="status">
      <span className="limited-data-icon" aria-hidden="true">
        ◐
      </span>
      <p className="limited-data-title">{title}</p>
      {description && <p className="text-small text-muted">{description}</p>}
      {availableCount !== undefined && (
        <p className="text-small text-muted limited-data-count">
          Available: {availableCount} run{availableCount === 1 ? "" : "s"}
        </p>
      )}
    </div>
  );
}

export default LimitedDataState;
