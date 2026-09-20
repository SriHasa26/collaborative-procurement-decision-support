// UI-4 -- step metadata and per-step error gating for the guided analysis
// workflow. Operates ENTIRELY on validateAnalysisForm()'s existing,
// unmodified output shape ({fields, vendors, transportTiers}) -- it does
// not duplicate or reinterpret any validation rule, it only groups
// already-computed error keys by which step owns them. No field/step
// mapping here changes what is required vs optional; it only reflects
// validateAnalysisForm.js's own existing rules.

export const STEPS = [
  { key: "context", label: "Context", title: "Procurement Context" },
  { key: "commodity", label: "Commodity", title: "Commodity Constraints" },
  { key: "config", label: "Configuration", title: "Procurement Configuration" },
  { key: "vendors", label: "Vendors", title: "Vendor Network" },
  { key: "review", label: "Review", title: "Review & Analyze" },
];

const FIELD_KEYS_BY_STEP = {
  context: ["commodityId", "date", "wholesalePriceValue"],
  commodity: ["freshnessWindowDays", "moqKg"],
  config: ["dMaxKm", "traderMargin", "transportTiersGeneral"],
  vendors: ["vendorsGeneral"],
  review: [], // Review has no fields of its own -- see hasStepErrors below.
};

// True if `errors` (validateAnalysisForm's output) contains any error that
// belongs to `stepKey`. "review" is special: it is invalid whenever ANY
// step is invalid, since Review's own job is to gate final submission on
// the complete payload (this phase's own "Review -> Analyze must validate
// the complete payload" requirement).
export function hasStepErrors(errors, stepKey) {
  if (stepKey === "review") {
    return STEPS.slice(0, -1).some((step) => hasStepErrors(errors, step.key));
  }

  const fieldKeys = FIELD_KEYS_BY_STEP[stepKey] ?? [];
  if (fieldKeys.some((key) => errors.fields[key])) return true;

  if (stepKey === "config" && Object.keys(errors.transportTiers).length > 0) return true;
  if (stepKey === "vendors" && Object.keys(errors.vendors).length > 0) return true;

  return false;
}

// The first step (in order) that currently has an error -- used to jump
// the user back to exactly the right place if Review's final prepare()
// call finds the whole-form payload invalid (e.g. they used step
// navigation to revisit and break an earlier, previously-valid step).
export function findFirstInvalidStepIndex(errors) {
  return STEPS.findIndex((step) => hasStepErrors(errors, step.key));
}
