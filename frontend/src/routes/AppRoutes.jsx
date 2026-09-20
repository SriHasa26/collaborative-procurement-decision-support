// Phase 7A -- routing foundation. Phase 7B -- pages now render inside the
// real application shell (AppLayout), superseding Phase 7A's placeholder
// Layout.
//
// Phase 8C -- adds /signin and /signup (public) and wraps /analyze,
// /results, /history in ProtectedRoute (Part 8's recommended policy).
// /analyze and /history make real backend requests that require
// authentication as of Phase 8D/8F, so gating them here is a genuine UX
// improvement, not just decoration -- an unauthenticated visitor would
// otherwise reach a working-looking page whose every request fails with
// HTTP 401. /results is gated too even though it never calls the backend
// itself (its data arrives only via router state from /analyze or
// /history, per those pages' own existing behavior) -- gating it keeps
// the "protected" set consistent with Part 8's recommendation and closes
// off a page that has no useful purpose for a signed-out visitor. /,
// /signin, /signup, and the 404 page remain public.
//
// UI-2 -- "/" now renders inside its own LandingLayout (a lighter shell:
// LandingNav + Footer, no permanent sidebar) instead of AppLayout -- a
// public marketing page and the authenticated app shell are different
// products with different navigation needs. Every other route
// (/signin, /signup, /analyze, /results, /history, 404) still renders
// inside AppLayout, completely unchanged, with identical protection.
//
// UI-3 -- adds /dashboard, protected by the SAME existing ProtectedRoute
// used by /analyze/etc. (no second auth mechanism), inside the SAME
// unmodified AppLayout. It is the new authenticated "home" -- SignInPage/
// SignUpPage now redirect here by default after a fresh sign-in (see
// their own comments) -- but "/" remains exactly UI-2's public landing
// page, untouched.
//
// UI-7 -- adds /insights, protected by the SAME ProtectedRoute, inside
// the SAME AppLayout -- no new auth mechanism, no new layout shell.
// Completes the coherent Dashboard -> Insights -> History -> Results
// flow this phase's own brief asks for.
import { Route, Routes } from "react-router-dom";
import ProtectedRoute from "../auth/ProtectedRoute";
import AppLayout from "../components/layout/AppLayout";
import LandingLayout from "../components/layout/LandingLayout";
import AnalysisPage from "../pages/AnalysisPage";
import DashboardPage from "../pages/DashboardPage";
import HistoryPage from "../pages/HistoryPage";
import HomePage from "../pages/HomePage";
import InsightsPage from "../pages/InsightsPage";
import NotFoundPage from "../pages/NotFoundPage";
import ResultsPage from "../pages/ResultsPage";
import SignInPage from "../pages/SignInPage";
import SignUpPage from "../pages/SignUpPage";

function AppRoutes() {
  return (
    <Routes>
      <Route element={<LandingLayout />}>
        <Route path="/" element={<HomePage />} />
      </Route>
      <Route element={<AppLayout />}>
        <Route path="/signin" element={<SignInPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/insights" element={<InsightsPage />} />
          <Route path="/analyze" element={<AnalysisPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default AppRoutes;
