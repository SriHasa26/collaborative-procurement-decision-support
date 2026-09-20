// UI-2 -- what makes this system different, per this phase's brief.

import Card from "../common/Card";

const DIFFERENTIATORS = [
  { title: "Collaborative by Design", description: "Finds groups instead of evaluating vendors in isolation." },
  { title: "Geography-Aware", description: "Uses vendor location compatibility as part of group formation." },
  { title: "Constraint-Aware", description: "Evaluates procurement constraints before recommending action." },
  { title: "Explainable", description: "Shows the decision path rather than returning a black-box score." },
  { title: "Savings-Focused", description: "Quantifies the economic value of collaboration." },
];

function Differentiators() {
  return (
    <section className="landing-section">
      <div className="landing-section-inner">
        <div className="landing-section-header">
          <p className="eyebrow">Why It's Different</p>
          <h2 className="section-title">Built specifically for collaborative procurement</h2>
        </div>

        <div className="differentiators-grid">
          {DIFFERENTIATORS.map((item) => (
            <Card key={item.title}>
              <p className="card-title">{item.title}</p>
              <p className="text-small">{item.description}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

export default Differentiators;
