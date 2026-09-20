// Phase 7B -- reusable horizontal (desktop) / vertical (mobile) step-flow
// presentation. Used by HomePage ("how the system works") and
// AnalysisPage ("analysis workflow") with different step labels -- purely
// presentational, takes no live data.

function WorkflowSteps({ steps }) {
  return (
    <div className="workflow-steps">
      {steps.map((step, index) => (
        <div className="workflow-step" key={step.label}>
          <span className="workflow-step-index" aria-hidden="true">
            {index + 1}
          </span>
          <span className="card-title">{step.label}</span>
          {step.description && <span className="text-small">{step.description}</span>}
        </div>
      ))}
    </div>
  );
}

export default WorkflowSteps;
