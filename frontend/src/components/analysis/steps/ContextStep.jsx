// UI-4 -- Step 1. Fields and behavior extracted UNCHANGED from the
// previous single-page AnalysisForm.jsx (Phase 7C/7D): same field names,
// same required/optional behavior (commodityId/date required,
// wholesalePriceValue required only when wholesalePriceKnown is checked),
// same progressive-disclosure checkbox pattern. Only the surrounding
// layout/copy is new.

import FormField from "../FormField";

const GEOGRAPHIC_LEVEL_OPTIONS = [
  { value: "MANDI_LEVEL", label: "Mandi-level (market-specific)" },
  { value: "DISTRICT_LEVEL_PROXY", label: "District-level proxy" },
  { value: "UNKNOWN_GRANULARITY", label: "Unknown granularity" },
];

function ContextStep({ formState, errors, onTextField, onCheckboxField }) {
  return (
    <>
      <p className="text-body">Start with the commodity and evaluation date for this procurement decision.</p>

      <div className="form-field-row">
        <FormField id="commodityId" label="Commodity ID" error={errors.fields.commodityId}>
          <input id="commodityId" type="text" value={formState.commodityId} onChange={onTextField("commodityId")} />
        </FormField>

        <FormField id="date" label="Evaluation date" error={errors.fields.date}>
          <input id="date" type="date" value={formState.date} onChange={onTextField("date")} />
        </FormField>
      </div>

      <FormField id="wholesalePriceKnown" label="Wholesale price">
        <label className="checkbox-field">
          <input
            id="wholesalePriceKnown"
            type="checkbox"
            checked={formState.wholesalePriceKnown}
            onChange={onCheckboxField("wholesalePriceKnown")}
          />
          <span className="text-small">Wholesale price is known for this date</span>
        </label>
      </FormField>

      {formState.wholesalePriceKnown && (
        <div className="form-field-row">
          <FormField id="wholesalePriceValue" label="Wholesale price (Rs/kg)" error={errors.fields.wholesalePriceValue}>
            <input
              id="wholesalePriceValue"
              type="number"
              step="any"
              value={formState.wholesalePriceValue}
              onChange={onTextField("wholesalePriceValue")}
            />
          </FormField>
          <FormField id="wholesalePriceGeoLevel" label="Price geographic level">
            <select
              id="wholesalePriceGeoLevel"
              value={formState.wholesalePriceGeoLevel}
              onChange={onTextField("wholesalePriceGeoLevel")}
            >
              {GEOGRAPHIC_LEVEL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </FormField>
        </div>
      )}
    </>
  );
}

export default ContextStep;
