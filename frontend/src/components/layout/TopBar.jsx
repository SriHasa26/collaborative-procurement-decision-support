// Phase 7B -- minimal top bar: mobile navigation toggle (hidden on
// desktop via CSS) plus the current section's title, derived from the
// existing route.
// Phase 8C -- adds the account area Phase 7B's own comment noted as
// deliberately absent ("nothing implying authentication exists") --
// authentication exists now. Shows the signed-in user's email + a Sign
// Out action when authenticated, or Sign In/Sign Up links when not. Never
// renders a token, user ID, or any JWT content -- only the email Supabase
// itself returns on the session's user object (Part 9).

import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/useAuth";
import Button from "../common/Button";

const ROUTE_TITLES = {
  "/dashboard": "Dashboard",
  "/insights": "Procurement Insights",
  "/analyze": "Analyze Procurement",
  "/results": "Results",
  "/history": "Run History",
  "/signin": "Sign In",
  "/signup": "Sign Up",
};

function TopBar({ onMenuClick, isMenuOpen }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const title = ROUTE_TITLES[location.pathname] || "Procurement Decision Support";

  async function handleSignOut() {
    // Sign-out errors are rare (e.g. an already-expired session) and are
    // not a reason to leave stale authenticated UI visible -- the local
    // session is gone from Supabase's client either way, so this still
    // navigates to a public page (Part 7).
    await signOut();
    navigate("/", { replace: true });
  }

  return (
    <header className="topbar">
      <button
        type="button"
        className="topbar-menu-button"
        onClick={onMenuClick}
        aria-label="Toggle navigation menu"
        aria-expanded={isMenuOpen}
        aria-controls="primary-sidebar"
      >
        <span aria-hidden="true">☰</span>
      </button>
      <span className="topbar-title">{title}</span>

      <div className="topbar-auth">
        {user ? (
          <>
            <span className="topbar-auth-email" title={user.email}>
              {user.email}
            </span>
            <Button type="button" variant="outline" onClick={handleSignOut}>
              Sign Out
            </Button>
          </>
        ) : (
          <div className="topbar-auth-actions">
            <Button to="/signin" variant="outline">
              Sign In
            </Button>
            <Button to="/signup" variant="primary">
              Sign Up
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}

export default TopBar;
