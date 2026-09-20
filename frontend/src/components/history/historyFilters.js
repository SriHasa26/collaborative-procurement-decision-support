// UI-6 -- pure search/filter logic over the entries useHistoryData.js
// produces. No calculation, no decision-making -- these functions only
// match already-real fields against a query/filter value.
//
// The decision filter's options are exactly the four real DecisionState
// values (backend/models/enums.py, the same exhaustive list
// decisionStateMeta.js already uses) plus one filter-only, clearly-
// distinct "No Group Selected" option grouping every run whose primary
// decision is absent (getPrimaryDecisionState returned null -- driven by
// RunStatus instead, exactly DecisionHero.jsx's own fallback case). "No
// Group Selected" is never presented as if it were a fifth DecisionState
// -- it describes the ABSENCE of a group-level decision, a run-level
// filtering concern, not a new decision category.

import { DECISION_STATE_META, DECISION_STATE_ORDER } from "../common/decisionStateMeta";
import { getPrimaryDecisionState } from "../results/resultHelpers";

export const NO_SELECTION_FILTER_VALUE = "NO_SELECTION";

export const DECISION_FILTER_OPTIONS = [
  { value: "ALL", label: "All decisions" },
  ...DECISION_STATE_ORDER.map((state) => ({ value: state, label: DECISION_STATE_META[state].label })),
  { value: NO_SELECTION_FILTER_VALUE, label: "No group selected" },
];

// Returns the real DecisionState value, NO_SELECTION_FILTER_VALUE, or
// null when the run's detail was never fetched (beyond
// HISTORY_DETAIL_FETCH_LIMIT, or its detail fetch failed) -- a run in
// that state is genuinely unknown and is excluded from every specific
// decision filter (it still appears under "All decisions").
export function getEntryDecisionFilterValue(entry) {
  if (!entry.detail?.result) return null;
  return getPrimaryDecisionState(entry.detail.result) ?? NO_SELECTION_FILTER_VALUE;
}

export function matchesDecisionFilter(entry, filterValue) {
  if (filterValue === "ALL") return true;
  return getEntryDecisionFilterValue(entry) === filterValue;
}

// Searches only real, already-available fields: commodity and run_id
// (always present, from the lightweight summary) and vendor IDs (only
// for a run whose detail was actually fetched -- `input.vendor_submissions`
// is the complete, as-submitted vendor list, not just the eligible
// subset). A run with no fetched detail simply cannot match a vendor-ID
// search -- it is never silently assumed to contain or exclude a vendor.
export function matchesSearch(entry, query) {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  if (entry.commodity?.toLowerCase().includes(q)) return true;
  if (entry.run_id?.toLowerCase().includes(q)) return true;
  const vendorIds = entry.detail?.input?.vendor_submissions?.map((v) => v.vendor_id?.toLowerCase() ?? "") ?? [];
  return vendorIds.some((id) => id.includes(q));
}

export function filterHistoryEntries(entries, { searchQuery, decisionFilter }) {
  return entries.filter((entry) => matchesSearch(entry, searchQuery) && matchesDecisionFilter(entry, decisionFilter));
}
