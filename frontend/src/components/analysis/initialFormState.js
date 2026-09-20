// Phase 7C -- factory functions for the analysis form's initial state.
//
// Every field starts as an empty string (or the first enum option, since a
// <select> always has a selected value) -- no economic/domain value
// (MOQ, D_max, price, freshness, demand) is ever pre-filled with an
// invented default. The only UI-only defaults are: one initial vendor row,
// one initial transport-tier row, and enum selects defaulting to their
// first listed option -- all purely structural, never a domain assumption.

let localIdCounter = 0;
function nextLocalId(prefix) {
  localIdCounter += 1;
  return `${prefix}-${localIdCounter}`;
}

export function createInitialVendor() {
  return {
    localId: nextLocalId("vendor"),
    vendorId: "",
    locationStatus: "VENDOR_SPECIFIC_APPROXIMATE",
    lat: "",
    lon: "",
    individualPriceRsPerKg: "",
    practicalHorizonDays: "",
    userProvidedQ: "",
    diaryRecordsText: "",
    peerQValuesText: "",
  };
}

export function createInitialTransportTier() {
  return {
    localId: nextLocalId("tier"),
    capacityKg: "",
    costRs: "",
  };
}

export function createInitialFormState() {
  return {
    // One shared commodity identifier -- used for BOTH the request's
    // `commodity.commodity_id` and `context.commodity_id` fields (see
    // buildAnalysisPayload.js's docstring for why these two structurally
    // separate backend fields are deliberately driven from one input).
    commodityId: "",
    freshnessWindowDays: "",
    moqKg: "",

    date: "",
    wholesalePriceKnown: false,
    wholesalePriceValue: "",
    wholesalePriceGeoLevel: "MANDI_LEVEL",

    dMaxKm: "",
    traderMargin: "",
    transportTiers: [createInitialTransportTier()],

    vendors: [createInitialVendor()],
  };
}
