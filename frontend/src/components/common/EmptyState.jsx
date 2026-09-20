// Phase 7B -- reusable "nothing here yet" presentation. Used by
// ResultsPage and HistoryPage in this phase (both pages have no real data
// yet, by design -- Phase 7B does not connect to the API), and intended
// for reuse by any future page/list that can legitimately be empty.

function EmptyState({ icon = "○", title, description, actions }) {
  return (
    <div className="empty-state" role="status">
      <span className="empty-state-icon" aria-hidden="true">
        {icon}
      </span>
      <p className="empty-state-title">{title}</p>
      {description && <p className="empty-state-description">{description}</p>}
      {actions && <div className="empty-state-actions">{actions}</div>}
    </div>
  );
}

export default EmptyState;
