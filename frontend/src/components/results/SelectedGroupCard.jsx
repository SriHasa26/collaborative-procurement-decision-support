// UI-5 -- Section 4: "Selected Procurement Group" -- WHO is being
// procured together, and the group-level facts behind that group's own
// GroupDecisionResult (backend/models/contracts.py). Replaces the former
// FinalSelectionSection.jsx (Phase 7E), which combined this with the
// per-vendor economics table -- now split out into VendorEconomics.jsx so
// each section answers exactly one of this phase's own questions ("who"
// vs "where did the savings come from"). A zero-selection outcome is a
// valid, neutral outcome (Phase 7E's own established wording), never a
// failure state.

import Card from "../common/Card";
import DecisionStateBadge from "../common/DecisionStateBadge";
import EmptyState from "../common/EmptyState";
import SelectedGroupNetwork from "./SelectedGroupNetwork";
import { formatDistance, formatNumber } from "./resultHelpers";

function GroupFacts({ decision }) {
  const facts = [
    { label: "Aggregate quantity", value: decision.aggregate_quantity_kg != null ? `${decision.aggregate_quantity_kg} kg` : "—" },
    { label: "Review period", value: decision.k_star != null ? `${decision.k_star} day(s)` : "—" },
    { label: "Centroid distance", value: formatDistance(decision.centroid_distance_km) },
    {
      label: "Within max distance",
      value: decision.within_d_max === null || decision.within_d_max === undefined ? "—" : decision.within_d_max ? "Yes" : "No",
    },
  ];

  if (decision.moq_applicable) {
    facts.push({ label: "MOQ met", value: decision.moq_met ? "Yes" : "No" });
  }

  return (
    <dl className="selected-group-facts">
      {facts.map((fact) => (
        <div key={fact.label} className="selected-group-fact">
          <dt className="text-small text-muted">{fact.label}</dt>
          <dd className="text-small">{fact.value}</dd>
        </div>
      ))}
    </dl>
  );
}

// UI-8 -- `batchEligibility` is threaded through (ResultsPage.jsx ->
// here -> SelectedGroupNetwork.jsx) so the network's click-to-inspect
// detail panel can show each vendor's real submitted price/demand
// (batch_eligibility.eligible_vendors[].vendor_input) alongside its real
// cost-share/savings (already available on `entry.decision.
// per_vendor_allocation`) -- no new data, only a deeper read of data this
// page already receives.
function SelectedGroupCard({ finalSelection, batchEligibility }) {
  const selectedResults = finalSelection?.selected_results ?? [];

  return (
    <section className="page-section" aria-labelledby="selected-group-heading">
      <h2 id="selected-group-heading" className="section-title">
        Selected Procurement Group
      </h2>

      {selectedResults.length === 0 ? (
        <EmptyState
          icon="○"
          title="No collaborative procurement group was selected for this run."
          description="This is a valid outcome: the evaluated evidence did not support selecting any group for this run. See the candidate group analysis below for the reasoning."
        />
      ) : (
        <div className="selected-group-list">
          {selectedResults.map((entry) => (
            <Card key={entry.decision.group_id} variant="elevated" className="selected-group-card">
              <div className="card-header-row">
                <div>
                  <span className="text-label">Group</span>
                  <p className="card-title">{entry.decision.group_id}</p>
                </div>
                <DecisionStateBadge state={entry.final_decision_state} />
              </div>

              <p className="text-small">{entry.decision.reason}</p>

              <div className="selected-group-vendors">
                <span className="text-label">Vendors ({formatNumber(entry.vendor_ids.length)})</span>
                <div className="selected-group-vendor-tags">
                  {entry.vendor_ids.map((vendorId) => (
                    <span key={vendorId} className="selected-group-vendor-tag">
                      {vendorId}
                    </span>
                  ))}
                </div>
              </div>

              <GroupFacts decision={entry.decision} />

              <SelectedGroupNetwork entry={entry} batchEligibility={batchEligibility} />
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}

export default SelectedGroupCard;
