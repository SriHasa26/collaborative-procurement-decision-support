// Phase 7B -- consistent page header: title + description + optional
// action(s) (e.g. a CTA button), used at the top of every real page.
// UI-1 -- `.animate-in` (global.css) gives every page a single, subtle
// entrance -- the one deliberately-chosen place for this, rather than
// animating every card on every page (this phase's own "avoid animation
// on every element" principle). Respects prefers-reduced-motion globally
// (global.css's reduced-motion block), no extra code needed here.

function PageHeader({ title, description, actions }) {
  return (
    <div className="page-header animate-in">
      <div className="page-header-text">
        <h1 className="page-title">{title}</h1>
        {description && <p className="text-body">{description}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </div>
  );
}

export default PageHeader;
