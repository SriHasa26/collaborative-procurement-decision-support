// UI-1 -- a standalone Label primitive, visually matching FormField.jsx's
// existing inline `<label className="text-label">` (Phase 7C) -- not a
// second style, just a reusable component form for it. FormField.jsx
// itself is left untouched; a future phase can adopt Label without
// affecting today's analysis form.

function Label({ htmlFor, className = "", children }) {
  return (
    <label htmlFor={htmlFor} className={`text-label ${className}`.trim()}>
      {children}
    </label>
  );
}

export default Label;
