// Phase 7C -- FRONTEND STRUCTURAL validation only ("Layer 1" per this
// phase's spec): is the text a well-formed number, is a required field
// present, are vendor IDs distinct enough to build a coherent request.
//
// This module NEVER duplicates Phase 6B's DOMAIN validation ("Layer 2"):
// it does not reject a negative price, a negative quantity, an
// out-of-range coordinate, or "insufficient evidence" -- those are
// backend/services/validation.py and eligibility.py's job, and they
// correctly route an affected vendor to VALIDATION_ERROR or ABSTAIN
// without blocking the rest of the batch. Rejecting that data here would
// prevent the user from ever sending a request that legitimately
// exercises those backend code paths.

import { parseOptionalNumber, parseOptionalNumberList, parseRequiredNumber, EMPTY, INVALID } from "./formNumbers.js";

const REQUIRED_NUMBER_MESSAGE = "Enter a valid number.";
const REQUIRED_FIELD_MESSAGE = "This field is required.";
const OPTIONAL_NUMBER_MESSAGE = "Enter a valid number, or leave this field blank.";
const OPTIONAL_LIST_MESSAGE = "Enter comma-separated numbers (e.g. 8, 9.5, 10), or leave this field blank.";

function validateRequiredNumberField(rawValue) {
  const parsed = parseRequiredNumber(rawValue);
  if (parsed === EMPTY) return REQUIRED_FIELD_MESSAGE;
  if (parsed === INVALID) return REQUIRED_NUMBER_MESSAGE;
  return null;
}

function validateOptionalNumberField(rawValue) {
  const parsed = parseOptionalNumber(rawValue);
  if (parsed === INVALID) return OPTIONAL_NUMBER_MESSAGE;
  return null;
}

function validateOptionalListField(rawValue) {
  const parsed = parseOptionalNumberList(rawValue);
  if (parsed === INVALID) return OPTIONAL_LIST_MESSAGE;
  return null;
}

function validateVendor(vendor) {
  const errors = {};

  if (!vendor.vendorId.trim()) {
    errors.vendorId = REQUIRED_FIELD_MESSAGE;
  }

  const isLocationMissing = vendor.locationStatus === "MISSING";
  if (!isLocationMissing) {
    const latError = validateOptionalNumberField(vendor.lat);
    if (latError) errors.lat = latError;
    const lonError = validateOptionalNumberField(vendor.lon);
    if (lonError) errors.lon = lonError;
  }

  const priceError = validateOptionalNumberField(vendor.individualPriceRsPerKg);
  if (priceError) errors.individualPriceRsPerKg = priceError;

  const horizonError = validateOptionalNumberField(vendor.practicalHorizonDays);
  if (horizonError) errors.practicalHorizonDays = horizonError;

  const demandError = validateOptionalNumberField(vendor.userProvidedQ);
  if (demandError) errors.userProvidedQ = demandError;

  const diaryError = validateOptionalListField(vendor.diaryRecordsText);
  if (diaryError) errors.diaryRecordsText = diaryError;

  const peerError = validateOptionalListField(vendor.peerQValuesText);
  if (peerError) errors.peerQValuesText = peerError;

  return errors;
}

function validateTransportTier(tier) {
  const errors = {};
  const capacityError = validateRequiredNumberField(tier.capacityKg);
  if (capacityError) errors.capacityKg = capacityError;
  const costError = validateRequiredNumberField(tier.costRs);
  if (costError) errors.costRs = costError;
  return errors;
}

export function validateAnalysisForm(formState) {
  const errors = {
    fields: {},
    vendors: {},
    transportTiers: {},
  };

  if (!formState.commodityId.trim()) {
    errors.fields.commodityId = REQUIRED_FIELD_MESSAGE;
  }

  if (!formState.date.trim()) {
    errors.fields.date = REQUIRED_FIELD_MESSAGE;
  }

  const freshnessError = validateOptionalNumberField(formState.freshnessWindowDays);
  if (freshnessError) errors.fields.freshnessWindowDays = freshnessError;

  const moqError = validateOptionalNumberField(formState.moqKg);
  if (moqError) errors.fields.moqKg = moqError;

  if (formState.wholesalePriceKnown) {
    const wholesaleError = validateRequiredNumberField(formState.wholesalePriceValue);
    if (wholesaleError) errors.fields.wholesalePriceValue = wholesaleError;
  }

  const dMaxError = validateRequiredNumberField(formState.dMaxKm);
  if (dMaxError) errors.fields.dMaxKm = dMaxError;

  const marginError = validateRequiredNumberField(formState.traderMargin);
  if (marginError) errors.fields.traderMargin = marginError;

  // -- Vendors: at least one is required to build a coherent request
  // (a zero-vendor request is structurally pointless, not a domain
  // rule -- backend/services/validation.py separately flags an empty
  // vendor collection as EMPTY_VENDOR_COLLECTION). Vendor IDs must be
  // distinct: backend/services/group_formation.py keys vendors by
  // vendor_id in a plain dict, so duplicate IDs would silently collide
  // rather than being classified as ABSTAIN/VALIDATION_ERROR -- this is
  // a structural request-integrity check, not a business rule about
  // savings or eligibility.
  if (formState.vendors.length === 0) {
    errors.fields.vendorsGeneral = "Add at least one vendor.";
  }

  const seenVendorIds = new Map();
  formState.vendors.forEach((vendor) => {
    const vendorErrors = validateVendor(vendor);
    const trimmedId = vendor.vendorId.trim();
    if (trimmedId) {
      seenVendorIds.set(trimmedId, (seenVendorIds.get(trimmedId) || 0) + 1);
    }
    if (Object.keys(vendorErrors).length > 0) {
      errors.vendors[vendor.localId] = vendorErrors;
    }
  });
  const duplicateIds = [...seenVendorIds.entries()].filter(([, count]) => count > 1).map(([id]) => id);
  if (duplicateIds.length > 0) {
    errors.fields.vendorsGeneral = `Vendor IDs must be unique. Duplicated: ${duplicateIds.join(", ")}.`;
  }

  // -- Transport tiers: at least one is required for the config to be
  // usable (an empty tier list cannot price any quantity) -- again a
  // structural completeness check, not a business rule.
  if (formState.transportTiers.length === 0) {
    errors.fields.transportTiersGeneral = "Add at least one transport tier.";
  }
  formState.transportTiers.forEach((tier) => {
    const tierErrors = validateTransportTier(tier);
    if (Object.keys(tierErrors).length > 0) {
      errors.transportTiers[tier.localId] = tierErrors;
    }
  });

  const isValid =
    Object.keys(errors.fields).length === 0 &&
    Object.keys(errors.vendors).length === 0 &&
    Object.keys(errors.transportTiers).length === 0;

  return { isValid, errors };
}
