// UI-2 -- a richer, visually-connected process flow than
// components/common/WorkflowSteps.jsx (left completely unchanged -- it is
// still used, as-is, by AnalysisPage's own "Analysis workflow" section;
// duplicating its visual treatment here for the landing page's different
// needs, rather than changing the shared component's look for both
// contexts). Uses "decision engine"/"deterministic rules" language, never
// "AI", matching this project's own established, honest positioning.

const STAGES = [
  { index: "01", title: "Submit", description: "Provide commodity, procurement constraints, and vendor information." },
  { index: "02", title: "Validate", description: "Check vendor data and demand evidence for completeness." },
  { index: "03", title: "Connect", description: "Identify geographically compatible vendors." },
  { index: "04", title: "Optimize", description: "Evaluate candidate groups against cost, savings, and constraints." },
  { index: "05", title: "Decide", description: "Produce an explainable, deterministic recommendation." },
];

function HowItWorks() {
  return (
    <section id="how-it-works" className="landing-section landing-section-alt">
      <div className="landing-section-inner">
        <div className="landing-section-header">
          <p className="eyebrow">How It Works</p>
          <h2 className="section-title">From submission to a decision, in five deterministic stages</h2>
        </div>

        <div className="how-it-works-track">
          {STAGES.map((stage) => (
            <div key={stage.index} className="how-it-works-stage">
              <span className="how-it-works-index" aria-hidden="true">
                {stage.index}
              </span>
              <p className="card-title">{stage.title}</p>
              <p className="text-small">{stage.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default HowItWorks;
