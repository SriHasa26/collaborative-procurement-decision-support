// Phase 7E -- Section G: a STATIC explanation of the pipeline's stages.
// This is deliberately generic and non-claiming -- it describes what the
// system evaluates in general, not that every stage "succeeded" for this
// specific run (that per-run detail is already shown in the sections
// above, straight from the backend response). No AI framing anywhere.
//
// UI-5 -- upgraded to a premium numbered-timeline visual (connecting line,
// stage titles). The stage TEXT itself is unchanged from Phase 7E -- this
// is explicitly "decision methodology" (a fixed explanation of what the
// system does in general), never "observed run data" (this run's own
// actual timings/counts, which are never shown here since the backend
// does not return per-stage timings and none is invented).

const PIPELINE_STAGES = [
  { title: "Validate", description: "Vendor submissions were validated for structural correctness." },
  { title: "Demand", description: "Demand evidence was evaluated (a directly provided quantity, diary history, or peer data)." },
  { title: "Compatibility", description: "Vendors with sufficient evidence were checked for geographic compatibility with one another." },
  { title: "Candidates", description: "Candidate groups were generated from geographically compatible vendors." },
  { title: "Economics", description: "Each candidate group was evaluated against procurement constraints (cost, savings, minimum order quantity, and freshness)." },
  { title: "Expansion", description: "Groups that could not yet satisfy those constraints were checked for a feasible expansion within the same compatibility pool." },
  { title: "Overlap resolution", description: "Overlapping feasible groups were resolved so no vendor belongs to more than one selected group." },
  { title: "Decision", description: "The final groups were selected by maximizing total savings, using vendor coverage only as a tie-break." },
];

function DecisionExplanation() {
  return (
    <section className="page-section">
      <h2 className="section-title">How This Decision Was Reached</h2>
      <p className="text-body">
        This is a rule-based decision-support system, not an AI model — every stage below is a
        deterministic, documented rule applied to the data you provided. This is the decision
        methodology (what the system always does), not a log of this specific run.
      </p>
      <ol className="decision-pipeline">
        {PIPELINE_STAGES.map((stage, index) => (
          <li key={stage.title} className="decision-pipeline-stage">
            <span className="decision-pipeline-index" aria-hidden="true">
              {String(index + 1).padStart(2, "0")}
            </span>
            <div className="decision-pipeline-content">
              <span className="card-title">{stage.title}</span>
              <span className="text-small text-muted">{stage.description}</span>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

export default DecisionExplanation;
