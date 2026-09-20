// Landing polish -- Part 2D: shows the real "11 candidate groups" value as a
// cluster of dots rather than a bare number a second time. The 11 fixed
// offsets below are this exact real count (3 rows of 4/4/3), not a generic
// N-dot layout -- this cluster only ever represents ProductPreview.jsx's
// real, already-established demo value, never a placeholder for arbitrary
// data.

const DOT_R = 3.2;
const SPACING = 9;

const OFFSETS = [
  [-13.5, -SPACING], [-4.5, -SPACING], [4.5, -SPACING], [13.5, -SPACING],
  [-13.5, 0], [-4.5, 0], [4.5, 0], [13.5, 0],
  [-9, SPACING], [0, SPACING], [9, SPACING],
];

function CandidateGroupVisual({ cx, cy, isActive, baseDelay = 0 }) {
  return (
    <g className={`candidate-group-visual${isActive ? " is-active" : ""}`}>
      {OFFSETS.map(([dx, dy], index) => (
        <circle
          key={index}
          className="candidate-group-dot"
          cx={cx + dx}
          cy={cy + dy}
          r={DOT_R}
          style={{ animationDelay: `${baseDelay + index * 30}ms` }}
        />
      ))}
    </g>
  );
}

export default CandidateGroupVisual;
