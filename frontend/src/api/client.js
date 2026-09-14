// Phase 7A -- centralized HTTP client. This is the ONLY module in the
// frontend that calls `fetch` directly. Every other module (procurementApi.js,
// and eventually page components) must go through get()/post() here rather
// than scattering fetch() calls across the codebase.
//
// Contains no procurement business logic (no distance, savings, MOQ,
// freshness, or decision calculation) -- it only knows how to talk HTTP to
// whatever backend API_BASE_URL points at.

import { API_BASE_URL } from "../config/env";

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  let response;

  try {
    response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
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
