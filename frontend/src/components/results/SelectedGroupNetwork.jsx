// UI-5 -- an abstract hub-and-members diagram of one selected group's REAL
// vendor membership (vendor_ids, backend/models/decision_contracts.py's
// EvaluatedGroupResult). Reuses the exact technique and CSS classes UI-3's
// dashboard/NetworkOverview.jsx already established (same hub/edge/node
// markup, same .network-overview-* classes from styles/dashboard.css)
// rather than inventing a second implementation -- this is a "selected
// procurement relationship" diagram, not a geographic map: no
// coordinates, no distances are drawn, and it is labeled as such.
//
// UI-8 -- "Procurement Network": upgraded from a plain node-ID toggle
// into a real interactive network. Hover/focus now softly highlights the
// active node and its edge while dimming the rest (a genuine relationship
// cue, not decoration); click/Enter/Space opens an accessible detail
// panel showing ONLY real fields this response actually carries for that
// vendor -- its real cost share and savings
// (entry.decision.per_vendor_allocation) and, when available, its real
// submitted price/demand (batchEligibility.eligible_vendors[].
// vendor_input) -- never an invented field. Escape closes the panel.
//
// UI-9 -- "advanced SVG" pass (chosen over 3D -- see
// reports/ui9_advanced_visual_experience.md Sections 4-6 for the full
// justification): curved edges (a gentle quadratic bezier instead of a
// straight line -- purely a legibility/premium-feel choice, draws no new
// relationship that wasn't already there), a soft depth glow on the hub
// AND each node (CSS drop-shadow, not a new dependency), a hub color tied
// to this group's own REAL final_decision_state (supplementary to, never
// a replacement for, the existing DecisionStateBadge shown elsewhere on
// this card -- Section E's own explicit instruction), and a brief
// staggered entrance (edges "draw" in, nodes fade+scale in) reusing UI-8's
// existing motion primitives and the same site-wide reduced-motion
// override -- no new animation system, no camera, no continuous loop.

import { useEffect, useMemo, useRef, useState } from "react";
import { DECISION_STATE_META } from "../common/decisionStateMeta";
import { formatCurrency, formatNumber } from "./resultHelpers";

function layoutNodes(count, radius = 110, center = 140) {
  return Array.from({ length: count }, (_, i) => {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2;
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
    };
  });
}

// A gentle quadratic-bezier curve from the hub to each node, bowed
// perpendicular to the straight-line direction by a small, fixed amount
// -- purely a visual/legibility choice (curved edges read as less
// mechanical than a spoke of straight lines); it represents exactly the
// same hub-to-vendor membership relationship a straight line would, never
// a new or different one.
function curvedEdgePath(cx, cy, x, y) {
  const mx = (cx + x) / 2;
  const my = (cy + y) / 2;
  const dx = x - cx;
  const dy = y - cy;
  const len = Math.hypot(dx, dy) || 1;
  const bow = 14;
  const controlX = mx + (-dy / len) * bow;
  const controlY = my + (dx / len) * bow;
  return `M ${cx},${cy} Q ${controlX},${controlY} ${x},${y}`;
}

function buildAllocationLookup(perVendorAllocation) {
  const map = new Map();
  for (const allocation of perVendorAllocation ?? []) {
    map.set(allocation.vendor_id, allocation);
  }
  return map;
}

function buildVendorInputLookup(batchEligibility) {
  const map = new Map();
  for (const vendor of batchEligibility?.eligible_vendors ?? []) {
    if (vendor.vendor_input) map.set(vendor.vendor_id, vendor.vendor_input);
  }
  return map;
}

function VendorDetailPanel({ vendorId, allocation, vendorInput }) {
  const facts = [];
  if (vendorInput?.individual_price_rs_per_kg != null) {
    facts.push({ label: "Submitted price", value: formatCurrency(vendorInput.individual_price_rs_per_kg) + "/kg" });
  }
  if (vendorInput?.q_i != null) {
    facts.push({ label: "Demand (q_i)", value: `${formatNumber(vendorInput.q_i)} kg/day` });
  }
  if (allocation?.share_rs != null) {
    facts.push({ label: "Cost share", value: formatCurrency(allocation.share_rs) });
  }
  if (allocation?.individual_savings_rs != null) {
    facts.push({ label: "Individual savings", value: formatCurrency(allocation.individual_savings_rs) });
  }
  if (allocation?.consumption_time_days != null) {
    facts.push({ label: "Consumption time", value: `${allocation.consumption_time_days} day(s)` });
  }

  return (
    <div className="network-detail-panel" role="region" aria-label={`Details for vendor ${vendorId}`}>
      <p className="text-label">{vendorId}</p>
      {facts.length === 0 ? (
        <p className="text-small text-muted">No further detail is available for this vendor in this response.</p>
      ) : (
        <dl className="network-detail-facts">
          {facts.map((fact) => (
            <div key={fact.label}>
              <dt className="text-small text-muted">{fact.label}</dt>
              <dd className="text-small">{fact.value}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

function SelectedGroupNetwork({ entry, batchEligibility }) {
  const vendorIds = entry.vendor_ids;
  const groupId = entry.decision.group_id;
  const [selectedVendorId, setSelectedVendorId] = useState(null);
  const [hoveredVendorId, setHoveredVendorId] = useState(null);
  const containerRef = useRef(null);

  const positions = useMemo(() => layoutNodes(vendorIds.length), [vendorIds.length]);
  const allocationByVendorId = useMemo(() => buildAllocationLookup(entry.decision.per_vendor_allocation), [entry]);
  const vendorInputByVendorId = useMemo(() => buildVendorInputLookup(batchEligibility), [batchEligibility]);
  const center = 140;
  const activeVendorId = hoveredVendorId ?? selectedVendorId;
  // UI-9 -- the hub's color reflects this group's own real
  // final_decision_state (DECISION_STATE_META, the same exhaustive
  // mapping DecisionStateBadge itself uses) -- supplementary color
  // reinforcement only; the badge remains the actual semantic source.
  const hubVariant = DECISION_STATE_META[entry.final_decision_state]?.variant ?? "neutral";

  useEffect(() => {
    if (!selectedVendorId) return undefined;
    function handleKeyDown(event) {
      if (event.key === "Escape") setSelectedVendorId(null);
    }
    const node = containerRef.current;
    node?.addEventListener("keydown", handleKeyDown);
    return () => node?.removeEventListener("keydown", handleKeyDown);
  }, [selectedVendorId]);

  function toggleVendor(vendorId) {
    setSelectedVendorId((prev) => (prev === vendorId ? null : vendorId));
  }

  return (
    <div className="selected-group-network" ref={containerRef}>
      <p className="text-label">Procurement Network</p>
      <p className="text-small text-muted">Selected procurement relationship — not a geographic map.</p>
      <svg
        className={`network-overview-svg${activeVendorId ? " has-active-node" : ""}`}
        viewBox="0 0 280 280"
        role="img"
        aria-label={`Group ${groupId} with ${vendorIds.length} vendors: ${vendorIds.join(", ")}. Select a vendor to view its details.`}
      >
        {positions.map((pos, index) => {
          const vendorId = vendorIds[index];
          const isActiveEdge = vendorId === activeVendorId;
          return (
            <path
              key={`edge-${vendorId}`}
              className={`network-overview-edge network-edge-draw${isActiveEdge ? " is-active" : ""}`}
              style={{ animationDelay: `${index * 50}ms` }}
              d={curvedEdgePath(center, center, pos.x, pos.y)}
              fill="none"
            />
          );
        })}

        <circle
          className={`network-overview-hub network-overview-hub-${hubVariant}`}
          cx={center}
          cy={center}
          r={26}
        />
        <text className="network-overview-hub-label" x={center} y={center + 4}>
          Group
        </text>

        {positions.map((pos, index) => {
          const vendorId = vendorIds[index];
          const isSelected = vendorId === selectedVendorId;
          const isActive = vendorId === activeVendorId;
          return (
            <g
              key={vendorId}
              className={`network-overview-node network-node-enter${isSelected ? " is-selected" : ""}${isActive ? " is-active" : ""}`}
              style={{ animationDelay: `${100 + index * 50}ms` }}
              tabIndex={0}
              role="button"
              aria-pressed={isSelected}
              aria-label={`Vendor ${vendorId}`}
              onClick={() => toggleVendor(vendorId)}
              onMouseEnter={() => setHoveredVendorId(vendorId)}
              onMouseLeave={() => setHoveredVendorId(null)}
              onFocus={() => setHoveredVendorId(vendorId)}
              onBlur={() => setHoveredVendorId(null)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  toggleVendor(vendorId);
                }
              }}
            >
              <circle cx={pos.x} cy={pos.y} r={17} />
              <text x={pos.x} y={pos.y + 4}>
                {index + 1}
              </text>
            </g>
          );
        })}
      </svg>

      <p className="text-small" aria-live="polite">
        {selectedVendorId ? `Selected: ${selectedVendorId}` : "Select a node to see its vendor details."}
      </p>

      {selectedVendorId && (
        <VendorDetailPanel
          vendorId={selectedVendorId}
          allocation={allocationByVendorId.get(selectedVendorId)}
          vendorInput={vendorInputByVendorId.get(selectedVendorId)}
        />
      )}
    </div>
  );
}

export default SelectedGroupNetwork;
