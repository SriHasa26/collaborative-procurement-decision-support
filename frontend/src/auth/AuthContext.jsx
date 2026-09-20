// Phase 8C -- centralized authentication state, via React Context (the
// project's existing state pattern -- component-local useState/useEffect
// everywhere else, e.g. AppLayout.jsx's isMobileNavOpen; no Redux/Zustand
// exists or is introduced here). Session truth lives entirely in
// frontend/src/lib/supabase.js's client -- this context only mirrors it
// into React state so components can read/react to it, and never stores
// a token/credential itself.

import { useEffect, useState } from "react";
import { isSupabaseConfigured, supabase } from "../lib/supabase";
import { AuthContext } from "./authContextObject";

export function AuthProvider({ children }) {
  // `loading` starts true and stays true until the INITIAL session check
  // (getSession(), below) resolves -- Part 4's "do not briefly flash
  // protected content before authentication state is known" requirement.
  // A misconfigured Supabase client (isSupabaseConfigured === false) is
  // treated as "definitively signed out," not "stuck loading forever" --
  // see frontend/src/lib/supabase.js.
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(isSupabaseConfigured);

  useEffect(() => {
    if (!supabase) return;

    let isActive = true;

    // Restores whatever session Supabase's client already persisted
    // (its own storage, not anything this app manages) -- this is what
    // makes a refresh keep the user signed in without any app-level code
    // re-implementing session storage.
    supabase.auth.getSession().then(({ data }) => {
      if (isActive) {
        setSession(data.session);
        setLoading(false);
      }
    });

    // The official Supabase mechanism for reacting to sign-in/sign-out/
    // token-refresh as they happen, so the UI updates immediately without
    // a manual refresh (Part 3's requirement). One listener for the
    // lifetime of the provider -- the empty dependency array below means
    // this effect (and therefore this subscription) runs exactly once.
    const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
      if (isActive) {
        setSession(newSession);
        setLoading(false);
      }
    });

    return () => {
      isActive = false;
      listener.subscription.unsubscribe();
    };
  }, []);

  // A fixed, safe shape for the "Supabase is not configured" case (see
  // frontend/src/lib/supabase.js) -- SignInPage/SignUpPage already know
  // how to render an `error` field from these calls, so this reuses that
  // path instead of letting `supabase.auth...` throw on a null client.
  const NOT_CONFIGURED_ERROR = { error: { message: "Authentication is not configured for this environment." } };

  const value = {
    session,
    user: session?.user ?? null,
    loading,
    signUp: (email, password) =>
      supabase ? supabase.auth.signUp({ email, password }) : Promise.resolve(NOT_CONFIGURED_ERROR),
    signIn: (email, password) =>
      supabase ? supabase.auth.signInWithPassword({ email, password }) : Promise.resolve(NOT_CONFIGURED_ERROR),
    signOut: () => (supabase ? supabase.auth.signOut() : Promise.resolve(NOT_CONFIGURED_ERROR)),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
