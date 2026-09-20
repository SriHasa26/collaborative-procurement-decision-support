// UI-5 -- one group's per-vendor cost/savings allocation
// (backend/models/contracts.py's PerVendorAllocation, via
// GroupDecisionResult.per_vendor_allocation). Extracted from the former
// FinalSelectionSection.jsx (Phase 7E) into its own reusable component --
// both SelectedGroupCard.jsx and CandidateGroupRow.jsx need this exact
// same table, and duplicating it would risk the two copies silently
// drifting apart. Logic is unchanged from the Phase 7E original: render
// nothing if there is no allocation data, never fabricate a row.

import { formatCurrency } from "./resultHelpers";

function AllocationTable({ allocations }) {
  if (!allocations || allocations.length === 0) return null;
  return (
    <div className="history-table-wrapper">
      <table className="history-table allocation-table">
        <thead>
          <tr>
            <th scope="col">Vendor</th>
            <th scope="col">Cost share (Rs)</th>
            <th scope="col">Individual savings (Rs)</th>
            <th scope="col">Consumption time (days)</th>
          </tr>
        </thead>
        <tbody>
          {allocations.map((allocation) => (
            <tr key={allocation.vendor_id}>
              <td>{allocation.vendor_id}</td>
              <td>{formatCurrency(allocation.share_rs)}</td>
              <td>{formatCurrency(allocation.individual_savings_rs)}</td>
              <td>{allocation.consumption_time_days}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AllocationTable;
