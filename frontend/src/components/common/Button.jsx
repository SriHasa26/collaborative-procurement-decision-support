// Phase 7B -- reusable Button. Renders a real <button> for in-page actions,
// or a react-router <Link> (still visually a button) when a `to` prop is
// given for navigation -- so navigation always uses an actual link element,
// never a button with a manual onClick(navigate) side effect.
// UI-1 -- variants gained "ghost"/"danger" (components.css already defines
// .btn-ghost/.btn-danger; no JS change was needed for that, since the
// className is already built from whatever `variant` string is passed).
// Added an optional `isLoading` prop: shows an inline spinner, forces
// `aria-busy`, and disables the button -- a reusable alternative to the
// manual aria-busy + separate <LoadingState> pattern AnalysisForm.jsx
// already uses (left completely untouched; this is an additive capability
// for future pages, not a replacement of that existing, working pattern).
// UI-2 -- added an optional `href` prop: renders a real <a> (e.g. for a
// same-page anchor CTA like the hero's "See How It Works", which must
// jump to a section, not push a new browser-history route the way a
// react-router `to` would).

import { Link } from "react-router-dom";

function Button({
  variant = "primary",
  to,
  href,
  type = "button",
  className = "",
  isLoading = false,
  disabled = false,
  children,
  ...rest
}) {
  const classes = `btn btn-${variant} ${className}`.trim();

  if (to) {
    return (
      <Link to={to} className={classes} {...rest}>
        {children}
      </Link>
    );
  }

  if (href) {
    return (
      <a href={href} className={classes} {...rest}>
        {children}
      </a>
    );
  }

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || isLoading}
      aria-busy={isLoading || undefined}
      {...rest}
    >
      {isLoading && <span className="btn-spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}

export default Button;
