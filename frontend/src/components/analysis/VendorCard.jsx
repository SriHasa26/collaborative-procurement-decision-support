// UI-4 -- collapsible wrapper around the EXISTING, UNCHANGED VendorForm
// (Phase 7C) -- no vendor field was removed, renamed, or re-implemented;
// this component only decides whether to show a compact summary or the
// full (unmodified) editing form. "✓ Complete" / "Needs information" is
// read directly from `errors` (validateAnalysisForm's own real per-vendor
// error object, refreshed by the parent step -- see
// steps/VendorNetworkStep.jsx) -- never a guessed or cosmetic state. The
// summary line shows whichever REAL demand evidence the vendor actually
// has (user-provided, diary, or peer), never a fabricated value.

import Button from "../common/Button";
import Badge from "../common/Badge";
import VendorForm from "./VendorForm";

const LOCATION_LABELS = {
  VENDOR_SPECIFIC_APPROXIMATE: "Vendor-specific (approximate)",
  LOCALITY_CENTROID_PROXY: "Locality centroid (proxy)",
  MISSING: "Missing",
};

function describeDemandEvidence(vendor) {
  if (vendor.userProvidedQ.trim()) return `${vendor.userProvidedQ} kg/day (user-provided)`;
  if (vendor.diaryRecordsText.trim()) return `Diary records: ${vendor.diaryRecordsText}`;
  if (vendor.peerQValuesText.trim()) return `Peer quantities: ${vendor.peerQValuesText}`;
  return "No demand evidence yet";
}

function VendorCard({ vendor, index, errors, isExpanded, isComplete, canRemove, onToggleExpand, onChange, onRemove }) {
  // UI-8 -- `key` differs between the two branches (though both render a
  // literal <div> at the same position) specifically so React treats a
  // toggle as a real unmount+mount rather than patching the existing
  // node's classes in place -- the latter would never actually replay
  // .animate-in's CSS animation, since that class name would stay
  // continuously present across the toggle either way.
  if (isExpanded) {
    return (
      <div key="expanded" className="vendor-card is-expanded animate-in">
        <VendorForm vendor={vendor} index={index} errors={errors} canRemove={canRemove} onChange={onChange} onRemove={onRemove} />
        <div className="vendor-card-done-row">
          <Button type="button" variant="primary" onClick={onToggleExpand}>
            Done Editing
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div key="summary" className="vendor-card vendor-card-summary animate-in">
      <div className="card-header-row">
        <div>
          <span className="text-label">Vendor {index + 1}</span>
          <p className="card-title">{vendor.vendorId.trim() || "Untitled vendor"}</p>
        </div>
        <Badge variant={isComplete ? "success" : "warning"}>{isComplete ? "✓ Complete" : "Needs information"}</Badge>
      </div>

      <p className="text-small text-muted">Location: {LOCATION_LABELS[vendor.locationStatus]}</p>
      <p className="text-small text-muted">Demand: {describeDemandEvidence(vendor)}</p>

      <div className="vendor-card-actions">
        <Button type="button" variant="outline" onClick={onToggleExpand}>
          Edit Vendor
        </Button>
        <Button type="button" variant="ghost" onClick={() => onRemove(vendor.localId)} disabled={!canRemove}>
          Remove
        </Button>
      </div>
    </div>
  );
}

export default VendorCard;
