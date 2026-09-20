// Phase 7E -- display metadata for RunStatus (backend/models/run_contracts.py).
// Mirrors the existing pattern in components/common/decisionStateMeta.js:
// a fixed, exhaustive mapping from each REAL enum value to a human label
// and a Badge color variant -- no new status is invented, and an
// unrecognized value falls back to showing the raw string rather than
// guessing.
//
// Colors deliberately never use "danger" here: every RunStatus value is
// returned over HTTP 200 as a genuinely successful API response (Phase 7D
// Section 9) -- including COMPLETED_INVALID_CONTEXT, which describes a
// structural issue with the submitted batch, not a system failure.
//
// UI-5 -- added `description`, a one-sentence explanation of what the
// status itself means (grounded directly in run_contracts.py's own
// RunStatus docstring), for DecisionHero.jsx to show when no group was
// selected and there is therefore no single group-level decision to
// headline. This is static explanatory text keyed to a real, already-
// returned enum value -- exactly decisionStateMeta.js's own `description`
// pattern, applied to this second enum -- never a number or a claim about
// this specific run's data (those come from the run's own real counts,
// shown separately).

export const RUN_STATUS_META = {
  COMPLETED: {
    label: "Completed",
    variant: "success",
    description: "Every stage of the evaluation completed normally for this run.",
  },
  COMPLETED_WITH_ABSTENTIONS: {
    label: "Completed, with abstentions",
    variant: "warning",
    description: "The run completed, but one or more vendors abstained due to insufficient evidence.",
  },
  COMPLETED_NO_SELECTION: {
    label: "Completed, no group selected",
    variant: "warning",
    description: "Candidate groups were evaluated, but none met the criteria for a collaborative procurement recommendation.",
  },
  COMPLETED_NO_GROUPS: {
    label: "Completed, no candidate groups",
    variant: "neutral",
    description: "Eligible vendors were found, but no geographically compatible candidate groups could be formed among them.",
  },
  COMPLETED_INSUFFICIENT_ELIGIBLE_VENDORS: {
    label: "Completed, insufficient eligible vendors",
    variant: "neutral",
    description: "Fewer than two vendors were eligible for this run, so group formation was not attempted.",
  },
  COMPLETED_INVALID_CONTEXT: {
    label: "Completed, invalid procurement context",
    variant: "warning",
    description: "The submitted procurement context did not pass structural validation.",
  },
};

export function getRunStatusMeta(runStatus) {
  return RUN_STATUS_META[runStatus] ?? { label: runStatus, variant: "neutral" };
}
