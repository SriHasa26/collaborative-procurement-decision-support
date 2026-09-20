// Phase 8C -- the ONE module in this frontend that constructs a Supabase
// client. Mirrors frontend/src/api/client.js's existing role as "the only
// module that calls fetch() directly" -- here, `supabase` (below) is the
// only Supabase client instance anywhere in the app; every other module
// (AuthContext, SignInPage, SignUpPage) imports it rather than
// constructing its own.
//
// Uses ONLY the two browser-safe values Supabase itself documents as safe
// to ship in client code: the project URL and the publishable/anon key.
// Never the service role key, never a database connection string, never
// any backend/.env value -- those exist only in backend/.env (git-ignored,
// server-side) and are never read by anything under frontend/.
//
// This client is entirely separate from frontend/src/api/client.js: it
// talks directly to Supabase Auth (sign up/in/out, session storage) and is
// NOT used to call the FastAPI backend, and frontend/src/api/client.js is
// NOT used to talk to Supabase. Phase 8C does not connect the two -- no
// access token from this client is attached to any FastAPI request yet
// (that is a later, dedicated integration phase; see
// reports/phase8c_frontend_supabase_authentication.md Section 12).

import { createClient } from "@supabase/supabase-js";
import { SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL } from "../config/env";

export const isSupabaseConfigured = Boolean(SUPABASE_URL && SUPABASE_PUBLISHABLE_KEY);

if (!isSupabaseConfigured) {
  // A missing value here means authentication cannot possibly work --
  // surfaced loudly and immediately (at module load, in the console)
  // rather than allowed to fail silently or confusingly deep inside a
  // sign-in attempt. Never logs the value itself (there is nothing to log
  // here besides the fact that it is missing). `createClient` itself
  // throws synchronously on an empty URL, which would crash the entire
  // app (including public pages) on a misconfigured checkout -- `supabase`
  // is left `null` instead below, and AuthContext treats that as "signed
  // out, not loading" rather than letting the whole app fail to render.
  console.error(
    "Supabase is not configured: VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY " +
      "must both be set in frontend/.env (see frontend/.env.example). Authentication will not work until they are."
  );
}

export const supabase = isSupabaseConfigured ? createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY) : null;
