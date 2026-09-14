// Phase 7A -- single source of truth for frontend environment configuration.
// No component or API module should read `import.meta.env` directly; every
// configurable value is read here once and exported, so the backend base
// URL is never hardcoded elsewhere in the application.

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8731";

// import.meta.env.VITE_API_BASE_URL comes from frontend/.env (git-ignored,
// developer-local) -- see frontend/.env.example for the documented shape.
// Falls back to DEFAULT_API_BASE_URL only so the app has a sane value
// before a developer creates their own .env; it is not a claim that the
// backend is actually reachable there.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;
