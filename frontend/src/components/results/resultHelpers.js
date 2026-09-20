// Phase 7E -- presentation-only helpers for the Results Dashboard.
//
// CRITICAL BOUNDARY: every function here reads/reshapes/formats data that
// the backend already computed. None of them make a procurement decision,
// calculate savings/cost/distance, resolve MOQ/freshness/WAIT_OR_EXPAND
// logic, or infer a value the backend did not provide. Where a value is
// absent (null/undefined/missing array), these helpers return a safe
// empty/placeholder result -- they never invent a substitute number or
// decision.

// -- Currency/number formatting (frontend-only formatting, not calculation) --

export function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  return `${sign}₹${abs.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatNumber(value, fallback = "—") {
  return value === null || value === undefined ? fallback : String(value);
}

export function formatDistance(km) {
  if (km === null || km === undefined || Number.isNaN(km)) return "—";
  return `${km.toFixed(2)} km`;
}

// UI-5 -- a savings PERCENTAGE, derived from two numbers the backend
// already computed (savings_rs, individual_cost_total_rs) -- not a new
// business metric. individual_cost_total_rs is what vendors would have
// paid buying alone; savings_rs / individual_cost_total_rs is the
// standard, unambiguous ratio of the two, guarded against a missing or
// zero denominator (never divides by zero, never invents a value when
// either input is absent).
export function getSavingsPercent(savingsRs, individualCostTotalRs) {
  if (
    savingsRs === null || savingsRs === undefined ||
    individualCostTotalRs === null || individualCostTotalRs === undefined ||
    individualCostTotalRs === 0
  ) {
    return null;
  }
  return (savingsRs / individualCostTotalRs) * 100;
}

export function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toFixed(1)}%`;
}

// UI-5 -- human-readable labels for backend/models/reasons.py's
// ContextValidationReason values, shown in Diagnostics when a run's
// context failed structural validation (batch_eligibility.context_validation).
// Same exhaustive, fixed-mapping pattern already established by
// decisionStateMeta.js/runStatusMeta.js -- an unrecognized code falls back
// to the raw string rather than guessing at its meaning.
const CONTEXT_VALIDATION_REASON_LABELS = {
  MISSING_COMMODITY: "The commodity identifier was missing.",
  EMPTY_VENDOR_COLLECTION: "No vendor submissions were included in the request.",
  MALFORMED_VENDOR_COLLECTION: "The vendor submissions were not structured as expected.",
  MALFORMED_CONTEXT_METADATA: "The procurement context (commodity/date/price) was not structured as expected.",
};

export function getContextValidationReasonLabel(reasonCode) {
  return CONTEXT_VALIDATION_REASON_LABELS[reasonCode] ?? reasonCode;
}

// -- Safe accessors: normalize a possibly-absent nested structure to a
// safe default (an empty array/object), never fabricating its contents. --

export function hasUsableResult(result) {
  return Boolean(result) && typeof result.run_status === "string";
}

// UI-6 -- the same "primary decision" derivation DecisionHero.jsx (UI-5)
// already uses inline, extracted so History's own run rows/filters can
// reuse it rather than re-deriving it a second time. A run's group-level
// decision is only meaningful once at least one group was actually
// selected (final_selection.selected_results[0].final_decision_state --
// read directly from the response, never assumed to be "BUY_TOGETHER"
// even though selection.py only ever selects already-BUY_TOGETHER
// candidates). Returns null when there is no selection -- callers must
// fall back to the run's own RunStatus (getRunStatusMeta), never invent a
// group-level decision where none exists.
export function getPrimaryDecisionState(result) {
  const selectedResults = result?.final_selection?.selected_results ?? [];
  return selectedResults.length > 0 ? selectedResults[0].final_decision_state : null;
}

export function getVendorOutcomes(batchEligibility) {
  if (!batchEligibility) return [];
  const eligible = batchEligibility.eligible_vendors ?? [];
  const abstained = batchEligibility.abstained_vendors ?? [];
  const validationErrors = batchEligibility.validation_error_vendors ?? [];
  // Simple concatenation for one combined table -- each vendor's own
  // `status` field (from backend/models/enums.py's OutcomeKind: "OK" /
  // "ABSTAIN" / "VALIDATION_ERROR") is preserved unchanged and is what
  // the table actually renders per row; this is presentation-only
  // aggregation of three already-existing arrays, not a new judgment.
  return [...eligible, ...abstained, ...validationErrors];
}

const GROUP_STATE_DISPLAY_PRIORITY = {
  BUY_TOGETHER: 0,
  WAIT_OR_EXPAND_GROUP: 1,
  DO_NOT_BUY_TOGETHER: 2,
  ABSTAIN: 3,
};

// Deterministic, stable DISPLAY ordering only (selected groups first, then
// by final_decision_state, then alphabetically by group_id) -- never
// changes which state a group is shown with.
export function sortEvaluatedGroups(allEvaluatedResults, selectedGroupIds) {
  const selectedSet = new Set(selectedGroupIds ?? []);
  return [...(allEvaluatedResults ?? [])].sort((a, b) => {
    const aSelected = selectedSet.has(a.decision.group_id) ? 0 : 1;
    const bSelected = selectedSet.has(b.decision.group_id) ? 0 : 1;
    if (aSelected !== bSelected) return aSelected - bSelected;

    const aPriority = GROUP_STATE_DISPLAY_PRIORITY[a.final_decision_state] ?? 99;
    const bPriority = GROUP_STATE_DISPLAY_PRIORITY[b.final_decision_state] ?? 99;
    if (aPriority !== bPriority) return aPriority - bPriority;

    return a.decision.group_id.localeCompare(b.decision.group_id);
  });
}
