// Phase 7B -- page header + workflow overview (unchanged in substance).
// Phase 7C -- the placeholder "information this analysis will collect"
// cards are replaced by the real AnalysisForm.
// Phase 7D -- AnalysisForm now actually submits to the backend; this page
// itself is unchanged except for the introductory copy below.
// UI-4 -- AnalysisForm is now a guided, five-step workflow with its own
// step progress indicator (context/commodity/config/vendors/review) --
// distinct from, and complementary to, the DECISION ENGINE'S pipeline
// stages below (validation/eligibility/compatibility/group
// evaluation/final selection), which describe what happens on the
// backend AFTER submission, not what the user fills in. The redundant
// "Analysis request" intro section (Phase 7D) was removed -- the wizard
// card itself now provides that framing per-step, more usefully.

import AnalysisForm from "../components/analysis/AnalysisForm";
import PageHeader from "../components/common/PageHeader";
import WorkflowSteps from "../components/common/WorkflowSteps";

const WORKFLOW_STEPS = [
  { label: "Validation" },
  { label: "Eligibility" },
  { label: "Compatibility" },
  { label: "Group Evaluation" },
  { label: "Final Selection" },
];

function AnalysisPage() {
  return (
    <>
      <PageHeader
        title="Analyze Procurement"
        description="Provide vendor and procurement information to evaluate whether collaborative procurement is feasible."
      />

      <section className="page-section">
        <h2 className="section-title">How your analysis will be processed</h2>
        <WorkflowSteps steps={WORKFLOW_STEPS} />
      </section>

      <AnalysisForm />
    </>
  );
}

export default AnalysisPage;
