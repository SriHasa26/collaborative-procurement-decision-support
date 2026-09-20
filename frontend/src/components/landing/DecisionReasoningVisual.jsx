// Landing polish -- Part B: turns the four static reasoning bullet points
// into compact, interactive "evidence chips". Each explanation describes
// this project's OWN real, existing rules (Phase 5D/6A-6D's documented
// evaluation logic, the same one results/DecisionExplanation.jsx already
// explains on the real Results page) -- never an invented metric or a
// second algorithm.
//
// Reuses the exact hover/focus/click "preview vs. persist" interaction
// pattern UI-8's SelectedGroupNetwork.jsx already established
// (hoveredIndex previews, click pins, activeIndex = hovered ?? pinned) --
// one interaction language across the whole product, not a second one
// invented for the landing page.

import { useState } from "react";

const FACTORS = [
  {
    label: "Geographic compatibility",
    detail: "All selected vendors satisfy the configured distance constraint.",
  },
  {
    label: "Demand evidence",
    detail: "Demand is evaluated against the configured procurement horizon.",
  },
  {
    label: "Procurement feasibility",
    detail: "Minimum order quantity and transport capacity constraints are satisfied.",
  },
  {
    label: "Cost optimization",
    detail: "The selected group produces positive expected savings.",
  },
];

function DecisionReasoningVisual() {
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [pinnedIndex, setPinnedIndex] = useState(null);
  const activeIndex = hoveredIndex ?? pinnedIndex;

  return (
    <ul className="decision-reasoning-list">
      {FACTORS.map((factor, index) => {
        const isActive = activeIndex === index;
        return (
          <li key={factor.label} className={`decision-reasoning-row${isActive ? " is-active" : ""}`}>
            <button
              type="button"
              className="decision-reasoning-trigger"
              aria-expanded={isActive}
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex((prev) => (prev === index ? null : prev))}
              onFocus={() => setHoveredIndex(index)}
              onBlur={() => setHoveredIndex((prev) => (prev === index ? null : prev))}
              onClick={() => setPinnedIndex((prev) => (prev === index ? null : index))}
            >
              <span className="decision-reasoning-check" aria-hidden="true">
                ✓
              </span>
              <span className="decision-reasoning-label">{factor.label}</span>
            </button>
            <div className="decision-reasoning-detail-wrapper">
              <p className="decision-reasoning-detail text-small text-muted">{factor.detail}</p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export default DecisionReasoningVisual;
