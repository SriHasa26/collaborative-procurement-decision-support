// Landing polish -- the Decision Intelligence card's "reasoning engine"
// visual: a small node-and-connector pipeline plus a synced status
// caption, both staggered by the SAME real pipeline-stage order this
// project already uses honestly elsewhere (results/DecisionExplanation.jsx's
// own Validate -> Demand -> Compatibility -> Candidates -> Economics ->
// Decision stages, condensed to fit a compact card) -- never an invented
// stage, never a fabricated runtime duration. This is explanatory
// methodology, exactly like DecisionExplanation.jsx's own "decision
// methodology, not observed run data" framing -- it never claims to be
// the actual backend's execution telemetry.
//
// Plays ONCE when the card scrolls into view (via the shared
// useInViewOnce hook, not on mount -- this card sits below the fold);
// respects the existing site-wide prefers-reduced-motion override with
// zero extra code (every animation below is a plain CSS keyframe, gated
// by an `.is-in-view` class this component toggles once).
//
// Reuses the EXACT node-in/draw-edge/pulse-ring keyframes
// components/landing/HeroNetwork.jsx (UI-2) already established, rather
// than a second entrance-animation implementation.

import DecisionStateBadge from "../common/DecisionStateBadge";

const STAGES = [
  { key: "vendors", label: "Vendors", caption: "Evaluating vendors" },
  { key: "eligibility", label: "Eligibility", caption: "Checking demand evidence & eligibility" },
  { key: "compatibility", label: "Compatibility", caption: "Checking geographic compatibility" },
  { key: "candidates", label: "Candidate Groups", caption: "Forming candidate groups" },
  { key: "economics", label: "Cost Evaluation", caption: "Evaluating cost & savings" },
];

const STAGE_GAP = 320; // ms between each stage node/caption activating
// Exported so DecisionIntelligence.jsx (the parent composing both this
// pipeline AND the separate supporting-metrics reveal) can time the
// metrics' own reveal to start right after the decision settles --
// a single source of truth for that delay, never duplicated as a second
// hardcoded number.
export const DECISION_DELAY = STAGES.length * STAGE_GAP + 260;

function nodeX(index, total, width = 400) {
  const margin = 36;
  return margin + (index * (width - margin * 2)) / (total - 1);
}

function DecisionPipeline({ isInView }) {
  const y = 30;
  const positions = STAGES.map((_, index) => nodeX(index, STAGES.length));

  return (
    <div className={`decision-pipeline${isInView ? " is-in-view" : ""}`}>
      <svg
        className="decision-pipeline-svg"
        viewBox="0 0 400 60"
        role="img"
        aria-label={`Decision pipeline: ${STAGES.map((s) => s.label).join(" then ")}, resulting in Buy Together.`}
      >
        {positions.slice(1).map((x, i) => (
          <line
            key={`edge-${STAGES[i + 1].key}`}
            className="decision-pipeline-edge"
            x1={positions[i]}
            y1={y}
            x2={x}
            y2={y}
            style={{ animationDelay: `${i * STAGE_GAP}ms` }}
          />
        ))}
        {positions.map((x, index) => (
          <circle
            key={STAGES[index].key}
            className="decision-pipeline-node"
            cx={x}
            cy={y}
            r={6}
            style={{ animationDelay: `${index * STAGE_GAP}ms` }}
          />
        ))}
      </svg>

      <p className="decision-pipeline-caption text-small text-muted" aria-hidden="true">
        {STAGES.map((stage, index) => (
          <span
            key={stage.key}
            className="decision-pipeline-caption-item"
            style={{ animationDelay: `${index * STAGE_GAP}ms` }}
          >
            {stage.caption}
          </span>
        ))}
      </p>

      <div className="decision-pipeline-outcome" style={{ animationDelay: `${DECISION_DELAY}ms` }}>
        <span className="decision-pipeline-outcome-pulse" aria-hidden="true" />
        <DecisionStateBadge state="BUY_TOGETHER" />
      </div>
    </div>
  );
}

export default DecisionPipeline;
