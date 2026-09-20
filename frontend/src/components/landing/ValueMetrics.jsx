// UI-2 -- capability-focused value cards, deliberately NOT fabricated
// usage statistics (no "10,000+ vendors" / "₹50M saved" / "99.9%
// accuracy" -- none of that exists for this project). This is the "safer
// alternative" this phase's own brief explicitly names.

import Card from "../common/Card";

const CAPABILITIES = [
  {
    icon: "◎",
    title: "Geographic Compatibility",
    description: "Evaluate vendor proximity against a configurable maximum collaboration distance.",
  },
  {
    icon: "▤",
    title: "Demand Evidence",
    description: "Use explicit or diary/peer-supported demand signals, never a guessed quantity.",
  },
  {
    icon: "⚖",
    title: "Cost Optimization",
    description: "Compare every feasible collaborative group against buying individually.",
  },
  {
    icon: "◈",
    title: "Explainable Decisions",
    description: "Every recommendation shows exactly which rules and evidence produced it.",
  },
];

function ValueMetrics() {
  return (
    <section className="landing-section">
      <div className="landing-section-inner">
        <div className="value-grid">
          {CAPABILITIES.map((item) => (
            <Card key={item.title}>
              <span className="value-card-icon" aria-hidden="true">
                {item.icon}
              </span>
              <p className="card-title">{item.title}</p>
              <p className="text-small">{item.description}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

export default ValueMetrics;
