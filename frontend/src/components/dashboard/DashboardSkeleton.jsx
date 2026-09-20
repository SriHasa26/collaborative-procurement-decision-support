// UI-3 -- a polished loading placeholder shown while useDashboardData is
// still fetching, instead of a blank screen. Purely presentational,
// non-interactive (aria-hidden) shapes -- never a real number, never a
// fabricated value. Uses a subtle CSS shimmer, respecting
// prefers-reduced-motion via the existing global rule (global.css) with
// no extra code.

function SkeletonBlock({ className = "" }) {
  return <div className={`skeleton-block ${className}`.trim()} aria-hidden="true" />;
}

function DashboardSkeleton() {
  return (
    <div className="dashboard-skeleton" role="status" aria-label="Loading your procurement dashboard">
      <div className="value-grid">
        <SkeletonBlock className="skeleton-kpi" />
        <SkeletonBlock className="skeleton-kpi" />
        <SkeletonBlock className="skeleton-kpi" />
        <SkeletonBlock className="skeleton-kpi" />
      </div>
      <div className="dashboard-grid-2">
        <SkeletonBlock className="skeleton-panel" />
        <SkeletonBlock className="skeleton-panel" />
      </div>
      <div className="dashboard-grid-2">
        <SkeletonBlock className="skeleton-panel" />
        <SkeletonBlock className="skeleton-panel" />
      </div>
    </div>
  );
}

export default DashboardSkeleton;
