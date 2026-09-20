// Phase 7B -- primary navigation for the authenticated app shell.
// NavLink's active matching gives a clear, real (not guessed) active-route
// indication.
// UI-3 -- nav items changed to exactly this phase's own suggested set:
// Dashboard, New Analysis, Run History. "Home" (-> "/") was removed: "/"
// is now UI-2's public marketing page, not part of the authenticated app
// -- an authenticated user's "home" is now /dashboard, per this phase's
// own instruction. The standalone "Results" link was also dropped: /results
// only ever has content via router state handed off from /analyze or
// /history (unchanged, Phase 7D/7F), so it was never a real standalone
// destination -- it remains a fully working ROUTE (unchanged), just no
// longer a dead-feeling top-level nav entry. "Insights"/"Settings" (this
// phase's own suggested "potential future" items) were deliberately
// omitted rather than shown as disabled/fake links -- neither page exists
// yet, and this phase's own instruction is explicit: "do not create dead
// links that look functional."
// UI-7 -- "Insights" is added now that /insights is a real, working page
// (routes/AppRoutes.jsx), positioned right after Dashboard to match this
// phase's own "Dashboard -> Insights -> History -> Results" coherent flow.
import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", end: true },
  { to: "/insights", label: "Insights" },
  { to: "/analyze", label: "New Analysis" },
  { to: "/history", label: "Run History" },
];

function navLinkClassName({ isActive }) {
  return `sidebar-nav-link${isActive ? " is-active" : ""}`;
}

function Sidebar({ isOpen, onClose }) {
  return (
    <>
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} aria-hidden="true" />}
      <aside id="primary-sidebar" className={`sidebar${isOpen ? " is-open" : ""}`}>
        <div className="sidebar-brand">
          <span className="sidebar-brand-name">Procurement Decision Support</span>
          <span className="sidebar-brand-tagline">Collaborative Procurement Decision-Support System</span>
        </div>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={navLinkClassName}
              onClick={onClose}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}

export default Sidebar;
