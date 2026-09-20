// UI-3 -- deterministic, pure aggregation over already-fetched, already-
// persisted run details (the exact shape GET /procurement/runs/{run_id}
// returns: { run_id, created_at, commodity, run_status, input, result }).
// Same boundary as results/resultHelpers.js: every function here only
// reads/sums/counts fields the backend already computed -- it never makes
// a procurement decision, calculates savings, or invents a value for a
// field that is absent. `storedRuns` is assumed newest-first, matching
// GET /procurement/runs' own ordering (backend/persistence/*_repository.py:
// "ORDER BY created_at DESC, run_id DESC").

export function buildDashboardMetrics(storedRuns) {
  const totalAnalyses = storedRuns.length;

  let totalSavings = 0;
  let runsWithSavings = 0;
  let totalVendorsEvaluated = 0;
  let totalSelectedGroups = 0;
  let totalVendorCoverage = 0;
  const decisionCounts = {};

  for (const stored of storedRuns) {
    const result = stored.result;
    if (!result) continue;

    totalVendorsEvaluated += result.total_vendors_submitted ?? 0;
    totalSelectedGroups += result.selected_group_count ?? 0;

    const finalSelection = result.final_selection;
    if (finalSelection && (finalSelection.selected_results?.length ?? 0) > 0) {
      totalSavings += finalSelection.total_savings_rs ?? 0;
      totalVendorCoverage += finalSelection.total_vendor_coverage ?? 0;
      runsWithSavings += 1;
    }

    // Decision distribution: every candidate group this run actually
    // evaluated has its own final_decision_state (a group-level concept,
    // distinct from the run-level run_status -- see
    // backend/models/run_contracts.py's own docstring on this
    // distinction). Counted per group, across every fetched run, never
    // per run.
    const evaluatedGroups = finalSelection?.all_evaluated_results ?? [];
    for (const evaluated of evaluatedGroups) {
      const state = evaluated.final_decision_state;
      if (state) decisionCounts[state] = (decisionCounts[state] ?? 0) + 1;
    }
  }

  return {
    totalAnalyses,
    totalSavings,
    hasSavingsData: runsWithSavings > 0,
    totalVendorsEvaluated,
    totalSelectedGroups,
    averageVendorsPerGroup: totalSelectedGroups > 0 ? totalVendorCoverage / totalSelectedGroups : null,
    decisionCounts,
  };
}

// The most recent run (storedRuns is newest-first) that actually has a
// selected group -- a run can be COMPLETED with zero selections
// (COMPLETED_NO_SELECTION), which is not "no decision", but has nothing
// to surface as a "latest decision" either. Returns null if none exists
// yet (the caller shows an empty state, never a fabricated one).
export function getLatestSelectedRun(storedRuns) {
  for (const stored of storedRuns) {
    const finalSelection = stored.result?.final_selection;
    if (finalSelection && (finalSelection.selected_results?.length ?? 0) > 0) {
      return stored;
    }
  }
  return null;
}

// Real per-run savings series, oldest-first (reversed from storedRuns'
// newest-first order) for a left-to-right chronological chart -- only
// includes runs that actually produced a selected group; a run with no
// selection contributes no savings data point (not a fabricated zero).
export function buildSavingsSeries(storedRuns) {
  return [...storedRuns]
    .reverse()
    .map((stored) => {
      const finalSelection = stored.result?.final_selection;
      if (!finalSelection || (finalSelection.selected_results?.length ?? 0) === 0) return null;
      return {
        runId: stored.run_id,
        commodity: stored.commodity,
        createdAt: stored.created_at,
        savings: finalSelection.total_savings_rs ?? 0,
      };
    })
    .filter(Boolean);
}
