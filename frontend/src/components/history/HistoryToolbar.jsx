// UI-6 -- Section 3+4: search + decision filter, kept as one compact
// component since they are always shown together as a single toolbar row.
// First real adoption of UI-1's `Input`/`Select` primitives
// (components/ui/), which existed but were deliberately left unused by
// every phase since ("a future page adopting this component looks like
// part of the same product, not a second visual language" -- Input.jsx's
// own comment) -- reusing them here rather than a third bespoke styled
// input/select.

import Button from "../common/Button";
import Input from "../ui/Input";
import Select from "../ui/Select";
import { DECISION_FILTER_OPTIONS } from "./historyFilters";

function HistoryToolbar({ searchQuery, onSearchChange, decisionFilter, onDecisionFilterChange, onClear, hasActiveFilters }) {
  return (
    <div className="history-toolbar">
      <div className="history-toolbar-field">
        <label htmlFor="history-search" className="sr-only">
          Search procurement runs
        </label>
        <Input
          id="history-search"
          type="search"
          placeholder="Search by commodity, run ID, or vendor ID…"
          value={searchQuery}
          onChange={(event) => onSearchChange(event.target.value)}
        />
      </div>

      <div className="history-toolbar-field">
        <label htmlFor="history-decision-filter" className="sr-only">
          Filter by decision
        </label>
        <Select
          id="history-decision-filter"
          value={decisionFilter}
          onChange={(event) => onDecisionFilterChange(event.target.value)}
        >
          {DECISION_FILTER_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      {hasActiveFilters && (
        <Button type="button" variant="ghost" onClick={onClear}>
          Clear Filters
        </Button>
      )}
    </div>
  );
}

export default HistoryToolbar;
