// UI-7 -- Procurement Insights & Analytics. Reuses UI-6's own
// useHistoryData.js UNCHANGED -- the same {run_id, created_at, commodity,
// run_status, detail} entries, the same real, unbounded total count, and
// the same bounded (HISTORY_DETAIL_FETCH_LIMIT) detail-enrichment
// strategy History already established and this phase's own brief
// explicitly asks to respect ("UI-7 must respect this limitation... reuse
// that bounded strategy"). No second fetch implementation, no new
// endpoint, no additional API load beyond what a History page visit
// already causes.
//
// Every number below is a plain count/sum/grouping computed in
// insightsMetrics.js (and, where already covered, dashboardMetrics.js's
// own buildSavingsSeries) -- see that file's own comments for exactly
// what each metric means and does not mean.

import { useMemo } from "react";
import Button from "../components/common/Button";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import PageHeader from "../components/common/PageHeader";
import { buildSavingsSeries } from "../components/dashboard/dashboardMetrics";
import SavingsAnalytics from "../components/dashboard/SavingsAnalytics";
import { useHistoryData } from "../components/history/useHistoryData";
import CommodityBreakdown from "../components/insights/CommodityBreakdown";
import DataScopeBanner from "../components/insights/DataScopeBanner";
import DecisionDistribution from "../components/insights/DecisionDistribution";
import EvidenceObservations from "../components/insights/EvidenceObservations";
import GroupSizeAnalysis from "../components/insights/GroupSizeAnalysis";
import InsightsOverviewMetrics from "../components/insights/InsightsOverviewMetrics";
import InsightsSkeleton from "../components/insights/InsightsSkeleton";
import {
  buildCommodityBreakdown,
  buildDecisionDistribution,
  buildEvidenceObservations,
  buildGroupSizeDistribution,
  buildVendorParticipation,
  summarizeSavings,
} from "../components/insights/insightsMetrics";
import MethodologyNote from "../components/insights/MethodologyNote";
import SavingsOverview from "../components/insights/SavingsOverview";
import VendorParticipation from "../components/insights/VendorParticipation";

const PAGE_SUBTITLE = "Explore patterns across your procurement decisions.";

function InsightsPage() {
  const { status, entries, totalCount, enrichedCount, error, reload } = useHistoryData();

  const enrichedDetails = useMemo(() => entries.map((entry) => entry.detail).filter(Boolean), [entries]);
  const decisionDistribution = useMemo(() => buildDecisionDistribution(entries), [entries]);
  const savingsSeries = useMemo(() => buildSavingsSeries(enrichedDetails), [enrichedDetails]);
  const savingsSummary = useMemo(() => summarizeSavings(savingsSeries), [savingsSeries]);
  const commodityBreakdown = useMemo(() => buildCommodityBreakdown(entries), [entries]);
  const vendorParticipation = useMemo(() => buildVendorParticipation(entries), [entries]);
  const groupSizeDistribution = useMemo(() => buildGroupSizeDistribution(entries), [entries]);
  const observations = useMemo(
    () =>
      buildEvidenceObservations({
        decisionDistribution,
        savingsSummary,
        totalRunsWithSavingsPossible: decisionDistribution.consideredCount,
        commodityBreakdown,
        vendorParticipation,
        groupSizeDistribution,
      }),
    [decisionDistribution, savingsSummary, commodityBreakdown, vendorParticipation, groupSizeDistribution]
  );

  return (
    <>
      <PageHeader
        title="Procurement Insights"
        description={PAGE_SUBTITLE}
        actions={
          <>
            <Button to="/history" variant="secondary">
              Run History
            </Button>
            <Button to="/analyze" variant="primary">
              New Analysis
            </Button>
          </>
        }
      />

      {status === "loading" && <InsightsSkeleton />}

      {status === "error" && (
        <ErrorState
          title="Unable to load procurement insights"
          description={error}
          actions={
            <>
              <Button type="button" variant="primary" onClick={reload}>
                Retry
              </Button>
              <Button to="/dashboard" variant="secondary">
                Back to Dashboard
              </Button>
            </>
          }
        />
      )}

      {status === "success" && totalCount === 0 && (
        <EmptyState
          icon="≡"
          title="No procurement runs yet"
          description="Insights will appear here once you have completed at least one procurement analysis."
          actions={
            <Button to="/analyze" variant="primary">
              Start Your First Analysis
            </Button>
          }
        />
      )}

      {status === "success" && totalCount > 0 && (
        <>
          <DataScopeBanner totalCount={totalCount} enrichedCount={enrichedCount} />

          <InsightsOverviewMetrics
            totalCount={totalCount}
            savingsSummary={savingsSummary}
            buyTogetherCount={decisionDistribution.counts.BUY_TOGETHER ?? 0}
            consideredCount={decisionDistribution.consideredCount}
            vendorCount={vendorParticipation.vendors.length}
            vendorConsideredRunCount={vendorParticipation.consideredRunCount}
          />

          <DecisionDistribution decisionDistribution={decisionDistribution} />

          <SavingsOverview savingsSummary={savingsSummary} />

          <section className="page-section">
            <SavingsAnalytics savingsSeries={savingsSeries} />
          </section>

          <CommodityBreakdown commodityBreakdown={commodityBreakdown} />

          <VendorParticipation vendorParticipation={vendorParticipation} />

          <GroupSizeAnalysis groupSizeDistribution={groupSizeDistribution} />

          <EvidenceObservations observations={observations} />

          <MethodologyNote />
        </>
      )}
    </>
  );
}

export default InsightsPage;
