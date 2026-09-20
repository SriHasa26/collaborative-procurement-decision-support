// UI-2 -- navigation for the public landing page (/) only. Deliberately
// separate from Sidebar/TopBar (layout.css/AppLayout.jsx, unchanged) --
// a marketing page and the authenticated app shell are different
// products with different navigation needs. Reads the EXISTING auth
// state via useAuth() (unchanged, read-only) to decide which CTA to
// show; never invents a fake signed-in/out state. "Start an Analysis"
// always points at /analyze -- for a signed-out visitor, the EXISTING,
// already-tested ProtectedRoute (Phase 8C) redirects to /signin and
// returns them to /analyze after signing in, so no new auth flow is
// invented here.

import { useState } from "react";
import { useAuth } from "../../auth/useAuth";
import Button from "../common/Button";

const NAV_LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#decision-intelligence", label: "Intelligence" },
];

function LandingNav() {
  const { user, loading } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const primaryCta = !loading && user ? (
    <Button to="/analyze" variant="primary" onClick={() => setIsMenuOpen(false)}>
      Go to Analysis
    </Button>
  ) : (
    <>
      <Button to="/signin" variant="ghost" onClick={() => setIsMenuOpen(false)}>
        Sign In
      </Button>
      <Button to="/analyze" variant="primary" onClick={() => setIsMenuOpen(false)}>
        Start Analysis
      </Button>
    </>
  );

  return (
    <header className="landing-nav">
      <div className="landing-nav-inner">
        <a href="#top" className="landing-nav-brand">
          Procurement<span className="landing-nav-brand-accent">DS</span>
        </a>

        <nav className="landing-nav-links" aria-label="Page sections">
          {NAV_LINKS.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>

        <div className="landing-nav-actions">{primaryCta}</div>

        <button
          type="button"
          className="landing-nav-menu-button"
          onClick={() => setIsMenuOpen((open) => !open)}
          aria-label="Toggle navigation menu"
          aria-expanded={isMenuOpen}
          aria-controls="landing-mobile-menu"
        >
          <span aria-hidden="true">☰</span>
        </button>
      </div>

      {isMenuOpen && (
        <div className="landing-mobile-menu" id="landing-mobile-menu">
          {NAV_LINKS.map((link) => (
            <a key={link.href} href={link.href} onClick={() => setIsMenuOpen(false)}>
              {link.label}
            </a>
          ))}
          <div className="landing-mobile-menu-actions">{primaryCta}</div>
        </div>
      )}
    </header>
  );
}

export default LandingNav;
