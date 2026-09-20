// UI-1 -- see Input.jsx's comment; the same reasoning applies here.

function Select({ className = "", children, ...rest }) {
  return (
    <select className={`ui-select ${className}`.trim()} {...rest}>
      {children}
    </select>
  );
}

export default Select;
