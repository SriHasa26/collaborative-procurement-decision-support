// UI-2 -- landing page footer. Only real, existing navigation and an
// honest project description -- no fake social links, addresses, phone
// numbers, customer logos, or certifications (none of those exist for
// this project).

import { Link } from "react-router-dom";

function Footer() {
  return (
    <footer className="landing-footer">
      <div className="landing-footer-inner">
        <div>
          <span className="landing-footer-brand">Procurement Decision Support</span>
          <p className="text-small text-muted">
            A rule-based, deterministic decision-support system for collaborative
            <br />
            procurement — not an AI forecasting product, not an autonomous purchasing system.
          </p>
        </div>
        <nav className="landing-footer-links" aria-label="Footer navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#decision-intelligence">Intelligence</a>
          <Link to="/signin">Sign In</Link>
          <Link to="/analyze">Start Analysis</Link>
        </nav>
      </div>
      <p className="text-small text-muted landing-footer-note">
        Built as a research and decision-support project. Figures shown on this page under
        "Demo Scenario" or "Example" labels are illustrative only, not live production statistics.
      </p>
    </footer>
  );
}

export default Footer;
