// Phase 7C -- converts validated form state into the EXACT request shape
// backend/api/schemas.py's ProcurementAnalysisRequest expects. This module
// prepares the payload only -- it never sends it (no fetch, no import of
// frontend/src/api/procurementApi.js or client.js). Backend submission is
// Phase 7D's job.
//
// Call buildAnalysisPayload() only after validateAnalysisForm() has
// returned { isValid: true } -- this function assumes every field it reads
// is already known to be structurally parseable, and throws (rather than
// silently emitting a malformed payload) if that assumption is violated,
// since a corrupt "prepared request" would be worse than a visible error.
//
// FIELD-MAPPING NOTE (discrepancy documented, not "fixed" -- the backend
// is frozen for this phase, per reports/phase7c_procurement_analysis_form.md
// Section 2): ProcurementAnalysisRequest carries TWO independent
// commodity_id fields -- `commodity.commodity_id` and `context.commodity_id`
// -- with no cross-field validator enforcing they match. Asking the user
// to type the same commodity twice would be confusing UX with no benefit,
// so this form collects ONE `commodityId` value (single source of truth,
// initialFormState.js) and deliberately populates both request fields from
// it. This is a frontend UX decision, not a backend contract change.

import { parseOptionalNumber, parseOptionalNumberList, parseRequiredNumber, EMPTY, INVALID } from "./formNumbers.js";

function requireNumber(rawValue, fieldDescription) {
  const parsed = parseRequiredNumber(rawValue);
  if (parsed === EMPTY || parsed === INVALID) {
    throw new Error(`buildAnalysisPayload: expected a valid, already-validated number for ${fieldDescription}`);
  }
  return parsed;
}

function optionalNumber(rawValue, fieldDescription) {
  const parsed = parseOptionalNumber(rawValue);
  if (parsed === INVALID) {
    throw new Error(`buildAnalysisPayload: expected a valid, already-validated number for ${fieldDescription}`);
  }
  return parsed; // number or null
}

function optionalNumberList(rawValue, fieldDescription) {
  const parsed = parseOptionalNumberList(rawValue);
  if (parsed === INVALID) {
    throw new Error(`buildAnalysisPayload: expected a valid, already-validated number list for ${fieldDescription}`);
  }
  return parsed; // array, or null
}

function buildVendorSubmission(vendor) {
  const isLocationMissing = vendor.locationStatus === "MISSING";

  return {
    vendor_id: vendor.vendorId.trim(),
    location: {
      status: vendor.locationStatus,
      lat: isLocationMissing ? null : optionalNumber(vendor.lat, `vendor "${vendor.vendorId}" latitude`),
      lon: isLocationMissing ? null : optionalNumber(vendor.lon, `vendor "${vendor.vendorId}" longitude`),
    },
    individual_price_rs_per_kg: optionalNumber(
      vendor.individualPriceRsPerKg,
      `vendor "${vendor.vendorId}" individual price`
    ),
    practical_horizon_days: optionalNumber(
      vendor.practicalHorizonDays,
      `vendor "${vendor.vendorId}" practical horizon`
    ),
    user_provided_q_i: optionalNumber(vendor.userProvidedQ, `vendor "${vendor.vendorId}" user-provided demand`),
    diary_records: optionalNumberList(vendor.diaryRecordsText, `vendor "${vendor.vendorId}" diary records`),
    peer_q_values: optionalNumberList(vendor.peerQValuesText, `vendor "${vendor.vendorId}" peer quantities`),
  };
}

function buildTransportTier(tier) {
  return {
    capacity_kg: requireNumber(tier.capacityKg, "a transport tier's capacity"),
    cost_rs: requireNumber(tier.costRs, "a transport tier's cost"),
  };
}

export function buildAnalysisPayload(formState) {
  const commodityId = formState.commodityId.trim();

  return {
    commodity: {
      commodity_id: commodityId,
      freshness_window_days: optionalNumber(formState.freshnessWindowDays, "freshness window (days)"),
      moq_kg: optionalNumber(formState.moqKg, "MOQ (kg)"),
    },
    context: {
      commodity_id: commodityId,
      date: formState.date,
      wholesale_price: formState.wholesalePriceKnown
        ? {
            value_rs_per_kg: requireNumber(formState.wholesalePriceValue, "wholesale price"),
            geographic_level: formState.wholesalePriceGeoLevel,
          }
        : null,
    },
    vendor_submissions: formState.vendors.map(buildVendorSubmission),
    config: {
      d_max_km: requireNumber(formState.dMaxKm, "maximum compatible distance (D_max)"),
      trader_margin: requireNumber(formState.traderMargin, "trader margin"),
      transport_tiers: formState.transportTiers.map(buildTransportTier),
    },
  };
}
