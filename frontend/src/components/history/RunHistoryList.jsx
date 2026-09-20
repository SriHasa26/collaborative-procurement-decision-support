// UI-6 -- Section 6 + 15: renders the (already search/filter-applied)
// run list, or the distinct "no matches" empty state when the user HAS
// runs but the current search/filter combination matches none of them --
// never confused with "no runs exist at all" (HistoryPage.jsx's own,
// separate EmptyState handles that case, before this component is even
// rendered).

import Button from "../common/Button";
import EmptyState from "../common/EmptyState";
import RunHistoryRow from "./RunHistoryRow";

function RunHistoryList({ entries, onViewResults, pendingRunId, isSelecting, onClearFilters }) {
  if (entries.length === 0) {
    return (
      <EmptyState
        icon="⌕"
        title="No matching procurement runs"
        description="Try a different search term or a different decision filter."
        actions={
          <Button type="button" variant="secondary" onClick={onClearFilters}>
            Clear Filters
          </Button>
        }
      />
    );
  }

  return (
    <ul className="run-history-list">
      {entries.map((entry) => (
        <RunHistoryRow
          key={entry.run_id}
          entry={entry}
          onViewResults={onViewResults}
          isPending={isSelecting && pendingRunId === entry.run_id}
          isDisabled={isSelecting}
        />
      ))}
    </ul>
  );
}

export default RunHistoryList;
