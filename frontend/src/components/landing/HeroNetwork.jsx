// UI-2 -- an illustrative, static procurement-network visualization
// (inline SVG + CSS keyframe animation -- no charting/network library
// added). Communicates "vendors -> compatible connections -> a
// collaborative procurement group -> a decision" at a glance. This is
// NOT live data, NOT a real analysis result, and NOT the specific
// vendor/location names used anywhere in this project's real test data --
// every label here is a generic placeholder ("Vendor A"..."Vendor D"),
// and the caption says so explicitly (both visually and via an
// accessible text equivalent for the SVG, per this phase's own
// accessibility requirement). Animation runs once on mount; the existing
// global prefers-reduced-motion rule (global.css) already neutralizes
// every CSS animation/transition site-wide, so a user with that
// preference sees the finished state immediately, with no extra code
// needed here.

const HUB = { x: 200, y: 200 };
const NODES = [
  { id: "a", label: "Vendor A", x: 200, y: 60 },
  { id: "b", label: "Vendor B", x: 70, y: 165 },
  { id: "c", label: "Vendor C", x: 330, y: 165 },
  { id: "d", label: "Vendor D", x: 120, y: 330 },
  { id: "e", label: "Vendor E", x: 280, y: 330 },
];

function HeroNetwork() {
  return (
    <figure className="hero-visual" aria-label="Illustration of vendors connecting into a collaborative procurement group">
      <svg
        className="hero-network"
        viewBox="0 0 400 400"
        role="img"
        aria-labelledby="hero-network-title hero-network-desc"
      >
        <title id="hero-network-title">Collaborative procurement network</title>
        <desc id="hero-network-desc">
          An illustrative diagram, not live data: five vendor nodes connect to a central
          procurement hub, representing how fragmented demand becomes a compatible group,
          resulting in a collaborative Buy Together decision.
        </desc>

        {NODES.map((node, index) => (
          <line
            key={`edge-${node.id}`}
            className="hero-network-edge"
            x1={HUB.x}
            y1={HUB.y}
            x2={node.x}
            y2={node.y}
            style={{ animationDelay: `${500 + index * 90}ms` }}
          />
        ))}

        {NODES.map((node, index) => (
          <g key={node.id} className="hero-network-node">
            <circle
              className="hero-network-node-circle"
              cx={node.x}
              cy={node.y}
              r={20}
              style={{ animationDelay: `${index * 80}ms` }}
            />
            <text
              className="hero-network-node-label"
              x={node.x}
              y={node.y + 36}
              style={{ animationDelay: `${index * 80}ms` }}
            >
              {node.label}
            </text>
          </g>
        ))}

        {/* Pulse ring: a single, non-repeating "activation" animation on
            the hub, timed to fire once the connections have finished
            drawing (per this phase's "nodes fade -> connections draw ->
            central collaboration state activates -> decision indicator
            appears" sequence). */}
        <circle className="hero-network-pulse" cx={HUB.x} cy={HUB.y} r={26} />

        <g className="hero-network-node hero-network-node-hub">
          <circle className="hero-network-node-circle" cx={HUB.x} cy={HUB.y} r={26} />
          <text className="hero-network-hub-label" x={HUB.x} y={HUB.y + 4}>
            Group
          </text>
        </g>

        <g className="hero-network-badge">
          <rect x={HUB.x - 62} y={HUB.y + 42} width={124} height={26} rx={13} fill="var(--color-success-light)" stroke="var(--color-success-border)" />
          <text className="hero-network-badge-text" x={HUB.x} y={HUB.y + 59}>
            ✓ Buy Together
          </text>
        </g>
      </svg>
      <figcaption className="hero-network-caption text-small text-muted">
        Illustrative network — not live vendor data.
      </figcaption>
    </figure>
  );
}

export default HeroNetwork;
