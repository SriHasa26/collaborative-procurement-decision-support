// UI-4 -- premium step indicator. Desktop shows all five stages with
// connecting lines (CSS handles hiding this and showing the compact
// mobile version below ~640px -- see analysis.css); mobile always shows
// "STEP X OF N" + the current step's own title, never five cramped
// labels. Completion state (done/current/upcoming) is real: `completed`
// is the set of step keys the caller has determined have no validation
// errors AND have been visited (see AnalysisForm.jsx) -- never assumed.
// A future (not-yet-visited) step's indicator is not a link -- clicking
// ahead is deliberately not supported (this phase's own "do not force
// users to complete future steps" is about not REQUIRING it, not about
// letting them skip ahead to unvalidated ground).

import { STEPS } from "./wizardSteps";

function StepProgress({ currentIndex, completedKeys, onStepClick }) {
  const currentStep = STEPS[currentIndex];

  return (
    <nav className="wizard-progress" aria-label="Analysis workflow progress">
      <ol className="wizard-progress-track">
        {STEPS.map((step, index) => {
          const isCompleted = completedKeys.has(step.key);
          const isCurrent = index === currentIndex;
          const isClickable = isCompleted || isCurrent || index < currentIndex;
          const status = isCompleted ? "completed" : isCurrent ? "current" : "upcoming";

          return (
            <li key={step.key} className={`wizard-progress-step is-${status}`}>
              <button
                type="button"
                className="wizard-progress-step-button"
                onClick={() => isClickable && onStepClick(index)}
                disabled={!isClickable}
                aria-current={isCurrent ? "step" : undefined}
              >
                <span className="wizard-progress-step-index" aria-hidden="true">
                  {isCompleted ? "✓" : String(index + 1).padStart(2, "0")}
                </span>
                <span className="wizard-progress-step-label">{step.label}</span>
              </button>
            </li>
          );
        })}
      </ol>

      <p className="wizard-progress-compact text-small text-muted">
        Step {currentIndex + 1} of {STEPS.length} — <span className="text-body">{currentStep.title}</span>
      </p>
    </nav>
  );
}

export default StepProgress;
