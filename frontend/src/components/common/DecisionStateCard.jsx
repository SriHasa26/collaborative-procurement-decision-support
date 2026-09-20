// Phase 7B -- larger, explanatory presentation of one decision state, used
// on the Home page's "Decision transparency" section. Meaning is carried
// by the label + description text, never by color/icon alone.

import Card from "./Card";
import DecisionStateBadge from "./DecisionStateBadge";
import { DECISION_STATE_META } from "./decisionStateMeta";

function DecisionStateCard({ state }) {
  const meta = DECISION_STATE_META[state];
  if (!meta) return null;

  return (
    <Card className="decision-card">
      <DecisionStateBadge state={state} />
      <span className="decision-card-summary">{meta.summary}</span>
      <p className="text-small">{meta.description}</p>
    </Card>
  );
}

export default DecisionStateCard;
