// Phase 7B -- polished 404 page.

import Button from "../components/common/Button";

function NotFoundPage() {
  return (
    <div className="empty-state">
      <span className="not-found-code" aria-hidden="true">
        404
      </span>
      <p className="empty-state-title">This page doesn't exist</p>
      <p className="empty-state-description">
        The page you're looking for may have been moved or the address may be incorrect.
      </p>
      <div className="empty-state-actions">
        <Button to="/" variant="primary">
          Return to Home
        </Button>
      </div>
    </div>
  );
}

export default NotFoundPage;
