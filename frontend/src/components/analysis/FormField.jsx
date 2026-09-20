// Phase 7C -- consistent label + control + hint/error wrapper. A visible
// <label> is always rendered (never placeholder-text-as-label); `children`
// is the actual input/select element, composed in by the caller.

function FormField({ id, label, error, hint, children }) {
  return (
    <div className="form-field">
      <label htmlFor={id} className="text-label">
        {label}
      </label>
      {children}
      {error ? (
        <span className="form-field-error" role="alert">
          {error}
        </span>
      ) : (
        hint && <span className="text-small text-muted">{hint}</span>
      )}
    </div>
  );
}

export default FormField;
