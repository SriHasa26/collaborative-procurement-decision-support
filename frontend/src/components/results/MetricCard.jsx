// Phase 7E -- one summary metric (a backend-provided count), presented as
// a small Card. Purely presentational -- `value` is always a number or
// string already computed by the backend.
// UI-1 -- added an optional `tone="emphasis"` prop (default "default" is
// pixel-identical to Phase 7E) for a metric that should visually dominate
// the rest of a page -- this phase's own "₹3,732.60 expected savings
// should be visually stronger than metadata" principle, made reusable.
// ResultsSummary.jsx's existing call sites pass no `tone`, so today's
// Results page is unaffected; this is a primitive for later UI work.
// UI-3 -- added an optional `hint` line, for a dashboard KPI whose value
// is honestly "—" (not enough data yet) rather than a possibly-misleading
// bare dash -- see components/dashboard/KPISection.jsx. No existing call
// site passes a hint, so nothing else changes.

import Card from "../common/Card";

function MetricCard({ label, value, tone = "default", hint }) {
  const toneClass = tone === "emphasis" ? "metric-card-emphasis" : "";
  return (
    <Card className={`metric-card ${toneClass}`.trim()}>
      <span className="text-label">{label}</span>
      <span className="metric-card-value">{value}</span>
      {hint && <span className="text-small text-muted metric-card-hint">{hint}</span>}
    </Card>
  );
}

export default MetricCard;
