// Phase 8C -- route guard. This is a UI/navigation convenience only --
// per Part 17's explicit requirement, it is NOT a replacement for backend
// authorization. The real security boundary is Phase 8D/8F's
// get_current_user()/repository ownership filtering on the FastAPI side;
// this component only decides what the React app shows/navigates to. It
// never inspects a JWT itself -- only whether AuthContext currently has a
// `user`, which mirrors Supabase's own session state.

import { Navigate, Outlet, useLocation } from "react-router-dom";
import LoadingState from "../components/common/LoadingState";
import { useAuth } from "./useAuth";

function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Part 4: never redirect, and never render the protected content,
  // before the initial session check has completed -- avoids both a
  // false "please sign in" flash for an already-signed-in user AND a
  // flash of protected content for one who is not.
  if (loading) {
    return <LoadingState label="Checking your session…" />;
  }

  if (!user) {
    // `state={{ from: location }}` lets SignInPage return the user to the
    // page they actually asked for after a successful sign-in (Part 8),
    // instead of always landing on Home.
    return <Navigate to="/signin" state={{ from: location }} replace />;
  }

  return <Outlet />;
}

export default ProtectedRoute;
