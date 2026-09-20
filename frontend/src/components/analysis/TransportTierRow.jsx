// Phase 7C -- one transport tier's fields, matching
// backend/api/schemas.py's TransportTierRequest exactly: capacity_kg, cost_rs.

import Button from "../common/Button";
import FormField from "./FormField";

function TransportTierRow({ tier, index, errors, canRemove, onChange, onRemove }) {
  const fieldErrors = errors || {};
  const fieldId = (name) => `tier-${tier.localId}-${name}`;
  const handleChange = (field) => (event) => onChange(tier.localId, field, event.target.value);

  return (
    <div className="transport-tier-row">
      <span className="text-label">Tier {index + 1}</span>
      <div className="form-field-row">
        <FormField id={fieldId("capacityKg")} label="Capacity (kg)" error={fieldErrors.capacityKg}>
          <input
            id={fieldId("capacityKg")}
            type="number"
            step="any"
            value={tier.capacityKg}
            onChange={handleChange("capacityKg")}
          />
        </FormField>
        <FormField id={fieldId("costRs")} label="Cost (Rs)" error={fieldErrors.costRs}>
          <input
            id={fieldId("costRs")}
            type="number"
            step="any"
            value={tier.costRs}
            onChange={handleChange("costRs")}
          />
        </FormField>
        <Button variant="secondary" onClick={() => onRemove(tier.localId)} disabled={!canRemove}>
          Remove Tier
        </Button>
      </div>
    </div>
  );
}

export default TransportTierRow;
