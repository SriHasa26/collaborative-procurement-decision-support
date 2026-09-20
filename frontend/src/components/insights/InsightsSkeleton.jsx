// UI-7 -- Section 13: loading skeleton roughly matching the final
// section layout. Reuses UI-3's existing `.skeleton-block` shimmer
// (styles/dashboard.css) -- no second shimmer implementation -- which
// already respects prefers-reduced-motion via the site-wide global rule.

function InsightsSkeleton() {
  return (
    <div className="dashboard-skeleton" aria-hidden="true">
      <div className="skeleton-block insights-skeleton-banner" />
      <div className="skeleton-block skeleton-kpi" />
      <div className="skeleton-block skeleton-panel" />
      <div className="skeleton-block skeleton-panel" />
    </div>
  );
}

export default InsightsSkeleton;
