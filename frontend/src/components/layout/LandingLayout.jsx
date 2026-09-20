// UI-2 -- the public landing page's own shell: LandingNav + routed
// content + Footer. Deliberately NOT AppLayout/Sidebar/TopBar (those are
// completely unchanged and still used by every other route -- see
// routes/AppRoutes.jsx).

import { Outlet } from "react-router-dom";
import Footer from "./Footer";
import LandingNav from "./LandingNav";

function LandingLayout() {
  return (
    <div className="landing-shell" id="top">
      <LandingNav />
      <main>
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

export default LandingLayout;
