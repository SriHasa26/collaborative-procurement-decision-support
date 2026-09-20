// Phase 7B -- the single source of truth for how the backend's four
// DecisionState values (backend/models/enums.py) are presented visually.
// Reused by DecisionStateBadge and DecisionStateCard so the mapping is
// never duplicated.
//
// IMPORTANT (per this phase's explicit instruction): ABSTAIN uses the
// neutral "info" variant, never "danger" -- ABSTAIN means the system
// lacks sufficient evidence, which is NOT an application error and must
// never look like one. A real application/network error uses the
// separate ErrorState component instead, which is visually and
// semantically distinct from every one of these four cards.

export const DECISION_STATE_META = {
  BUY_TOGETHER: {
    label: "Buy Together",
    variant: "success",
    icon: "✓",
    summary: "Recommended",
    description:
      "The evaluated evidence supports collaborative procurement for this group.",
  },
  WAIT_OR_EXPAND_GROUP: {
    label: "Wait / Expand Group",
    variant: "warning",
    icon: "⏳",
    summary: "Conditional",
    description:
      "This group is not yet feasible on its own, but waiting or expanding the group may make it feasible.",
  },
  DO_NOT_BUY_TOGETHER: {
    label: "Do Not Buy Together",
    variant: "danger",
    icon: "✕",
    summary: "Not recommended",
    description:
      "The evaluated evidence does not currently support collaborative procurement for this group.",
  },
  ABSTAIN: {
    label: "Abstain",
    variant: "info",
    icon: "?",
    summary: "Insufficient evidence",
    description:
      "The system does not yet have enough verified information to make a recommendation. This is not an error.",
  },
};

export const DECISION_STATE_ORDER = [
  "BUY_TOGETHER",
  "WAIT_OR_EXPAND_GROUP",
  "DO_NOT_BUY_TOGETHER",
  "ABSTAIN",
];
