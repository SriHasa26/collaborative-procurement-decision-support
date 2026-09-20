// UI-3 -- "Procurement Group Overview": a real-data visualization of the
// user's latest SELECTED group's actual vendor membership
// (final_selection.selected_results[0].vendor_ids -- real vendor_id
// strings the backend returned, never invented). This is deliberately
// labeled "Group Overview", not "Network" or "Geographic Map": the result
// payload exposes group MEMBERSHIP (which vendors belong to the same
// candidate group) but no geographic coordinates or distance figures
// (backend/models/group_formation_contracts.py's GroupFormationResult
// carries pool_vendor_ids, not lat/lon), so drawing anything resembling a
// real map would misrepresent data that does not exist in this response.
// Per this phase's own instruction ("If it does NOT expose sufficient
// relationship information: do NOT invent geographic relationships...
// create a clearly labelled Procurement Group Overview visual using
// actual vendor membership only"), that is exactly what this component
// does -- an abstract hub-and-members diagram, not a map. No map/graph
// library was added; this reuses the same inline-SVG + CSS approach
// UI-2's HeroNetwork established, but every node here is real.

import { useState } from "react";
import Card from "../common/Card";
import EmptyState from "../common/EmptyState";

function layoutNodes(count, radius = 130, center = 160) {
  return Array.from({ length: count }, (_, i) => {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2;
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
    };
  });
}

function NetworkOverview({ latestSelectedRun }) {
  const [selectedVendorId, setSelectedVendorId] = useState(null);

  if (!latestSelectedRun) {
    return (
      <Card className="dashboard-panel">
        <p className="text-label">Procurement Group Overview</p>
        <EmptyState
          icon="◎"
          title="No collaborative group yet"
          description="A group's actual vendor membership will be visualized here once one is selected."
        />
      </Card>
    );
  }

  const primaryGroup = latestSelectedRun.result.final_selection.selected_results[0];
  const vendorIds = primaryGroup.vendor_ids;
  const positions = layoutNodes(vendorIds.length);
  const center = 160;

  return (
    <Card className="dashboard-panel">
      <p className="text-label">Procurement Group Overview</p>
      <p className="text-small text-muted">
        Actual vendor membership of your most recent selected group — not a geographic map.
      </p>

      <svg className="network-overview-svg" viewBox="0 0 320 320" role="img" aria-label={`Selected group with ${vendorIds.length} vendors: ${vendorIds.join(", ")}`}>
        {positions.map((pos, index) => (
          <line
            key={`edge-${vendorIds[index]}`}
            className="network-overview-edge"
            x1={center}
            y1={center}
            x2={pos.x}
            y2={pos.y}
          />
        ))}

        <circle className="network-overview-hub" cx={center} cy={center} r={28} />
        <text className="network-overview-hub-label" x={center} y={center + 4}>
          Group
        </text>

        {positions.map((pos, index) => {
          const vendorId = vendorIds[index];
          const isSelected = vendorId === selectedVendorId;
          return (
            <g
              key={vendorId}
              className={`network-overview-node${isSelected ? " is-selected" : ""}`}
              tabIndex={0}
              role="button"
              aria-pressed={isSelected}
              onClick={() => setSelectedVendorId(isSelected ? null : vendorId)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setSelectedVendorId(isSelected ? null : vendorId);
                }
              }}
            >
              <circle cx={pos.x} cy={pos.y} r={18} />
              <text x={pos.x} y={pos.y + 4}>
                {index + 1}
              </text>
            </g>
          );
        })}
      </svg>

      <p className="text-small" aria-live="polite">
        {selectedVendorId ? `Selected: ${selectedVendorId}` : `${vendorIds.length} vendor(s) in this group — select a node for its ID.`}
      </p>
    </Card>
  );
}

export default NetworkOverview;
