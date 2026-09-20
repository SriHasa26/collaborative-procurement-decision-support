// Phase 7C -- single source of truth for the procurement analysis form.
// Owns all form state and every mutation of it; AnalysisForm.jsx and its
// child components only read from and call functions returned by this
// hook -- no duplicate copy of the vendor list, commodity data, or config
// exists anywhere else.
//
// This hook does NOT call the backend. `prepare()` only validates and
// builds the payload into local state -- see buildAnalysisPayload.js and
// validateAnalysisForm.js. Backend submission is Phase 7D's job.

import { useCallback, useState } from "react";
import { buildAnalysisPayload } from "./buildAnalysisPayload.js";
import { createInitialFormState, createInitialTransportTier, createInitialVendor } from "./initialFormState.js";
import { validateAnalysisForm } from "./validateAnalysisForm.js";

export function useProcurementForm() {
  const [formState, setFormState] = useState(createInitialFormState);
  const [errors, setErrors] = useState({ fields: {}, vendors: {}, transportTiers: {} });
  const [preparedPayload, setPreparedPayload] = useState(null);

  const updateField = useCallback((field, value) => {
    setFormState((prev) => ({ ...prev, [field]: value }));
    setPreparedPayload(null); // any edit invalidates a previously prepared payload
  }, []);

  const updateVendor = useCallback((localId, field, value) => {
    setFormState((prev) => ({
      ...prev,
      vendors: prev.vendors.map((vendor) => (vendor.localId === localId ? { ...vendor, [field]: value } : vendor)),
    }));
    setPreparedPayload(null);
  }, []);

  const addVendor = useCallback(() => {
    setFormState((prev) => ({ ...prev, vendors: [...prev.vendors, createInitialVendor()] }));
    setPreparedPayload(null);
  }, []);

  const removeVendor = useCallback((localId) => {
    setFormState((prev) => {
      // Vendor-removal safety: never let the list drop to zero silently.
      // The final vendor's row is kept (its remove control is disabled by
      // the UI -- see VendorForm.jsx) rather than being removed and
      // leaving a structurally empty vendor list.
      if (prev.vendors.length <= 1) return prev;
      return { ...prev, vendors: prev.vendors.filter((vendor) => vendor.localId !== localId) };
    });
    setPreparedPayload(null);
  }, []);

  const updateTransportTier = useCallback((localId, field, value) => {
    setFormState((prev) => ({
      ...prev,
      transportTiers: prev.transportTiers.map((tier) =>
        tier.localId === localId ? { ...tier, [field]: value } : tier
      ),
    }));
    setPreparedPayload(null);
  }, []);

  const addTransportTier = useCallback(() => {
    setFormState((prev) => ({ ...prev, transportTiers: [...prev.transportTiers, createInitialTransportTier()] }));
    setPreparedPayload(null);
  }, []);

  const removeTransportTier = useCallback((localId) => {
    setFormState((prev) => {
      if (prev.transportTiers.length <= 1) return prev;
      return { ...prev, transportTiers: prev.transportTiers.filter((tier) => tier.localId !== localId) };
    });
    setPreparedPayload(null);
  }, []);

  const resetForm = useCallback(() => {
    setFormState(createInitialFormState());
    setErrors({ fields: {}, vendors: {}, transportTiers: {} });
    setPreparedPayload(null);
  }, []);

  // Validates structurally and, if valid, builds the exact request
  // payload into `preparedPayload`. Never calls the backend.
  const prepare = useCallback(() => {
    const result = validateAnalysisForm(formState);
    setErrors(result.errors);

    if (!result.isValid) {
      setPreparedPayload(null);
      return { isValid: false, payload: null };
    }

    const payload = buildAnalysisPayload(formState);
    setPreparedPayload(payload);
    return { isValid: true, payload };
  }, [formState]);

  // UI-4 -- runs the EXACT SAME validateAnalysisForm() as prepare() (no
  // duplicate/parallel validation logic), refreshing `errors` without
  // requiring the WHOLE form to be valid or building a payload. This is
  // what the guided workflow's per-step "Continue" gating uses (see
  // components/analysis/wizardSteps.js's hasStepErrors(), which reads
  // exactly this same `errors` shape and only looks at one step's own
  // keys) -- prepare() itself is unchanged and remains the Review step's
  // final, whole-form check before actually submitting.
  const validateCurrentState = useCallback(() => {
    const result = validateAnalysisForm(formState);
    setErrors(result.errors);
    return result;
  }, [formState]);

  return {
    formState,
    errors,
    preparedPayload,
    updateField,
    updateVendor,
    addVendor,
    removeVendor,
    updateTransportTier,
    addTransportTier,
    removeTransportTier,
    resetForm,
    prepare,
    validateCurrentState,
  };
}
