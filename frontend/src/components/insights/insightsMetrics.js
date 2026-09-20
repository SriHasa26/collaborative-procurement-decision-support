// UI-7 -- pure, deterministic aggregation over the SAME entries
// useHistoryData.js (UI-6) already produces: {run_id, created_at,
// commodity, run_status, detail: StoredRun|null}. `detail` is null for
// any run beyond useHistoryData's own bounded enrichment cap
// (HISTORY_DETAIL_FETCH_LIMIT) or whose individual detail fetch failed --
// every function below treats that honestly, contributing nothing to a
// metric it cannot support rather than guessing.
//
// CRITICAL BOUNDARY (same as results/resultHelpers.js and
// dashboard/dashboardMetrics.js): nothing here computes a procurement
// decision, savings figure, or eligibility outcome -- it only counts,
// sums, and groups values the backend already computed. Reuses
// getEntryDecisionFilterValue (history/historyFilters.js, UI-6) for the
// per-run "primary decision" classification and buildSavingsSeries
// (dashboard/dashboardMetrics.js, UI-3) for the savings-over-time series,
// rather than re-deriving either a second time.

import { getEntryDecisionFilterValue, DECISION_FILTER_OPTIONS } from "../history/historyFilters";

// Below this many CONSIDERED (detail-loaded) runs, a distribution/ranking
// visual would visually overstate what 0-1 data points can actually show
// -- callers show a plain, honest single-fact statement instead (Rule 4:
// "If only one run exists: do not overstate the distribution").
export const MIN_RUNS_FOR_DISTRIBUTION_VISUAL = 2;

// -- Decision Distribution (Section B) -----------------------------------
// One classification per RUN (its OWN primary decision, exactly
// DecisionHero.jsx's/getPrimaryDecisionState's own rule: the selected
// group's final_decision_state, or "no group selected" when none was
// chosen) -- distinct from dashboardMetrics.js's buildDashboardMetrics()
// decisionCounts, which counts every individual CANDIDATE GROUP's
// decision across all evaluated groups in all fetched runs. Both are
// valid, real metrics; they answer different questions and must not be
// confused with one another (see reports/ui7_procurement_insights.md
// Section 7).
export function buildDecisionDistribution(entries) {
  const considered = entries.filter((entry) => Boolean(entry.detail));
  const counts = {};
  for (const entry of considered) {
    const value = getEntryDecisionFilterValue(entry);
    counts[value] = (counts[value] ?? 0) + 1;
  }
  return { counts, consideredCount: considered.length };
}

export function getDecisionDistributionLabel(value) {
  return DECISION_FILTER_OPTIONS.find((option) => option.value === value)?.label ?? value;
}

// -- Savings Overview (Section C) ----------------------------------------
// Summarizes an already-built savings series (dashboardMetrics.js's
// buildSavingsSeries -- oldest-first, real per-run savings, only for runs
// with an actual selected group). Returns null when there is no data at
// all -- callers must never show a total/average/highest of zero data
// points as if it were a real "0".
export function summarizeSavings(savingsSeries) {
  if (savingsSeries.length === 0) return null;
  const total = savingsSeries.reduce((sum, point) => sum + point.savings, 0);
  const highest = Math.max(...savingsSeries.map((point) => point.savings));
  return { total, average: total / savingsSeries.length, highest, count: savingsSeries.length };
}

// -- Commodity Analysis (Section E) --------------------------------------
// Uses the FULL entry list (commodity/run count are always real,
// regardless of the enrichment cap) for runCount; savings are only
// accumulated for entries whose detail was actually loaded AND which had
// a selected group -- savingsRunCount honestly tracks how many of a
// commodity's runs actually contributed to savingsTotal, so a caller can
// say "savings available for 1 of 3 runs" rather than implying
// completeness. Sorted by run count (a plain frequency count, never a
// quality ranking) then alphabetically as a deterministic tie-break.
export function buildCommodityBreakdown(entries) {
  const byCommodity = new Map();
  for (const entry of entries) {
    const key = entry.commodity;
    if (!byCommodity.has(key)) {
      byCommodity.set(key, { commodity: key, runCount: 0, savingsTotal: 0, savingsRunCount: 0 });
    }
    const bucket = byCommodity.get(key);
    bucket.runCount += 1;

    const finalSelection = entry.detail?.result?.final_selection;
    if (finalSelection && (finalSelection.selected_results?.length ?? 0) > 0) {
      bucket.savingsTotal += finalSelection.total_savings_rs ?? 0;
      bucket.savingsRunCount += 1;
    }
  }
  return [...byCommodity.values()].sort(
    (a, b) => b.runCount - a.runCount || a.commodity.localeCompare(b.commodity)
  );
}

// -- Vendor Participation (Section F) ------------------------------------
// Only derivable from a run whose detail was actually fetched --
// input.vendor_submissions is the complete, as-submitted vendor list for
// that run (every vendor, not just the eligible/selected subset).
// `selectedCount` counts how many of those runs placed the vendor inside
// an actually-selected group (final_selection.selected_results[].vendor_ids).
// Sorted by submitted-appearance count, a plain frequency count -- never
// labeled "best" or "most reliable".
export function buildVendorParticipation(entries) {
  const byVendor = new Map();
  let consideredRunCount = 0;

  for (const entry of entries) {
    const submissions = entry.detail?.input?.vendor_submissions;
    if (!submissions) continue;
    consideredRunCount += 1;

    const selectedVendorIds = new Set(
      (entry.detail.result?.final_selection?.selected_results ?? []).flatMap((result) => result.vendor_ids ?? [])
    );

    for (const submission of submissions) {
      const vendorId = submission.vendor_id;
      if (!vendorId) continue;
      if (!byVendor.has(vendorId)) byVendor.set(vendorId, { vendorId, submittedCount: 0, selectedCount: 0 });
      const bucket = byVendor.get(vendorId);
      bucket.submittedCount += 1;
      if (selectedVendorIds.has(vendorId)) bucket.selectedCount += 1;
    }
  }

  const vendors = [...byVendor.values()].sort(
    (a, b) => b.submittedCount - a.submittedCount || a.vendorId.localeCompare(b.vendorId)
  );
  return { vendors, consideredRunCount };
}

// -- Group Size / Collaboration Pattern (Section G) ----------------------
// Counts actual selected-group sizes (vendor_ids.length) across every
// enriched run's final_selection.selected_results -- purely descriptive,
// carries no "larger is better" implication anywhere in this module.
export function buildGroupSizeDistribution(entries) {
  const sizeCounts = {};
  let totalSelectedGroups = 0;
  let consideredRunCount = 0;

  for (const entry of entries) {
    if (!entry.detail) continue;
    consideredRunCount += 1;
    const selectedResults = entry.detail.result?.final_selection?.selected_results ?? [];
    for (const group of selectedResults) {
      const size = group.vendor_ids?.length;
      if (!size) continue;
      sizeCounts[size] = (sizeCounts[size] ?? 0) + 1;
      totalSelectedGroups += 1;
    }
  }

  return { sizeCounts, totalSelectedGroups, consideredRunCount };
}

// -- Evidence-Based Observations (Section H) ------------------------------
// Every sentence here is a direct restatement of one of the counts above,
// never an inference beyond it. A "most frequently observed X" statement
// is only produced when at least 2 analyzed runs contributed to that
// count (MIN_RUNS_FOR_DISTRIBUTION_VISUAL) -- with only one data point,
// calling it "most frequent" would be trivially true but misleadingly
// authoritative-sounding, so it is simply omitted.
export function buildEvidenceObservations({
  decisionDistribution,
  savingsSummary,
  totalRunsWithSavingsPossible,
  commodityBreakdown,
  vendorParticipation,
  groupSizeDistribution,
}) {
  const observations = [];

  if (decisionDistribution.consideredCount >= MIN_RUNS_FOR_DISTRIBUTION_VISUAL) {
    for (const [value, count] of Object.entries(decisionDistribution.counts)) {
      if (count > 0) {
        observations.push(
          `${getDecisionDistributionLabel(value)} occurred in ${count} of ${decisionDistribution.consideredCount} analyzed run(s).`
        );
      }
    }
  }

  if (savingsSummary) {
    observations.push(
      `Expected savings were available for ${savingsSummary.count} of ${totalRunsWithSavingsPossible} analyzed run(s).`
    );
  }

  // A "most frequent/common X" statement claims X is UNIQUELY ahead of
  // every other value -- if two or more values are tied for the highest
  // count, no single one of them is genuinely "the most frequent", and
  // asserting one anyway (even the data's own first- or lowest-sorting
  // value) would be a claim the numbers do not actually support. Each
  // superlative observation below is therefore only produced when the
  // top count strictly exceeds the second-highest one.
  if (commodityBreakdown.length >= 1 && commodityBreakdown[0].runCount >= MIN_RUNS_FOR_DISTRIBUTION_VISUAL) {
    const topRunCount = commodityBreakdown[0].runCount;
    const isUniqueTop = commodityBreakdown.length === 1 || commodityBreakdown[1].runCount < topRunCount;
    if (isUniqueTop) {
      observations.push(
        `The most frequently analyzed commodity was ${commodityBreakdown[0].commodity} (${topRunCount} run(s)).`
      );
    }
  }

  if (
    vendorParticipation.vendors.length >= 1 &&
    vendorParticipation.consideredRunCount >= MIN_RUNS_FOR_DISTRIBUTION_VISUAL
  ) {
    const [top, second] = vendorParticipation.vendors;
    const isUniqueTop = !second || second.submittedCount < top.submittedCount;
    if (isUniqueTop) {
      observations.push(
        `The most frequently observed vendor across analyzed run details was ${top.vendorId} (${top.submittedCount} appearance(s)).`
      );
    }
  }

  if (groupSizeDistribution.totalSelectedGroups >= MIN_RUNS_FOR_DISTRIBUTION_VISUAL) {
    const sortedSizes = Object.entries(groupSizeDistribution.sizeCounts).sort((a, b) => b[1] - a[1]);
    const [topSize, topCount] = sortedSizes[0];
    const isUniqueTop = sortedSizes.length === 1 || sortedSizes[1][1] < topCount;
    if (isUniqueTop) {
      observations.push(
        `The most common selected group size was ${topSize} vendors (${topCount} of ${groupSizeDistribution.totalSelectedGroups} selected group(s)).`
      );
    }
  }

  return observations;
}
