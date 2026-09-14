"""
Data contracts for Phase 6C's candidate-group generation output.

Reuses, does not modify or duplicate, Phase 6A's existing CandidateGroup
contract (backend/models/contracts.py: group_id + members) -- that
contract is exactly what Phase 6A's decision_engine.evaluate_group already
consumes, so Phase 6C wraps it with traceability metadata rather than
inventing a competing "candidate group" shape (Phase 6C Step 13).

IMPORTANT: no field here represents a final decision. There is no
BUY_TOGETHER, no savings figure, no selected flag. A candidate group is a
structural possibility only (Phase 6C Step 16) -- that determination
belongs to Phase 6D (per-candidate evaluation via the unchanged
evaluate_group) and Phase 6E (final overlap-resolved selection).
"""

from dataclasses import dataclass, field
from typing import Tuple

from backend.models.contracts import CandidateGroup


@dataclass(frozen=True)
class CandidateGroupRecord:
    """One generated candidate group plus the traceability metadata Phase
    6C Step 14 requires: Candidate Group -> Source Pool -> Eligible
    Vendors -> Phase 6B. `candidate` is Phase 6A's own, unmodified
    CandidateGroup contract -- ready to be passed directly into
    evaluate_group in a later phase with no conversion step."""
    candidate: CandidateGroup
    commodity_id: str
    context_date: str
    source_pool_id: str
    pool_vendor_ids: Tuple[str, ...]  # every vendor_id in this candidate's source pool, sorted


@dataclass(frozen=True)
class PoolDiagnostic:
    """A non-blocking, explicit diagnostic about one connected-component
    pool's size and nominal candidate count (Phase 6C Step 11). Never
    used to truncate, drop, or silently limit candidate generation --
    only to surface computational cost honestly."""
    pool_id: str
    vendor_count: int
    nominal_candidate_count: int  # 2^m - m - 1, per Phase 2B Part 5
    large_pool_warning: bool


@dataclass(frozen=True)
class GroupFormationResult:
    """The full output of Phase 6C for one procurement context.
    candidate_groups is in deterministic order (Phase 6C Step 12).
    singleton_vendor_ids lists eligible vendors with no compatible
    pool-mate at all -- a normal, expected outcome (Phase 2B Part 2),
    never an error."""
    commodity_id: str
    context_date: str
    pools: Tuple[Tuple[str, Tuple[str, ...]], ...]  # (pool_id, sorted vendor_ids) per pool with >=2 members
    candidate_groups: Tuple[CandidateGroupRecord, ...]
    singleton_vendor_ids: Tuple[str, ...]
    diagnostics: Tuple[PoolDiagnostic, ...] = field(default_factory=tuple)
