// Phase 7B -- compact pill form of a decision state, for future inline use
// (e.g. next to a group ID in a results table, Phase 7E). Not used to
// display any real data in this phase -- Phase 7B does not connect to the
// API.

import Badge from "./Badge";
import { DECISION_STATE_META } from "./decisionStateMeta";

function DecisionStateBadge({ state }) {
  const meta = DECISION_STATE_META[state];

  if (!meta) {
    // Fails visibly rather than silently rendering nothing for an
    // unrecognized value -- never invents a fifth decision state.
    return <Badge variant="neutral">Unknown state: {String(state)}</Badge>;
  }

  return (
    <Badge variant={meta.variant} icon={meta.icon}>
      {meta.label}
    </Badge>
  );
}

export default DecisionStateBadge;
