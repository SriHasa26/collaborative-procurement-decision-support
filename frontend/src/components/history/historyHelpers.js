// Phase 7F -- presentation-only helpers for the Run History page.
//
// Same boundary as frontend/src/components/results/resultHelpers.js
// (Phase 7E): these functions format/shorten/interpret already-provided
// data for display -- none of them fabricate a value, infer a decision,
// or change the underlying data used for any API call.

// -- Timestamp formatting (display only; the raw `created_at` ISO string
// from the backend is never mutated -- callers keep using it for
// anything besides display, e.g. sorting is already done by the backend). --
export function formatRunTimestamp(createdAt) {
  if (!createdAt) return "—";
  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) return createdAt; // unparseable -- show the raw value, never invent one
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

// -- Run ID display shortening. The FULL run_id (unaltered) must still be
// used for every API call and remains available via `title`/full-text
// display alongside this shortened form -- this never changes what's
// sent to getProcurementRun(). --
export function shortenRunId(runId) {
  if (!runId) return "—";
  return `Run #${runId.slice(0, 8)}`;
}

// -- Run-detail-retrieval error wording. Mirrors the SAME prefix-matching
// technique already established in
// frontend/src/components/analysis/AnalysisForm.jsx's
// describeSubmissionError() -- reusing client.js's own existing error
// message convention (Phase 7A), not inventing a parallel error format. --
export function describeRunRetrievalError(error) {
  const message = error instanceof Error ? error.message : String(error);
  if (message.startsWith("Unable to reach the backend")) {
    return "Unable to connect to the analysis service. Please check that the backend is running and try again.";
  }
  if (message.includes("HTTP 404")) {
    return "This run could not be found. It may have been removed.";
  }
  return "This run's details could not be loaded. Please try again.";
}

export function describeHistoryLoadError(error) {
  const message = error instanceof Error ? error.message : String(error);
  if (message.startsWith("Unable to reach the backend")) {
    return "Unable to connect to the analysis service. Please check that the backend is running and try again.";
  }
  return "Run history could not be loaded. Please try again.";
}
