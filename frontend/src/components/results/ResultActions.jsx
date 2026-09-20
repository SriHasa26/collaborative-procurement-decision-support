// UI-5 -- Section 11: closing actions. Both routes already exist and are
// unchanged (/analyze, /history) -- no fake action, no dead link.

import Button from "../common/Button";

function ResultActions() {
  return (
    <section className="page-section result-actions">
      <Button to="/analyze" variant="primary">
        Analyze Another Procurement
      </Button>
      <Button to="/history" variant="secondary">
        View Run History
      </Button>
    </section>
  );
}

export default ResultActions;
