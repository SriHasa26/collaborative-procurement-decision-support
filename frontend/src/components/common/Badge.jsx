// Phase 7B -- generic small status pill. `icon` is a plain text/emoji
// glyph (not an icon-library dependency) and is marked aria-hidden since
// the label text always carries the actual meaning -- icons never carry
// meaning alone (Phase 7B accessibility requirement).

function Badge({ variant = "neutral", icon, children }) {
  return (
    <span className={`badge badge-${variant}`}>
      {icon && (
        <span className="badge-icon" aria-hidden="true">
          {icon}
        </span>
      )}
      {children}
    </span>
  );
}

export default Badge;
