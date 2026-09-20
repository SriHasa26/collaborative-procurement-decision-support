// UI-2 -- a visual preview of what the real Results Dashboard looks like,
// reusing the EXISTING MetricCard component (results/MetricCard.jsx,
// unchanged) rather than duplicating its markup/styling. Explicitly
// labeled "Demo Scenario" -- these are illustrative, round numbers (the
// same style of example the brief itself offers), never a specific
// currency figure lifted from real test output, and never presented as a
// live platform statistic. Does not call the API, does not read any real
// run -- purely a static visual composition.
//
// Landing polish -- Part 2: the three metric cards, the network diagram and
// the decision panel all describe the SAME real demo shape this component
// has always claimed (4 vendors -> 1 compatible pool -> 11 candidate
// groups -> Buy Together). Hovering, focusing or clicking a metric card
// highlights the matching zone of ProductPreviewNetwork -- one shared
// "activeZone" state, reusing the exact hover/focus/click "preview vs.
// persist" pattern already established by SelectedGroupNetwork.jsx (UI-8)
// and DecisionReasoningVisual.jsx (this task's Part 1). No specific
// currency figure is introduced anywhere in this rewrite.

import { useState } from "react";
import Card from "../common/Card";
import DecisionStateBadge from "../common/DecisionStateBadge";
import MetricCard from "../results/MetricCard";
import ProductPreviewNetwork, { NETWORK_SETTLE_DELAY } from "./ProductPreviewNetwork";
import { useInViewOnce } from "./useInViewOnce";

const ZONES = [
  { key: "vendors", label: "Vendors", value: "4" },
  { key: "pool", label: "Compatible pool", value: "1" },
  { key: "candidates", label: "Candidate groups", value: "11" },
];

function ProductPreview() {
  const [sectionRef, isInView] = useInViewOnce();
  const [hoveredZone, setHoveredZone] = useState(null);
  const [pinnedZone, setPinnedZone] = useState(null);
  const activeZone = hoveredZone ?? pinnedZone;

  return (
    <section className="landing-section landing-section-alt" ref={sectionRef}>
      <div className="landing-section-inner">
        <div className={`landing-section-header${isInView ? " animate-in" : ""}`}>
          <p className="eyebrow">Product Preview</p>
          <h2 className="section-title">See what an analysis produces</h2>
        </div>

        <Card variant="elevated" className={`product-preview-card${isInView ? " is-in-view" : ""}`}>
          <span className="text-label">Demo Scenario</span>
          <p className="card-title">Procurement Analysis</p>

          <div className="product-preview-metrics">
            {ZONES.map((zone, index) => (
              <div
                key={zone.key}
                className={`product-preview-metric-zone${activeZone === zone.key ? " is-active" : ""}`}
                style={{ animationDelay: `${index * 80}ms` }}
                tabIndex={0}
                role="button"
                aria-pressed={pinnedZone === zone.key}
                aria-label={`Highlight ${zone.label} in the diagram below`}
                onMouseEnter={() => setHoveredZone(zone.key)}
                onMouseLeave={() => setHoveredZone((prev) => (prev === zone.key ? null : prev))}
                onFocus={() => setHoveredZone(zone.key)}
                onBlur={() => setHoveredZone((prev) => (prev === zone.key ? null : prev))}
                onClick={() => setPinnedZone((prev) => (prev === zone.key ? null : zone.key))}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setPinnedZone((prev) => (prev === zone.key ? null : zone.key));
                  }
                }}
              >
                <MetricCard label={zone.label} value={zone.value} />
              </div>
            ))}
          </div>

          <div className="landing-analysis-surface">
            <ProductPreviewNetwork isInView={isInView} activeZone={activeZone} />
          </div>

          <div
            className={`product-preview-outcome${isInView ? " is-in-view" : ""}`}
            style={{ animationDelay: `${NETWORK_SETTLE_DELAY}ms` }}
          >
            <span className="text-label">Decision reached</span>
            <DecisionStateBadge state="BUY_TOGETHER" />
            <span className="text-small text-muted">Expected savings quantified for the selected group</span>
          </div>
        </Card>
      </div>
    </section>
  );
}

export default ProductPreview;
