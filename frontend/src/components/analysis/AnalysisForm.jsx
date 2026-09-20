// UI-4 -- the guided, five-step analysis workflow. Rewritten from Phase
// 7C/7D's single continuous form, but every piece of DATA/behavior it
// depends on is unchanged: useProcurementForm.js (form state + prepare()
// + the new, additive validateCurrentState()), buildAnalysisPayload.js,
// validateAnalysisForm.js, and the exact submission logic (analyzeProcurement
// call, response check, navigate("/results", {state: {result}})) below are
// byte-for-byte the same as before this phase -- only HOW the fields are
// presented (five steps instead of one long page) changed. The backend
// payload this produces is therefore identical for identical input; see
// reports/ui4_premium_analysis_workflow.md Section 15 for the explicit
// before/after comparison.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeProcurement } from "../../api/procurementApi";
import ErrorState from "../common/ErrorState";
import LoadingState from "../common/LoadingState";
import Button from "../common/Button";
import CommodityStep from "./steps/CommodityStep";
import ConfigStep from "./steps/ConfigStep";
import ContextStep from "./steps/ContextStep";
import ReviewStep from "./steps/ReviewStep";
import VendorNetworkStep from "./steps/VendorNetworkStep";
import FormSection from "./FormSection";
import StepProgress from "./StepProgress";
import { useProcurementForm } from "./useProcurementForm";
import { findFirstInvalidStepIndex, hasStepErrors, STEPS } from "./wizardSteps";

// Identical to Phase 7D's own describeSubmissionError -- unchanged wording,
// unchanged logic, only relocated alongside its one caller.
function describeSubmissionError(error) {
  const message = error instanceof Error ? error.message : String(error);
  if (message.startsWith("Unable to reach the backend")) {
    return "Unable to connect to the analysis service. Please check that the backend is running and try again.";
  }
  return "The analysis request could not be completed. Please try again.";
}

function AnalysisForm() {
  const {
    formState,
    errors,
    updateField,
    updateVendor,
    addVendor,
    removeVendor,
    updateTransportTier,
    addTransportTier,
    removeTransportTier,
    prepare,
    validateCurrentState,
  } = useProcurementForm();

  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState(new Set());
  const [submission, setSubmission] = useState({ status: "idle", message: "" });
  const navigate = useNavigate();

  const handleTextField = (field) => (event) => updateField(field, event.target.value);
  const handleCheckboxField = (field) => (event) => updateField(field, event.target.checked);

  function goToStep(index) {
    setCurrentStepIndex(Math.max(0, Math.min(index, STEPS.length - 1)));
  }

  function handleContinue() {
    const result = validateCurrentState();
    const currentKey = STEPS[currentStepIndex].key;
    if (hasStepErrors(result.errors, currentKey)) {
      return; // stay on this step -- inline errors are already visible from the freshly-set `errors`
    }
    setCompletedSteps((prev) => new Set(prev).add(currentKey));
    goToStep(currentStepIndex + 1);
  }

  function handleBack() {
    goToStep(currentStepIndex - 1);
  }

  async function handleAnalyze() {
    // Duplicate-submission guard, unchanged from Phase 7D.
    if (submission.status === "submitting") return;

    const result = prepare(); // the SAME, unmodified whole-form validate + build-payload
    if (!result.isValid) {
      // Jump back to the first step that actually has an error, rather
      // than silently failing on Review -- a real UX improvement this
      // phase's own guided-workflow goal calls for, made possible because
      // hasStepErrors() already knows how to map errors back to a step.
      const firstInvalid = findFirstInvalidStepIndex(result.errors);
      if (firstInvalid >= 0) goToStep(firstInvalid);
      setSubmission({ status: "idle", message: "" });
      return;
    }

    setSubmission({ status: "submitting", message: "" });
    try {
      const response = await analyzeProcurement(result.payload);

      // Identical minimal response-shape check to Phase 7D's own.
      if (!response || typeof response.run_status !== "string") {
        throw new Error("The analysis service returned an unexpected response.");
      }

      navigate("/results", { state: { result: response } });
    } catch (error) {
      setSubmission({ status: "error", message: describeSubmissionError(error) });
    }
  }

  function handleFormSubmit(event) {
    event.preventDefault();
    if (STEPS[currentStepIndex].key === "review") {
      handleAnalyze();
    } else {
      handleContinue();
    }
  }

  const currentStep = STEPS[currentStepIndex];
  const isSubmitting = submission.status === "submitting";

  return (
    <div className="analysis-wizard">
      <StepProgress currentIndex={currentStepIndex} completedKeys={completedSteps} onStepClick={goToStep} />

      <form className="analysis-form animate-in" onSubmit={handleFormSubmit} noValidate>
        {currentStep.key === "review" ? (
          // Review renders its own complete visual container (an elevated
          // Card) -- nesting that inside FormSection's own fieldset/card
          // would box it twice, so Review deliberately bypasses
          // FormSection rather than reusing it here.
          // UI-8 -- `key={currentStep.key}` on both branches forces a
          // real remount on every step change (React would otherwise
          // just patch the existing <FormSection>/<ReviewStep> in place,
          // which would never replay .animate-in's entrance) -- a
          // deliberate, fast crossfade that reinforces "you moved to a
          // new step" without any JS animation state.
          <ReviewStep
            key={currentStep.key}
            formState={formState}
            onEditStep={goToStep}
            isSubmitting={isSubmitting}
            submissionError={submission.status === "error" ? submission.message : ""}
          />
        ) : (
          <FormSection key={currentStep.key} title={currentStep.title} className="animate-in">
            {currentStep.key === "context" && (
              <ContextStep
                formState={formState}
                errors={errors}
                onTextField={handleTextField}
                onCheckboxField={handleCheckboxField}
              />
            )}

            {currentStep.key === "commodity" && (
              <CommodityStep formState={formState} errors={errors} onTextField={handleTextField} />
            )}

            {currentStep.key === "config" && (
              <ConfigStep
                formState={formState}
                errors={errors}
                onTextField={handleTextField}
                onUpdateTier={updateTransportTier}
                onAddTier={addTransportTier}
                onRemoveTier={removeTransportTier}
              />
            )}

            {currentStep.key === "vendors" && (
              <VendorNetworkStep
                formState={formState}
                errors={errors}
                onUpdateVendor={updateVendor}
                onAddVendor={addVendor}
                onRemoveVendor={removeVendor}
                onValidate={validateCurrentState}
              />
            )}
          </FormSection>
        )}

        {currentStep.key !== "review" && (
          <div className="wizard-nav-row">
            <Button type="button" variant="secondary" onClick={handleBack} disabled={currentStepIndex === 0}>
              ← Back
            </Button>
            <Button type="submit" variant="primary">
              Continue →
            </Button>
          </div>
        )}

        {isSubmitting && <LoadingState label="Submitting your procurement analysis…" />}
        {currentStep.key !== "review" && submission.status === "error" && (
          <ErrorState title="Analysis request failed" description={submission.message} />
        )}
      </form>
    </div>
  );
}

export default AnalysisForm;
