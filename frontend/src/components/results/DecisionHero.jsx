// UI-5 -- the Decision Hero: the single most important section of the
// results cockpit. Every value below is read directly from the real
// ProcurementRunResult (backend/models/run_contracts.py) -- nothing here
// computes a decision, savings figure, or vendor count of its own.
//
// TWO DISTINCT CONCEPTS, deliberately never merged (per backend/models/
// run_contracts.py's own explicit warning): a GROUP-level decision
// (DecisionState -- BUY_TOGETHER/etc., only meaningful when at least one
// group was actually selected) and a RUN-level outcome (RunStatus -- a
// property of the whole run, assigned by the pipeline regardless of
// whether any group was selected). When a group WAS selected, the hero
// headlines that group's own `final_decision_state` (read directly from
// the response -- never assumed to be "BUY_TOGETHER", even though the
// backend's own selection.py only ever selects candidates whose final
// state already is BUY_TOGETHER). When none was selected, there is no
// single group-level decision to headline, so the hero honestly falls
// back to the run's own RunStatus and its real, already-computed counts
// instead of inventing a merged "decision".

import Badge from "../common/Badge";
import DecisionStateBadge from "../common/DecisionStateBadge";
import { DECISION_STATE_META } from "../common/decisionStateMeta";
import { formatCurrency } from "./resultHelpers";
import { getRunStatusMeta } from "./runStatusMeta";

function pluralize(count, noun) {
  return `${count} ${noun}${count === 1 ? "" : "s"}`;
}

function DecisionHero({ result }) {
  const finalSelection = result.final_selection;
  const selectedResults = finalSelection?.selected_results ?? [];
  const hasSelection = selectedResults.length > 0;
  const runStatusMeta = getRunStatusMeta(result.run_status);
  const showRunStatusNote = result.run_status !== "COMPLETED";

  if (hasSelection) {
    const primaryState = selectedResults[0].final_decision_state;
    const stateMeta = DECISION_STATE_META[primaryState];
    const groupCount = selectedResults.length;
    const vendorCoverage = finalSelection.total_vendor_coverage;

    return (
      <section className="decision-hero" aria-labelledby="decision-hero-heading">
        <p className="eyebrow eyebrow-on-dark animate-in">Procurement Decision</p>
        <div className="animate-in animate-in-delay-1">
          <DecisionStateBadge state={primaryState} />
        </div>
        <h1
          id="decision-hero-heading"
          className={`decision-hero-state decision-hero-state-${stateMeta?.variant ?? "neutral"} animate-in animate-in-delay-1`}
        >
          {stateMeta?.label ?? primaryState}
        </h1>
        <p className="decision-hero-sentence animate-in animate-in-delay-2">
          {pluralize(vendorCoverage, "vendor")} can be coordinated into{" "}
          {pluralize(groupCount, "collaborative procurement group")} under the evaluated constraints.
        </p>

        <div className="decision-hero-savings animate-in animate-in-delay-3">
          <span className="text-label text-label-on-dark">Expected Savings</span>
          <p className="decision-hero-savings-value">{formatCurrency(finalSelection.total_savings_rs)}</p>
        </div>

        <div className="decision-hero-chips animate-in animate-in-delay-4">
          <span className="decision-hero-chip">{pluralize(result.total_vendors_submitted, "vendor submitted")}</span>
          <span className="decision-hero-chip">{pluralize(result.selected_group_count, "selected group")}</span>
          <span className="decision-hero-chip">{pluralize(result.candidate_group_count, "candidate group evaluated")}</span>
        </div>

        {showRunStatusNote && (
          <p className="decision-hero-note animate-in animate-in-delay-4">
            <Badge variant={runStatusMeta.variant}>{runStatusMeta.label}</Badge>{" "}
            <a href="#diagnostics" className="decision-hero-note-link">
              See diagnostics below
            </a>
          </p>
        )}
      </section>
    );
  }

  return (
    <section className="decision-hero decision-hero-no-selection" aria-labelledby="decision-hero-heading">
      <p className="eyebrow eyebrow-on-dark animate-in">Procurement Decision</p>
      <h1 id="decision-hero-heading" className="decision-hero-state decision-hero-state-compact animate-in animate-in-delay-1">
        <Badge variant={runStatusMeta.variant}>{runStatusMeta.label}</Badge>
      </h1>
      <p className="decision-hero-sentence animate-in animate-in-delay-2">{runStatusMeta.description}</p>

      <div className="decision-hero-chips animate-in animate-in-delay-3">
        <span className="decision-hero-chip">{pluralize(result.total_vendors_submitted, "vendor submitted")}</span>
        <span className="decision-hero-chip">{pluralize(result.eligible_vendor_count, "eligible vendor")}</span>
        <span className="decision-hero-chip">{pluralize(result.candidate_group_count, "candidate group evaluated")}</span>
      </div>
    </section>
  );
}

export default DecisionHero;
