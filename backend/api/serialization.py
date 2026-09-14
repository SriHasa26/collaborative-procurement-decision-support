"""
Phase 6F -- JSON serialization boundary.

The project's internal contracts (backend/models/*) are plain Python
dataclasses, some frozen, some not, holding Enums, tuples, and nested
dataclasses -- none of that is JSON-safe on its own. Rather than hand-write
a parallel Pydantic response schema mirroring every one of the ~15 nested
dataclass shapes already defined across Phase 6A-6E (ProcurementRunResult,
BatchEligibilityResult, VendorEligibilityResult, GroupFormationResult,
CandidateGroupRecord, PoolDiagnostic, FinalSelectionResult,
EvaluatedGroupResult, GroupDecisionResult, PerVendorAllocation, ...) --
which would itself be a duplicate, competing definition of shapes Phase
6A-6E already own -- this module provides ONE small, generic, structural
converter that walks any of those objects and produces a plain,
JSON-serializable Python structure. No field is renamed, dropped, or
reinterpreted; only the TYPE each value is represented as changes:

    Enum            -> its .value (a string)
    dataclass       -> a dict keyed by field name (recursively converted)
    tuple / list    -> a list (recursively converted)
    set / frozenset -> a sorted list where the elements are orderable
                        (recursively converted); this project's contracts
                        do not currently store raw sets in any field, but
                        the converter handles them defensively per Phase
                        6F's own serialization requirement
    None / str / int / float / bool -> unchanged

This is intentionally the ONLY place in Phase 6F that touches the shape of
a result object -- the route handlers never inspect or reshape a result
themselves.
"""

import dataclasses
from enum import Enum
from typing import Any


def to_json_safe(value: Any) -> Any:
    """Recursively convert a dataclass/Enum/tuple/set tree (as produced by
    ProcurementRunService.run) into plain dicts/lists/primitives, safe to
    return directly as a FastAPI JSON response."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Enum):
        return value.value

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_json_safe(getattr(value, f.name)) for f in dataclasses.fields(value)}

    if isinstance(value, dict):
        return {str(k): to_json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_json_safe(v) for v in value]

    if isinstance(value, (set, frozenset)):
        try:
            ordered = sorted(value)
        except TypeError:
            ordered = list(value)  # non-orderable elements -- best effort, no order claimed
        return [to_json_safe(v) for v in ordered]

    raise TypeError(f"to_json_safe: unsupported type {type(value)!r} for value {value!r}")
