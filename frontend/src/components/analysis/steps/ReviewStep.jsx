// UI-4 -- Step 5. A human-readable summary of REAL current form state --
// no result preview, no predicted savings/decision (this phase's own
// explicit "do not show predicted savings before the backend analysis"
// rule). Supersedes the old dev-only RequestPreview.jsx (deleted --
// its own docstring called itself a Phase-7D-era placeholder; a raw JSON
// dump is the opposite of "guided/premium" for an end user). Every value
// shown here is read directly from `formState` -- nothing is invented,
// and nothing here computes a decision or savings figure.

import Button from "../../common/Button";
import Card from "../../common/Card";
import ErrorState from "../../common/ErrorState";
import { STEPS } from "../wizardSteps";

const LOCATION_LABELS = {
  VENDOR_SPECIFIC_APPROXIMATE: "Vendor-specific (approximate)",
  LOCALITY_CENTROID_PROXY: "Locality centroid (proxy)",
  MISSING: "Missing",
};

function describeDemandEvidence(vendor) {
  if (vendor.userProvidedQ.trim()) return `${vendor.userProvidedQ} kg/day (user-provided)`;
  if (vendor.diaryRecordsText.trim()) return `Diary: ${vendor.diaryRecordsText}`;
  if (vendor.peerQValuesText.trim()) return `Peer: ${vendor.peerQValuesText}`;
  return "No demand evidence yet";
}

function ReviewSection({ title, stepIndex, onEdit, children }) {
  return (
    <div className="review-section">
      <div className="card-header-row">
        <span className="text-label">{title}</span>
        <Button type="button" variant="ghost" onClick={() => onEdit(stepIndex)}>
          Edit
        </Button>
      </div>
      {children}
    </div>
  );
}

// The primary action button is `type="submit"` with NO onClick of its
// own -- the wrapping <form>'s single onSubmit handler (AnalysisForm.jsx)
// is what actually calls onAnalyze, so clicking the button and pressing
// Enter in any field on this step both go through the exact same code
// path, never two.
function ReviewStep({ formState, onEditStep, isSubmitting, submissionError }) {
  const vendorsWithDemand = formState.vendors.filter((vendor) => describeDemandEvidence(vendor) !== "No demand evidence yet").length;

  return (
    <>
      <p className="text-body">Check your inputs before running the decision engine.</p>

      <Card variant="elevated" className="review-summary-card animate-in">
        <span className="text-label">Ready to Analyze</span>
        <p className="card-title review-commodity-title">{formState.commodityId || "—"}</p>

        <div className="decision-preview-metrics">
          <div>
            <span className="text-metric">{formState.vendors.length}</span>
            <p className="text-small text-muted">Vendor(s)</p>
          </div>
          <div>
            <span className="text-metric">{formState.dMaxKm || "—"}</span>
            <p className="text-small text-muted">D_MAX (km)</p>
          </div>
          <div>
            <span className="text-metric">{formState.traderMargin || "—"}</span>
            <p className="text-small text-muted">Trader margin</p>
          </div>
        </div>

        <ReviewSection title="Procurement Context" stepIndex={0} onEdit={onEditStep}>
          <p className="text-small">Commodity: {formState.commodityId || "—"}</p>
          <p className="text-small">Evaluation date: {formState.date || "—"}</p>
          <p className="text-small">
            Wholesale price:{" "}
            {formState.wholesalePriceKnown ? `${formState.wholesalePriceValue || "—"} Rs/kg` : "Not provided"}
          </p>
        </ReviewSection>

        <ReviewSection title="Commodity Constraints" stepIndex={1} onEdit={onEditStep}>
          <p className="text-small">Freshness window: {formState.freshnessWindowDays || "Not set"}</p>
          <p className="text-small">MOQ: {formState.moqKg || "Not set"}</p>
        </ReviewSection>

        <ReviewSection title="Procurement Configuration" stepIndex={2} onEdit={onEditStep}>
          <p className="text-small">D_MAX: {formState.dMaxKm || "—"} km</p>
          <p className="text-small">Trader margin: {formState.traderMargin || "—"}</p>
          <p className="text-small">
            Transport tiers: {formState.transportTiers.length} tier(s)
          </p>
        </ReviewSection>

        <ReviewSection title="Vendors" stepIndex={3} onEdit={onEditStep}>
          <p className="text-small">{formState.vendors.length} vendor(s) — {vendorsWithDemand} with demand evidence</p>
          <ul className="review-vendor-list">
            {formState.vendors.map((vendor) => (
              <li key={vendor.localId} className="text-small">
                <span className="review-vendor-bullet" aria-hidden="true">●</span>
                {vendor.vendorId.trim() || "Untitled vendor"} — {LOCATION_LABELS[vendor.locationStatus]}
              </li>
            ))}
          </ul>
        </ReviewSection>

        <div className="review-actions">
          <Button type="button" variant="secondary" onClick={() => onEditStep(STEPS.length - 2)}>
            ← Back
          </Button>
          <Button type="submit" variant="primary" isLoading={isSubmitting}>
            {isSubmitting ? "Analyzing Procurement…" : "Analyze Procurement"}
          </Button>
        </div>
        <p className="text-small text-muted">Your inputs will be validated before the analysis runs.</p>
      </Card>

      {submissionError && <ErrorState title="Analysis request failed" description={submissionError} />}
    </>
  );
}

export default ReviewStep;
