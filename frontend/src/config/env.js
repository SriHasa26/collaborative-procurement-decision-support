// Phase 7A -- single source of truth for frontend environment configuration.
// No component or API module should read `import.meta.env` directly; every
// configurable value is read here once and exported, so the backend base
// URL is never hardcoded elsewhere in the application.
// Phase 8C -- adds the two Supabase browser-safe configuration values
// (frontend/src/lib/supabase.js is the only module that imports them).
// Both are read from frontend/.env the same way VITE_API_BASE_URL already
// is; neither is a secret -- the Supabase URL and publishable/anon key are
// designed by Supabase to be shipped in browser code (unlike the service
// role key or a database connection string, which never appear in this
// project's frontend at all -- see reports/phase8c_frontend_supabase_authentication.md
// Section 20).

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8731";

// import.meta.env.VITE_API_BASE_URL comes from frontend/.env (git-ignored,
// developer-local) -- see frontend/.env.example for the documented shape.
// Falls back to DEFAULT_API_BASE_URL only so the app has a sane value
// before a developer creates their own .env; it is not a claim that the
// backend is actually reachable there.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;

// No fallback default for either of these: unlike the local backend URL,
// there is no sane placeholder Supabase project to fall back to -- an
// empty/missing value is surfaced as-is, and frontend/src/lib/supabase.js
// deliberately does not swallow that (Section 5 of the Phase 8C report).
export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
export const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;
