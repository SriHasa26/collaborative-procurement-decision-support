// Phase 7A -- centralized HTTP client. This is the ONLY module in the
// frontend that calls `fetch` directly. Every other module (procurementApi.js,
// and eventually page components) must go through get()/post() here rather
// than scattering fetch() calls across the codebase.
//
// Contains no procurement business logic (no distance, savings, MOQ,
// freshness, or decision calculation) -- it only knows how to talk HTTP to
// whatever backend API_BASE_URL points at.
//
// Phase 8E -- attaches `Authorization: Bearer <access_token>` when a
// Supabase session exists (backend/security/auth.py, Phase 8D, verifies
// it). This is the ONLY place that happens -- no page/component attaches
// its own header, per this phase's "centralize in the existing API
// request layer" requirement. Reuses the existing Supabase client
// singleton (frontend/src/lib/supabase.js) rather than a second one.

import { supabase } from "../lib/supabase";
import { API_BASE_URL } from "../config/env";

async function getAuthHeader() {
  if (!supabase) return {};
  try {
    // Reads the CURRENT session fresh on every request (never a token
    // cached here) -- getSession() also transparently refreshes an
    // expired access token via the stored refresh token, so a long-lived
    // page tab keeps sending a valid token without any extra code. After
    // sign-out, Supabase's own client reports no session, so this simply
    // stops attaching a header on the very next request -- no manual
    // "clear the token" step is needed anywhere.
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    // No session -> no header at all. Never send an empty/fake token.
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    // Session lookup failing (e.g. Supabase misconfigured) must not break
    // an otherwise-public request -- fall back to no header, exactly like
    // "no session".
    return {};
  }
}

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const authHeader = await getAuthHeader();
  let response;

  try {
    response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...authHeader,
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch (networkError) {
    // fetch() itself throws for network-level failures (backend down, CORS
    // rejection, DNS failure, etc.) -- never a Python/SQLite error, since
    // the frontend never talks to anything but this HTTP boundary.
    throw new Error(`Unable to reach the backend at ${url}: ${networkError.message}`);
  }

  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const body = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = isJson && body && body.detail !== undefined ? body.detail : body;
    throw new Error(`Request to ${path} failed (HTTP ${response.status}): ${JSON.stringify(detail)}`);
  }

  return body;
}

export function get(path) {
  return request(path, { method: "GET" });
}

export function post(path, data) {
  return request(path, { method: "POST", body: JSON.stringify(data) });
}
