// Phase 7A -- minimal application layout foundation only.
// Deliberately NOT a real navigation system, sidebar, or dashboard shell
// (those belong to Phase 7C+); this exists only so routed pages have a
// consistent place to render and a way to reach every placeholder route
// while verifying routing manually.

import { Link, Outlet } from "react-router-dom";

function Layout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-title">Collaborative Procurement Decision-Support System</span>
        <nav className="app-nav">
          <Link to="/">Home</Link>
          <Link to="/analyze">Analyze</Link>
          <Link to="/results">Results</Link>
          <Link to="/history">History</Link>
        </nav>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
