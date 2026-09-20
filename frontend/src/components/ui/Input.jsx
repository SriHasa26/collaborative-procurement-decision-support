// UI-1 -- a styled, reusable text input primitive for future form work
// (UI-4). NOT wired into the existing analysis form or auth forms yet --
// FormField.jsx/AnalysisForm.jsx/SignInPage.jsx/SignUpPage.jsx are
// deliberately untouched this phase (see this phase's own "do not
// redesign the analysis form yet" instruction). Visually identical to the
// input styling analysis.css already established (same tokens, same
// values, just under a standalone class so it works outside a
// `.form-field` wrapper too) -- a future page adopting this component
// looks like part of the same product, not a second visual language.

function Input({ className = "", ...rest }) {
  return <input className={`ui-input ${className}`.trim()} {...rest} />;
}

export default Input;
