// Phase 7D -- receives the backend result handed off from AnalysisForm via
// React Router navigation state. HANDOFF LIMITATION (unchanged from
// Phase 7D, still applies): navigation state does not survive a refresh
// or a direct URL visit -- the backend already durably persisted the run
// (Phase 6G) regardless, only this tab's in-memory reference is lost. No
// fetch happens on this page itself (no run_id in the URL) -- preserved
// exactly as-is per UI-5's explicit "do not break existing routing" rule;
// see reports/ui5_premium_results_dashboard.md Section 7 for why a
// LOADING state does not apply here (there is no async work to wait on).
//
// UI-5 -- redesigned into a premium "Procurement Decision Cockpit":
// Decision Hero -> Key Decision Metrics -> Selected Procurement Group ->
// Vendor Economics -> Candidate Groups Evaluated -> Diagnostics -> Vendor
// Submission Detail -> How This Decision Was Reached -> Decision Summary
// -> Actions. Every value displayed anywhere below is read directly from
// the backend's ProcurementRunResult response (see
// backend/models/run_contracts.py) -- nothing here recomputes a decision,
// savings, distance, or eligibility outcome. `runId`/`createdAt` are only
// present when this page was reached by reopening a persisted run from
// History (HistoryPage.jsx now forwards them) -- a freshly-completed
// analysis has neither, and the header simply omits them rather than
// showing a fabricated identifier.

import { useLocation } from "react-router-dom";
import Button from "../components/common/Button";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import PageHeader from "../components/common/PageHeader";
import Tooltip from "../components/common/Tooltip";
import { formatRunTimestamp } from "../components/history/historyHelpers";
import CandidateGroupsPanel from "../components/results/CandidateGroupsPanel";
import DecisionDiagnostics from "../components/results/DecisionDiagnostics";
import DecisionFlowVisual from "../components/results/DecisionFlowVisual";
import DecisionExplanation from "../components/results/DecisionExplanation";
import DecisionHero from "../components/results/DecisionHero";
import ResultActions from "../components/results/ResultActions";
import ResultMetricGrid from "../components/results/ResultMetricGrid";
import ResultSummary from "../components/results/ResultSummary";
import SelectedGroupCard from "../components/results/SelectedGroupCard";
import VendorEconomics from "../components/results/VendorEconomics";
import VendorOutcomesTable from "../components/results/VendorOutcomesTable";
import { hasUsableResult } from "../components/results/resultHelpers";

const PAGE_SUBTITLE = "A transparent summary of the collaborative procurement decision process.";

function ResultsPage() {
  const location = useLocation();
  const { result, runId, createdAt } = location.state ?? {};

  // A result object exists but is missing the one field every real
  // ProcurementRunResult always has -- treat as an unusable/malformed
  // response rather than guessing at its contents (Phase 7E Step 6).
  // Never expose the raw object/exception -- a generic, safe message only.
  if (result && !hasUsableResult(result)) {
    return (
      <>
        <PageHeader title="Analysis Results" description={PAGE_SUBTITLE} />
        <ErrorState
          title="We couldn't load this procurement run"
          description="The analysis response could not be displayed. Please try running the analysis again."
          actions={
            <Button to="/analyze" variant="primary">
              Start New Analysis
            </Button>
          }
        />
      </>
    );
  }

  if (!result) {
    return (
      <>
        <PageHeader title="Analysis Results" description={PAGE_SUBTITLE} />
        <EmptyState
          icon="□"
          title="No analysis result is currently available"
          description="Run a procurement analysis, or reopen a previous one from Run History, to view results here."
          actions={
            <Button to="/analyze" variant="primary">
              Start New Analysis
            </Button>
          }
        />
      </>
    );
  }

  // UI-10 -- reuses the exact same date-formatting helper History's own
  // run rows already use (historyHelpers.formatRunTimestamp), rather than
  // a second, ad-hoc `toLocaleDateString` call that previously rendered
  // the SAME run's created_at differently ("15/9/2026" here vs "15 Sept
  // 2026, 07:06 pm" in History) -- a real cross-page inconsistency found
  // during this phase's audit (see reports/ui10_final_product_audit.md).
  const headerDescription = createdAt
    ? `${result.commodity_id} — evaluated ${result.context_date} — reopened from a run saved on ${formatRunTimestamp(createdAt)}`
    : `${result.commodity_id} — evaluated ${result.context_date}`;

  return (
    <>
      <PageHeader
        title="Procurement Decision Cockpit"
        description={headerDescription}
        actions={
          <>
            <Button to="/history" variant="secondary">
              Back to History
            </Button>
            <Button to="/analyze" variant="primary">
              New Analysis
            </Button>
          </>
        }
      />
      {runId && (
        <p className="text-small text-muted results-run-id">
          <Tooltip label={runId}>Run #{runId.slice(0, 8)}</Tooltip>
        </p>
      )}

      <DecisionHero result={result} />

      <ResultMetricGrid result={result} />

      <SelectedGroupCard finalSelection={result.final_selection} batchEligibility={result.batch_eligibility} />

      <VendorEconomics finalSelection={result.final_selection} />

      <section className="page-section">
        <h2 className="section-title">Candidate Groups Evaluated</h2>
        <DecisionFlowVisual
          evaluatedCount={result.candidate_group_count}
          selectedCount={result.selected_group_count}
        />
        <CandidateGroupsPanel finalSelection={result.final_selection} groupFormation={result.group_formation} />
      </section>

      <DecisionDiagnostics result={result} />

      <section className="page-section">
        <details className="formation-pool vendor-submission-detail">
          <summary className="text-small card-title">Vendor Submission Detail</summary>
          <VendorOutcomesTable batchEligibility={result.batch_eligibility} />
        </details>
      </section>

      <DecisionExplanation />

      <ResultSummary result={result} />

      <ResultActions />
    </>
  );
}

export default ResultsPage;
