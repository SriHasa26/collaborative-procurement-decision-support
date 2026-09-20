// Landing polish -- Part 2C: a small SVG procurement network showing the
// SAME real demo shape ProductPreview.jsx has always claimed (4 vendors ->
// 1 compatible pool -> 11 candidate groups), with generic "Vendor 1..4"
// labels only -- never fake vendor names/stats. Plays once when scrolled
// into view (via the shared useInViewOnce hook, same pattern as
// DecisionPipeline.jsx) and reuses the EXACT node-in/draw-edge keyframes
// HeroNetwork.jsx already established rather than a second implementation.
//
// `activeZone` (lifted from ProductPreview.jsx, driven by hover/focus/click
// on the three metric cards above this diagram) highlights the matching
// nodes/edges -- Part 2B's "metric cards become interactive" and Part 2F's
// "hover micro-interactions across nodes/pool/candidates" are the SAME
// mechanism, not two separate features.

import CandidateGroupVisual from "./CandidateGroupVisual";

const VENDORS = ["Vendor 1", "Vendor 2", "Vendor 3", "Vendor 4"];
const VENDOR_X = 34;
const VENDOR_YS = [16, 44, 72, 100];
const POOL = { x: 175, y: 58 };
const CANDIDATES = { x: 320, y: 58 };
const STAGE_GAP = 130;
const CANDIDATE_DOT_COUNT = 11;
const ENTRANCE_DURATION = 280;

// Exported so ProductPreview.jsx (the parent) can time the decision panel's
// own reveal to start right after this network's entrance fully settles --
// a single source of truth for that delay, mirroring DecisionPipeline.jsx's
// own exported DECISION_DELAY rather than a second guessed number.
export const NETWORK_SETTLE_DELAY =
  VENDOR_YS.length * STAGE_GAP + STAGE_GAP + (CANDIDATE_DOT_COUNT - 1) * 30 + ENTRANCE_DURATION;

function ProductPreviewNetwork({ isInView, activeZone }) {
  const poolDelay = VENDOR_YS.length * STAGE_GAP;
  const candidatesDelay = poolDelay + STAGE_GAP;

  return (
    <svg
      className={`product-preview-network${isInView ? " is-in-view" : ""}`}
      viewBox="0 0 380 116"
      role="img"
      aria-label="Four vendors are narrowed to one geographically compatible pool, then evaluated into 11 candidate groups."
    >
      {VENDOR_YS.map((y, index) => (
        <line
          key={`edge-vendor-${index}`}
          className={`product-preview-edge${activeZone === "vendors" || activeZone === "pool" ? " is-active" : ""}`}
          x1={VENDOR_X}
          y1={y}
          x2={POOL.x}
          y2={POOL.y}
          style={{ animationDelay: `${index * STAGE_GAP}ms` }}
        />
      ))}

      <line
        className={`product-preview-edge${activeZone === "pool" || activeZone === "candidates" ? " is-active" : ""}`}
        x1={POOL.x}
        y1={POOL.y}
        x2={CANDIDATES.x}
        y2={CANDIDATES.y}
        style={{ animationDelay: `${poolDelay}ms` }}
      />

      {VENDOR_YS.map((y, index) => (
        <g key={`vendor-${index}`}>
          <circle
            className={`product-preview-node${activeZone === "vendors" ? " is-active" : ""}`}
            cx={VENDOR_X}
            cy={y}
            r={7}
            style={{ animationDelay: `${index * STAGE_GAP}ms` }}
          />
          <text
            className="product-preview-node-label"
            x={VENDOR_X}
            y={y - 11}
            textAnchor="middle"
            style={{ animationDelay: `${index * STAGE_GAP}ms` }}
          >
            {VENDORS[index]}
          </text>
        </g>
      ))}

      <circle
        className={`product-preview-node product-preview-node-pool${activeZone === "pool" ? " is-active" : ""}`}
        cx={POOL.x}
        cy={POOL.y}
        r={9}
        style={{ animationDelay: `${poolDelay}ms` }}
      />
      <text
        className="product-preview-node-label"
        x={POOL.x}
        y={POOL.y - 15}
        textAnchor="middle"
        style={{ animationDelay: `${poolDelay}ms` }}
      >
        Compatible Pool
      </text>

      <CandidateGroupVisual
        cx={CANDIDATES.x}
        cy={CANDIDATES.y}
        isActive={activeZone === "candidates"}
        baseDelay={candidatesDelay}
      />
      <text
        className="product-preview-node-label"
        x={CANDIDATES.x}
        y={CANDIDATES.y - 22}
        textAnchor="middle"
        style={{ animationDelay: `${candidatesDelay}ms` }}
      >
        Candidate Evaluation
      </text>
    </svg>
  );
}

export default ProductPreviewNetwork;
