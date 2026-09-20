// UI-5 -- Section 8: "Candidate Groups Evaluated". Replaces the former
// GroupDecisionList.jsx (Phase 7E), same underlying data
// (final_selection.all_evaluated_results) and the same, unmodified
// sortEvaluatedGroups() ordering (selected first, then by
// final_decision_state, then alphabetically) -- only the presentation
// changed, from a flat table to compact, expandable rows (so a run with
// many candidates does not render as an overwhelming wall of detail).
// Every selected group starts expanded (it is the most important row);
// every other row starts collapsed. Also folds in the former
// GroupFormationSummary.jsx's (Phase 7E) compatibility-pool count as a
// one-line intro -- this panel is the natural place to read "how many
// candidates, from how many pools" before drilling into any one of them.

import { useState } from "react";
import CandidateGroupRow from "./CandidateGroupRow";
import { sortEvaluatedGroups } from "./resultHelpers";

function CandidateGroupsPanel({ finalSelection, groupFormation }) {
  const allEvaluated = finalSelection?.all_evaluated_results ?? [];
  const selectedSet = new Set(finalSelection?.selected_group_ids ?? []);
  const rows = sortEvaluatedGroups(allEvaluated, finalSelection?.selected_group_ids);

  const [expandedIds, setExpandedIds] = useState(() => new Set(selectedSet));

  function toggleRow(groupId) {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  }

  if (!groupFormation) {
    return (
      <p className="text-small text-muted">
        Group formation was not attempted for this run (see the run status above for why).
      </p>
    );
  }

  const poolCount = groupFormation.pools?.length ?? 0;

  if (rows.length === 0) {
    return (
      <p className="text-small text-muted">
        No candidate groups were formed from the eligible vendors for this run
        {groupFormation.singleton_vendor_ids?.length > 0 &&
          ` (${groupFormation.singleton_vendor_ids.length} eligible vendor(s) had no compatible pool-mate)`}
        .
      </p>
    );
  }

  return (
    <div className="candidate-groups-panel">
      <p className="text-small text-muted">
        {rows.length} candidate group(s) evaluated across {poolCount} compatibility pool(s).
      </p>

      <div className="candidate-group-row-list">
        {rows.map((entry) => (
          <CandidateGroupRow
            key={entry.decision.group_id}
            entry={entry}
            isSelected={selectedSet.has(entry.decision.group_id)}
            isExpanded={expandedIds.has(entry.decision.group_id)}
            onToggle={() => toggleRow(entry.decision.group_id)}
          />
        ))}
      </div>
    </div>
  );
}

export default CandidateGroupsPanel;
