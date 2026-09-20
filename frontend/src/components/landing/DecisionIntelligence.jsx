// UI-2 -- reuses the EXISTING DecisionStateBadge/decisionStateMeta
// (unchanged, Phase 7B) rather than inventing a second decision-badge
// style. Explicitly labeled "Example Decision" throughout -- this card is
// never connected to a real analysis run or fake runtime data (no
// specific currency figure is shown, only a qualitative "Positive
// savings identified", since a fabricated-looking precise number could
// be mistaken for a real statistic).
//
// Landing polish -- transforms the card from a static infographic into a
// "decision reasoning engine" visual: a one-time, scroll-triggered
// pipeline reveal (DecisionPipeline.jsx) culminating in the SAME example
// decision this card has always shown, followed by the supporting
// numbers, with the four reasoning bullets now interactive
// (DecisionReasoningVisual.jsx). All still 100% static/illustrative --
// no API call, no real analysis run, no new data source. The section
// heading itself now fades in once scrolled into view (it previously had
// no entrance treatment at all), matching the pipeline's own reveal
// moment.

import Button from "../common/Button";
import Card from "../common/Card";
import DecisionPipeline, { DECISION_DELAY } from "./DecisionPipeline";
import DecisionReasoningVisual from "./DecisionReasoningVisual";
import { useInViewOnce } from "./useInViewOnce";

// The three supporting-metric reveals stagger in right after
// DecisionPipeline's own decision reveal settles -- DECISION_DELAY is
// that pipeline's real, exported total delay, the single source of truth
// for "when the decision itself has finished appearing" (never
// duplicated or guessed a second time here).
const METRIC_DELAYS = [DECISION_DELAY + 120, DECISION_DELAY + 180, DECISION_DELAY + 240];

function DecisionIntelligence() {
  const [sectionRef, isInView] = useInViewOnce();

  return (
    <section id="decision-intelligence" className="landing-section" ref={sectionRef}>
      <div className="landing-section-inner">
        <div className={`landing-section-header${isInView ? " animate-in" : ""}`}>
          <p className="eyebrow">Decision Intelligence</p>
          <h2 className="section-title">Don't just find a group. Understand why it works.</h2>
          <p className="text-body">
            Every recommendation traces back to the specific evidence and rules that produced it —
            never a black-box score.
          </p>
        </div>

        <Card variant="elevated" className={`decision-preview-card${isInView ? " is-in-view" : ""}`}>
          <span className="text-label">Example Decision</span>

          <div className="landing-analysis-surface">
            <DecisionPipeline isInView={isInView} />
          </div>

          <div className="decision-preview-metrics">
            <div style={{ animationDelay: `${METRIC_DELAYS[0]}ms` }}>
              <span className="text-metric">4</span>
              <p className="text-small text-muted">Vendors evaluated</p>
            </div>
            <div style={{ animationDelay: `${METRIC_DELAYS[1]}ms` }}>
              <span className="text-metric">1</span>
              <p className="text-small text-muted">Selected group</p>
            </div>
            <div style={{ animationDelay: `${METRIC_DELAYS[2]}ms` }}>
              <span className="text-metric text-metric-positive">+</span>
              <p className="text-small text-muted">Positive savings identified</p>
            </div>
          </div>

          <DecisionReasoningVisual />

          <Button to="/analyze" variant="outline" className="decision-preview-cta">
            Run Your Own Analysis <span className="decision-preview-cta-arrow" aria-hidden="true">→</span>
          </Button>
        </Card>
      </div>
    </section>
  );
}

export default DecisionIntelligence;
