// Phase 7B -- reusable loading indicator. Not driven by any real request
// in this phase except BackendStatusCheck's existing (Phase 7A) health
// check; intended for reuse once real API calls are wired up in later
// phases.

function LoadingState({ label = "Loading…" }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export default LoadingState;
