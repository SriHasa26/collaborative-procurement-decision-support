// Phase 7E -- Section D: per-vendor outcomes
// (backend/models/batch_contracts.py's VendorEligibilityResult, via
// batch_eligibility.{eligible,abstained,validation_error}_vendors).
//
// IMPORTANT: ABSTAIN and VALIDATION_ERROR are rendered with visually
// distinct badges (info vs. danger) and distinct labels -- they represent
// different concepts (insufficient evidence vs. malformed input,
// backend/models/enums.py's OutcomeKind) and must never be merged or
// look interchangeable, per this phase's explicit requirement.

import Badge from "../common/Badge";
import { getVendorOutcomes } from "./resultHelpers";

const OUTCOME_META = {
  OK: { label: "Eligible", variant: "success" },
  ABSTAIN: { label: "Abstained", variant: "info" },
  VALIDATION_ERROR: { label: "Validation error", variant: "danger" },
};

function VendorOutcomesTable({ batchEligibility }) {
  const vendors = getVendorOutcomes(batchEligibility);

  if (vendors.length === 0) {
    return <p className="text-small text-muted">No vendor submissions were recorded for this run.</p>;
  }

  return (
    <div className="history-table-wrapper">
      <table className="history-table vendor-outcomes-table">
        <thead>
          <tr>
            <th scope="col">Vendor ID</th>
            <th scope="col">Outcome</th>
            <th scope="col">Demand provenance</th>
            <th scope="col">Location status</th>
            <th scope="col">Explanation</th>
          </tr>
        </thead>
        <tbody>
          {vendors.map((vendor) => {
            const meta = OUTCOME_META[vendor.status] ?? { label: vendor.status, variant: "neutral" };
            return (
              <tr key={vendor.vendor_id}>
                <td>{vendor.vendor_id}</td>
                <td>
                  <Badge variant={meta.variant}>{meta.label}</Badge>
                </td>
                <td>{vendor.demand_provenance ?? "—"}</td>
                <td>{vendor.vendor_input?.location?.status ?? "—"}</td>
                <td className="vendor-outcomes-explanation">{vendor.reason_detail}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default VendorOutcomesTable;
