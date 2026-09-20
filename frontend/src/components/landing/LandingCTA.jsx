// UI-2 -- final conversion section. Same /analyze-first routing
// reasoning as Hero.jsx: ProtectedRoute (unchanged) handles the
// sign-in-then-return flow for a signed-out visitor.

import Button from "../common/Button";

function LandingCTA() {
  return (
    <section className="landing-cta-section">
      <div className="landing-cta-inner">
        <h2 className="landing-cta-heading">Ready to find your next procurement opportunity?</h2>
        <p className="landing-cta-subtext">
          Submit vendor and demand information, and get a transparent, explainable recommendation.
        </p>
        <Button to="/analyze" variant="primary">
          Start an Analysis
        </Button>
      </div>
    </section>
  );
}

export default LandingCTA;
