// UI-5 -- Section 5: "Vendor Economics" -- WHERE the savings came from,
// for each selected group. Every bar's proportion and every number is
// read directly from GroupDecisionResult.per_vendor_allocation
// (backend/models/contracts.py's PerVendorAllocation) -- no chart library
// was added; this is a plain proportional-width <div> bar, the same
// zero-dependency technique UI-3's SavingsAnalytics.jsx already
// established for its own bar chart (styles/dashboard.css's
// .savings-chart-bar), reused here rather than duplicated with a second
// implementation.

import Card from "../common/Card";
import EmptyState from "../common/EmptyState";
import AllocationTable from "./AllocationTable";
import { formatCurrency, formatPercent, getSavingsPercent } from "./resultHelpers";

// UI-9 -- Section G: "Vendor -> Cost Share -> Savings". Each vendor now
// gets TWO proportional bars, not one -- its real cost share (unchanged
// from UI-5, scaled against the highest share_rs in this group) directly
// paired with its real individual savings (share_rs's own sibling field
// on the exact same PerVendorAllocation object, scaled against the
// highest individual_savings_rs in this group) -- a genuine, data-driven
// pairing, never a fabricated ratio or intermediate value. Two colors
// (primary for cost share, success for savings) distinguish the two
// measures without relying on position alone.
function VendorEconomicsBars({ allocations }) {
  const maxShare = Math.max(...allocations.map((a) => a.share_rs));
  const maxSavings = Math.max(...allocations.map((a) => a.individual_savings_rs ?? 0));

  return (
    <div className="vendor-economics-bars">
      {allocations.map((allocation) => {
        const sharePercent = maxShare > 0 ? (allocation.share_rs / maxShare) * 100 : 0;
        const savingsPercent =
          maxSavings > 0 && allocation.individual_savings_rs != null
            ? (allocation.individual_savings_rs / maxSavings) * 100
            : 0;
        return (
          <div key={allocation.vendor_id} className="vendor-economics-bar-group">
            <span className="vendor-economics-bar-vendor text-small">{allocation.vendor_id}</span>

            <div className="vendor-economics-bar-row">
              <span className="vendor-economics-bar-label text-small text-muted">Cost share</span>
              <div className="vendor-economics-bar-track">
                <div
                  className="vendor-economics-bar-fill bar-grow-horizontal"
                  style={{ width: `${sharePercent}%` }}
                />
              </div>
              <span className="vendor-economics-bar-value text-small">{formatCurrency(allocation.share_rs)}</span>
            </div>

            {allocation.individual_savings_rs != null && (
              <div className="vendor-economics-bar-row">
                <span className="vendor-economics-bar-label text-small text-muted">Savings</span>
                <div className="vendor-economics-bar-track">
                  <div
                    className="vendor-economics-bar-fill vendor-economics-bar-fill-savings bar-grow-horizontal"
                    style={{ width: `${savingsPercent}%` }}
                  />
                </div>
                <span className="vendor-economics-bar-value text-small">
                  {formatCurrency(allocation.individual_savings_rs)}
                </span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function GroupEconomics({ entry }) {
  const decision = entry.decision;
  const allocations = decision.per_vendor_allocation ?? [];
  const savingsPercent = getSavingsPercent(decision.savings_rs, decision.individual_cost_total_rs);

  return (
    <Card className="vendor-economics-card">
      <div className="card-header-row">
        <span className="text-label">{decision.group_id}</span>
        <span className="text-small text-muted">
          {savingsPercent !== null ? `${formatPercent(savingsPercent)} lower than individual cost` : ""}
        </span>
      </div>

      <div className="vendor-economics-totals">
        <div>
          <span className="text-small text-muted">Individual cost (total)</span>
          <p className="text-metric">{formatCurrency(decision.individual_cost_total_rs)}</p>
        </div>
        <div>
          <span className="text-small text-muted">Collaborative cost</span>
          <p className="text-metric">{formatCurrency(decision.collaborative_cost_rs)}</p>
        </div>
        <div>
          <span className="text-small text-muted">Savings</span>
          <p className="text-metric text-metric-positive">{formatCurrency(decision.savings_rs)}</p>
        </div>
      </div>

      {allocations.length > 0 && (
        <>
          <span className="text-label">Cost share &amp; savings by vendor</span>
          <VendorEconomicsBars allocations={allocations} />
          <AllocationTable allocations={allocations} />
        </>
      )}
    </Card>
  );
}

function VendorEconomics({ finalSelection }) {
  const selectedResults = finalSelection?.selected_results ?? [];

  return (
    <section className="page-section" aria-labelledby="vendor-economics-heading">
      <h2 id="vendor-economics-heading" className="section-title">
        Vendor Economics
      </h2>

      {selectedResults.length === 0 ? (
        <EmptyState
          icon="—"
          title="No savings breakdown is available."
          description="A cost-share breakdown will appear here once a collaborative procurement group is selected."
        />
      ) : (
        <div className="vendor-economics-list">
          {selectedResults.map((entry) => (
            <GroupEconomics key={entry.decision.group_id} entry={entry} />
          ))}
        </div>
      )}
    </section>
  );
}

export default VendorEconomics;
