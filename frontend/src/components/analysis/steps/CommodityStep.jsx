// UI-4 -- Step 2. Fields extracted UNCHANGED from the previous
// single-page AnalysisForm.jsx: both fields optional, exact same hint
// wording (this phase's own explicit "do not change wording if it would
// change the meaning of the contract" instruction).

import FormField from "../FormField";

function CommodityStep({ formState, errors, onTextField }) {
  return (
    <>
      <p className="text-body">Add constraints that affect whether a procurement group is feasible.</p>

      <div className="form-field-row">
        <FormField
          id="freshnessWindowDays"
          label="Freshness window (days)"
          error={errors.fields.freshnessWindowDays}
          hint="Optional — leave blank if freshness does not bind"
        >
          <input
            id="freshnessWindowDays"
            type="number"
            step="1"
            value={formState.freshnessWindowDays}
            onChange={onTextField("freshnessWindowDays")}
          />
        </FormField>
        <FormField
          id="moqKg"
          label="Minimum order quantity (MOQ, kg)"
          error={errors.fields.moqKg}
          hint="Optional — leave blank if no MOQ applies"
        >
          <input id="moqKg" type="number" step="any" value={formState.moqKg} onChange={onTextField("moqKg")} />
        </FormField>
      </div>
    </>
  );
}

export default CommodityStep;
