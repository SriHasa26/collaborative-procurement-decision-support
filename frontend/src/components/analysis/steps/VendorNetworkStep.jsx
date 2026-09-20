// UI-4 -- Step 4. Vendor add/remove/update all call the EXISTING,
// UNCHANGED useProcurementForm functions -- this component owns no
// vendor DATA of its own, only which vendor card is currently expanded
// (pure UI/navigation state, not submitted anywhere). A freshly-added
// vendor is auto-expanded (it is empty, so there is nothing useful to
// summarize yet); collapsing a card re-runs validateCurrentState() so its
// "✓ Complete"/"Needs information" badge reflects real, fresh validation
// state, never a stale or guessed one.

import { useEffect, useRef, useState } from "react";
import Button from "../../common/Button";
import VendorCard from "../VendorCard";

function VendorNetworkStep({ formState, errors, onUpdateVendor, onAddVendor, onRemoveVendor, onValidate }) {
  const [expandedVendorId, setExpandedVendorId] = useState(formState.vendors[0]?.localId ?? null);
  const previousCount = useRef(formState.vendors.length);

  useEffect(() => {
    if (formState.vendors.length > previousCount.current) {
      // A vendor was just added -- expand the newest one so the user can
      // fill it in immediately, without hunting for it in the list.
      setExpandedVendorId(formState.vendors[formState.vendors.length - 1].localId);
    }
    previousCount.current = formState.vendors.length;
  }, [formState.vendors]);

  function handleToggleExpand(localId) {
    if (expandedVendorId === localId) {
      onValidate(); // refresh completion state for the card that just collapsed
      setExpandedVendorId(null);
    } else {
      setExpandedVendorId(localId);
    }
  }

  const hasGeneralVendorError = Boolean(errors.fields.vendorsGeneral);

  return (
    <>
      <p className="text-body">Add the vendors participating in this procurement decision.</p>
      {hasGeneralVendorError && <span className="form-field-error">{errors.fields.vendorsGeneral}</span>}

      <div className="vendor-card-list">
        {formState.vendors.map((vendor, index) => {
          const vendorErrors = errors.vendors[vendor.localId];
          const isComplete = Boolean(vendor.vendorId.trim()) && !vendorErrors;
          return (
            <VendorCard
              key={vendor.localId}
              vendor={vendor}
              index={index}
              errors={vendorErrors}
              isExpanded={expandedVendorId === vendor.localId}
              isComplete={isComplete}
              canRemove={formState.vendors.length > 1}
              onToggleExpand={() => handleToggleExpand(vendor.localId)}
              onChange={onUpdateVendor}
              onRemove={onRemoveVendor}
            />
          );
        })}
      </div>

      <Button type="button" variant="outline" onClick={onAddVendor}>
        + Add Vendor
      </Button>
    </>
  );
}

export default VendorNetworkStep;
