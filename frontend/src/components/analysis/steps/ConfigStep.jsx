// UI-4 -- Step 3. dMaxKm/traderMargin fields and the transport-tier
// list/add/remove behavior are all UNCHANGED (same field names, same
// required-number validation, same useProcurementForm functions) --
// TransportTierRow.jsx itself is untouched; only the surrounding section
// copy/labels and card spacing are new.

import Button from "../../common/Button";
import FormField from "../FormField";
import TransportTierRow from "../TransportTierRow";

function ConfigStep({ formState, errors, onTextField, onUpdateTier, onAddTier, onRemoveTier }) {
  const hasGeneralTierError = Boolean(errors.fields.transportTiersGeneral);

  return (
    <>
      <p className="text-body">
        Define the geographic and cost rules used to evaluate candidate procurement groups.
      </p>

      <div className="form-field-row">
        <FormField
          id="dMaxKm"
          label="Maximum compatible distance (D_MAX, km)"
          error={errors.fields.dMaxKm}
          hint="Maximum distance allowed between compatible vendors"
        >
          <input id="dMaxKm" type="number" step="any" value={formState.dMaxKm} onChange={onTextField("dMaxKm")} />
        </FormField>
        <FormField
          id="traderMargin"
          label="Trader margin (ratio, e.g. 0.10)"
          error={errors.fields.traderMargin}
          hint="Margin used in procurement cost calculations"
        >
          <input
            id="traderMargin"
            type="number"
            step="any"
            value={formState.traderMargin}
            onChange={onTextField("traderMargin")}
          />
        </FormField>
      </div>

      <div className="wizard-subsection">
        <span className="text-label">Transport tiers</span>
        {hasGeneralTierError && <span className="form-field-error">{errors.fields.transportTiersGeneral}</span>}
        <div className="transport-tier-list">
          {formState.transportTiers.map((tier, index) => (
            <TransportTierRow
              key={tier.localId}
              tier={tier}
              index={index}
              errors={errors.transportTiers[tier.localId]}
              canRemove={formState.transportTiers.length > 1}
              onChange={onUpdateTier}
              onRemove={onRemoveTier}
            />
          ))}
        </div>
        <Button type="button" variant="outline" onClick={onAddTier}>
          + Add Transport Tier
        </Button>
      </div>
    </>
  );
}

export default ConfigStep;
