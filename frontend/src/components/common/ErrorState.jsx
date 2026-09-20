// Phase 7B -- reusable APPLICATION/NETWORK error presentation (e.g. a
// failed API request). This is intentionally visually distinct (danger
// palette) from DecisionStateCard's ABSTAIN presentation (info palette) --
// ABSTAIN means "insufficient evidence," which this component must never
// be used for. Used today only by BackendStatusCheck's existing (Phase 7A)
// connectivity check; intended for reuse once real API calls exist.

function ErrorState({ title = "Something went wrong", description, actions }) {
  return (
    <div className="error-state" role="alert">
      <span className="error-state-icon" aria-hidden="true">
        !
      </span>
      <p className="error-state-title">{title}</p>
      {description && <p className="error-state-description">{description}</p>}
      {actions && <div className="empty-state-actions">{actions}</div>}
    </div>
  );
}

export default ErrorState;
