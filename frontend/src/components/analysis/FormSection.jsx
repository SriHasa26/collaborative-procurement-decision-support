// Phase 7C -- a form section: a Card-styled <fieldset>/<legend> grouping
// related controls, per this phase's accessibility requirement to use
// fieldset/legend where appropriate.
// UI-8 -- added an optional `className` (default ""), merged the same
// way Card.jsx already merges its own -- AnalysisForm.jsx's only call
// site now passes "animate-in" so each wizard step crossfades in on
// change; no existing call site passed a className before, so nothing
// else changes.

function FormSection({ title, description, className = "", children }) {
  return (
    <fieldset className={`card form-section ${className}`.trim()}>
      <legend className="card-title">{title}</legend>
      {description && <p className="text-small form-section-description">{description}</p>}
      <div className="form-section-body">{children}</div>
    </fieldset>
  );
}

export default FormSection;
