// UI-6 -- Section 16: loading skeleton roughly matching the real run-row
// layout, shown while useHistoryData's status is "loading". Reuses UI-3's
// existing `.skeleton-block`/shimmer keyframe (styles/dashboard.css) --
// no second shimmer implementation -- which already respects
// prefers-reduced-motion via the site-wide global rule.

function HistorySkeleton() {
  return (
    <div className="history-skeleton" aria-hidden="true">
      {[0, 1, 2, 3].map((index) => (
        <div key={index} className="skeleton-block history-skeleton-row" />
      ))}
    </div>
  );
}

export default HistorySkeleton;
