// Phase 7B -- generic surface container. Deliberately minimal: layout and
// content are entirely up to the caller via children.
// UI-1 -- added an optional `variant` prop ("standard" -- the default,
// pixel-identical to Phase 7B -- "elevated", "interactive", or
// "highlighted"; see components.css). No existing call site passes a
// variant, so every current page renders exactly as before.

function Card({ className = "", variant = "standard", children, ...rest }) {
  const variantClass = variant && variant !== "standard" ? `card-${variant}` : "";
  return (
    <div className={`card ${variantClass} ${className}`.trim()} {...rest}>
      {children}
    </div>
  );
}

export default Card;
