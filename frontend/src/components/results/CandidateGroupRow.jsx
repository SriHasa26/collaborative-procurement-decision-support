// UI-5 -- one row of the Candidate Group Analysis panel (Section 8).
// Collapsed by default (matching UI-4's VendorCard collapsed-by-default
// convention for a potentially long list), expandable via a real button
// (keyboard-accessible, aria-expanded) rather than native <details> here,
// since the selected row needs to be programmatically auto-expanded by
// its parent. Shows BOTH the base decision (decision.decision_state --
// Phase 6A's unmodified per-candidate evaluation) and the final decision
// (final_decision_state -- after WAIT_OR_EXPAND_GROUP superset
// resolution) side by side, exactly as the former GroupDecisionList.jsx
// (Phase 7E) already did -- that distinction must never be collapsed into
// one value.

import DecisionStateBadge from "../common/DecisionStateBadge";
import AllocationTable from "./AllocationTable";
import { formatCurrency, formatDistance } from "./resultHelpers";

function CandidateGroupRow({ entry, isSelected, isExpanded, onToggle }) {
  const decision = entry.decision;

  return (
    <div className={`candidate-group-row${isSelected ? " is-selected" : ""}${isExpanded ? " is-expanded" : ""}`}>
      <button
        type="button"
        className="candidate-group-row-header"
        onClick={onToggle}
        aria-expanded={isExpanded}
      >
        <div className="candidate-group-row-summary">
          {isSelected && <span className="candidate-group-selected-mark">✓ Selected</span>}
          <span className="card-title candidate-group-id">{decision.group_id}</span>
          <span className="text-small text-muted">{entry.vendor_ids.length} vendor(s)</span>
        </div>
        <div className="candidate-group-row-badges">
          <DecisionStateBadge state={decision.decision_state} />
          {decision.decision_state !== entry.final_decision_state && (
            <DecisionStateBadge state={entry.final_decision_state} />
          )}
          <span className="candidate-group-savings-preview text-small">{formatCurrency(decision.savings_rs)}</span>
          <span className="candidate-group-chevron" aria-hidden="true">
            {isExpanded ? "▲" : "▼"}
          </span>
        </div>
      </button>

      {/* UI-8 -- always mounted (rather than conditionally rendered) so
          the grid-rows expand/collapse below can actually transition;
          `inert` removes it from tab order and screen-reader traversal
          while visually collapsed, matching the old conditional-render's
          own accessibility guarantee (collapsed content was never
          reachable), and `aria-hidden` reinforces that for AT that
          doesn't yet support `inert`. */}
      <div className={`candidate-group-row-detail-wrapper${isExpanded ? " is-expanded" : ""}`} inert={!isExpanded}>
        <div className="candidate-group-row-detail" aria-hidden={!isExpanded}>
          <p className="text-small">Vendors: {entry.vendor_ids.join(", ")}</p>
          <p className="text-small">
            {entry.expansion_reason || decision.reason}
            {entry.resolving_superset_group_ids.length > 0 && (
              <span className="text-small text-muted">
                {" "}
                — resolved by: {entry.resolving_superset_group_ids.join(", ")}
              </span>
            )}
          </p>

          <dl className="candidate-group-facts">
            <div>
              <dt className="text-small text-muted">Aggregate quantity</dt>
              <dd className="text-small">{decision.aggregate_quantity_kg != null ? `${decision.aggregate_quantity_kg} kg` : "—"}</dd>
            </div>
            <div>
              <dt className="text-small text-muted">Centroid distance</dt>
              <dd className="text-small">{formatDistance(decision.centroid_distance_km)}</dd>
            </div>
            <div>
              <dt className="text-small text-muted">Individual cost</dt>
              <dd className="text-small">{formatCurrency(decision.individual_cost_total_rs)}</dd>
            </div>
            <div>
              <dt className="text-small text-muted">Collaborative cost</dt>
              <dd className="text-small">{formatCurrency(decision.collaborative_cost_rs)}</dd>
            </div>
          </dl>

          <AllocationTable allocations={decision.per_vendor_allocation} />
        </div>
      </div>
    </div>
  );
}

export default CandidateGroupRow;
