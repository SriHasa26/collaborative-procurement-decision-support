// UI-8 -- a small, genuinely accessible tooltip: unlike the native
// `title` attribute it replaces at its two call sites (History's
// RunHistoryRow.jsx, Results' reopened-run line), this is reachable by
// keyboard (a real <button>, Tab-focusable) and works on mobile (a tap
// toggles it -- never hover-only, per this phase's explicit requirement).
// Used only where it carries genuine value (a technical run ID) -- not
// added to already-self-explanatory labels.

import { useId, useState } from "react";

function Tooltip({ label, children }) {
  const [isOpen, setIsOpen] = useState(false);
  const tooltipId = useId();

  function close() {
    setIsOpen(false);
  }

  return (
    <span className="tooltip-wrapper">
      <button
        type="button"
        className="tooltip-trigger"
        aria-describedby={isOpen ? tooltipId : undefined}
        onClick={() => setIsOpen((prev) => !prev)}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={close}
        onFocus={() => setIsOpen(true)}
        onBlur={close}
        onKeyDown={(event) => {
          if (event.key === "Escape") close();
        }}
      >
        {children}
      </button>
      {isOpen && (
        <span role="tooltip" id={tooltipId} className="tooltip-bubble">
          {label}
        </span>
      )}
    </span>
  );
}

export default Tooltip;
