// UI-3 -- the authenticated dashboard. Protected by the EXISTING
// ProtectedRoute (see routes/AppRoutes.jsx) -- no second auth mechanism.
// Data comes exclusively from useDashboardData.js, which calls the
// EXISTING, centralized API client (api/procurementApi.js) -- this page
// never calls fetch() itself, never reads/writes a user_id, and never
// requests another user's data (the backend already scopes both
// GET /procurement/runs and GET /procurement/runs/{run_id} to the
// verified, authenticated caller -- Phase 8F/8G, unchanged).

import { useAuth } from "../auth/useAuth";
import ActionPanel from "../components/dashboard/ActionPanel";
import DashboardSkeleton from "../components/dashboard/DashboardSkeleton";
import KPISection from "../components/dashboard/KPISection";
import LatestDecisionCard from "../components/dashboard/LatestDecisionCard";
import NetworkOverview from "../components/dashboard/NetworkOverview";
import RecentAnalyses from "../components/dashboard/RecentAnalyses";
import SavingsAnalytics from "../components/dashboard/SavingsAnalytics";
import { buildDashboardMetrics, buildSavingsSeries, getLatestSelectedRun } from "../components/dashboard/dashboardMetrics";
import { MAX_DETAIL_FETCH, useDashboardData } from "../components/dashboard/useDashboardData";
import Button from "../components/common/Button";
import ErrorState from "../components/common/ErrorState";
import PageHeader from "../components/common/PageHeader";

function DashboardPage() {
  const { user } = useAuth();
  const { status, summaries, storedRuns, error, reload } = useDashboardData();

  const firstName = user?.email ? user.email.split("@")[0] : null;

  if (status === "loading") {
    return (
      <>
        <PageHeader
          title="Procurement Intelligence"
          description="Understand your procurement activity, collaboration opportunities, and realized value."
        />
        <DashboardSkeleton />
      </>
    );
  }

  if (status === "error") {
    return (
      <>
        <PageHeader title="Procurement Intelligence" />
        <ErrorState
          title="We couldn't load your procurement data"
          description={error}
          actions={
            <Button type="button" variant="primary" onClick={reload}>
              Try Again
            </Button>
          }
        />
      </>
    );
  }

  const metrics = buildDashboardMetrics(storedRuns);
  const latestSelectedRun = getLatestSelectedRun(storedRuns);
  const savingsSeries = buildSavingsSeries(storedRuns);
  const isCapped = summaries.length > storedRuns.length;

  return (
    <>
      <div className="dashboard-intro animate-in">
        <PageHeader
          title="Procurement Intelligence"
          description={
            firstName
              ? `Welcome, ${firstName} — here's your procurement activity, collaboration opportunities, and realized value.`
              : "Understand your procurement activity, collaboration opportunities, and realized value."
          }
          actions={
            <Button to="/analyze" variant="primary">
              + New Analysis
            </Button>
          }
        />
      </div>

      <KPISection metrics={metrics} />

      {isCapped && (
        <p className="text-small text-muted">
          Metrics reflect your {MAX_DETAIL_FETCH} most recent analyses out of {metrics.totalAnalyses} total.
        </p>
      )}

      <div className="dashboard-grid-2">
        <NetworkOverview latestSelectedRun={latestSelectedRun} />
        <LatestDecisionCard latestSelectedRun={latestSelectedRun} />
      </div>

      <div className="dashboard-grid-2">
        <SavingsAnalytics savingsSeries={savingsSeries} />
        <RecentAnalyses storedRuns={storedRuns} totalAnalyses={metrics.totalAnalyses} />
      </div>

      <ActionPanel />
    </>
  );
}

export default DashboardPage;
