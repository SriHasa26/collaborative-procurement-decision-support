// Phase 7B -- application shell: Sidebar + TopBar + routed page content.
// Supersedes Phase 7A's Layout.jsx (a bare header/nav placeholder) now
// that a real, responsive navigation shell exists. `isMobileNavOpen` is
// plain component-local React state -- not a state-management library --
// used only to toggle the off-canvas sidebar below the 1024px breakpoint.
// Closing it on navigation is handled directly by Sidebar's own nav-link
// onClick (see Sidebar.jsx), not by watching the route in an effect --
// that keeps the state change tied to the actual user interaction that
// causes it, rather than a synchronized side effect.

import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

function AppLayout() {
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar isOpen={isMobileNavOpen} onClose={() => setIsMobileNavOpen(false)} />
      <div className="app-main">
        <TopBar onMenuClick={() => setIsMobileNavOpen((open) => !open)} isMenuOpen={isMobileNavOpen} />
        <main className="app-content">
          <div className="app-content-inner">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
