// Phase 7C -- one vendor's fields, matching backend/api/schemas.py's
// VendorSubmissionRequest exactly: vendor_id, location (status/lat/lon),
// individual_price_rs_per_kg, practical_horizon_days, user_provided_q_i,
// diary_records, peer_q_values. No field beyond these is collected --
// no name, phone, address, or other personal/reputation data exists in
// the backend contract, so none is asked for here.

import Button from "../common/Button";
import FormField from "./FormField";

const LOCATION_STATUS_OPTIONS = [
  { value: "VENDOR_SPECIFIC_APPROXIMATE", label: "Vendor-specific (approximate)" },
  { value: "LOCALITY_CENTROID_PROXY", label: "Locality centroid (proxy)" },
  { value: "MISSING", label: "Missing" },
];

function VendorForm({ vendor, index, errors, canRemove, onChange, onRemove }) {
  const fieldErrors = errors || {};
  const isLocationMissing = vendor.locationStatus === "MISSING";

  const fieldId = (name) => `vendor-${vendor.localId}-${name}`;
  const handleChange = (field) => (event) => onChange(vendor.localId, field, event.target.value);

  return (
    <div className="vendor-card">
      <div className="card-header-row">
        <span className="card-title">Vendor {index + 1}</span>
        <Button variant="secondary" onClick={() => onRemove(vendor.localId)} disabled={!canRemove}>
          Remove Vendor
        </Button>
      </div>

      <div className="form-section-body">
        <FormField id={fieldId("vendorId")} label="Vendor ID" error={fieldErrors.vendorId}>
          <input
            id={fieldId("vendorId")}
            type="text"
            value={vendor.vendorId}
            onChange={handleChange("vendorId")}
          />
        </FormField>

        <FormField id={fieldId("locationStatus")} label="Location precision">
          <select
            id={fieldId("locationStatus")}
            value={vendor.locationStatus}
            onChange={handleChange("locationStatus")}
          >
            {LOCATION_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </FormField>

        {!isLocationMissing && (
          <div className="form-field-row">
            <FormField id={fieldId("lat")} label="Latitude" error={fieldErrors.lat} hint="Optional">
              <input id={fieldId("lat")} type="number" step="any" value={vendor.lat} onChange={handleChange("lat")} />
            </FormField>
            <FormField id={fieldId("lon")} label="Longitude" error={fieldErrors.lon} hint="Optional">
              <input id={fieldId("lon")} type="number" step="any" value={vendor.lon} onChange={handleChange("lon")} />
            </FormField>
          </div>
        )}

        <FormField
          id={fieldId("individualPriceRsPerKg")}
          label="Individual price (Rs/kg)"
          error={fieldErrors.individualPriceRsPerKg}
          hint="Optional"
        >
          <input
            id={fieldId("individualPriceRsPerKg")}
            type="number"
            step="any"
            value={vendor.individualPriceRsPerKg}
            onChange={handleChange("individualPriceRsPerKg")}
          />
        </FormField>

        <FormField
          id={fieldId("practicalHorizonDays")}
          label="Practical procurement horizon (days)"
          error={fieldErrors.practicalHorizonDays}
          hint="Optional"
        >
          <input
            id={fieldId("practicalHorizonDays")}
            type="number"
            step="1"
            value={vendor.practicalHorizonDays}
            onChange={handleChange("practicalHorizonDays")}
          />
        </FormField>

        <FormField
          id={fieldId("userProvidedQ")}
          label="User-provided demand (kg/day)"
          error={fieldErrors.userProvidedQ}
          hint="Optional -- a directly stated daily quantity"
        >
          <input
            id={fieldId("userProvidedQ")}
            type="number"
            step="any"
            value={vendor.userProvidedQ}
            onChange={handleChange("userProvidedQ")}
          />
        </FormField>

        <FormField
          id={fieldId("diaryRecordsText")}
          label="Diary records (kg/day)"
          error={fieldErrors.diaryRecordsText}
          hint="Optional, comma-separated -- e.g. 8, 9.5, 10"
        >
          <input
            id={fieldId("diaryRecordsText")}
            type="text"
            value={vendor.diaryRecordsText}
            onChange={handleChange("diaryRecordsText")}
          />
        </FormField>

        <FormField
          id={fieldId("peerQValuesText")}
          label="Peer quantities (kg/day)"
          error={fieldErrors.peerQValuesText}
          hint="Optional, comma-separated -- similar vendors' quantities"
        >
          <input
            id={fieldId("peerQValuesText")}
            type="text"
            value={vendor.peerQValuesText}
            onChange={handleChange("peerQValuesText")}
          />
        </FormField>
      </div>
    </div>
  );
}

export default VendorForm;
