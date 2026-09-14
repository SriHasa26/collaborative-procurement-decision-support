"""
Demand estimation service -- implements the authoritative hierarchy exactly
as specified, with no new algorithm invented.

Authoritative sources:
  - Hierarchy:        Phase 5C Sections 6-7; Phase 5D Section 3
  - Deterministic tie-break for the "limited history" tier (>=3 records ->
    moving-average-3, else last-observed-value): Phase 5G Section 3 -- this
    is a choice between two ALREADY-listed candidate methods, not a new
    algorithm.
  - ABSTAIN vs VALIDATION_ERROR distinction: Phase 5F Module Interfaces
    Section 4; Phase 5G Section 7.

ML (EstimationProvenance.ESTIMATE_ML) is a defined slot that this module
never produces -- Phase 5C Section 12's verdict is that ML is not
justified for this project's current data.
"""

from dataclasses import dataclass
from typing import Optional, Sequence

from backend.models.enums import EstimationProvenance, OutcomeKind


class ValidationError(Exception):
    """Raised for malformed/out-of-range submitted values (e.g. a negative
    quantity). Distinct from ABSTAIN, which represents a well-formed
    submission with genuinely insufficient evidence (Phase 5G Section 7)."""


@dataclass
class EstimationResult:
    """The outcome of a demand-estimation request. When outcome is ABSTAIN,
    q_i is None -- never a fabricated value (Phase 5E Section 4/13)."""
    outcome: str  # OutcomeKind value; OK or ABSTAIN (VALIDATION_ERROR is raised, not returned)
    q_i: Optional[float]
    provenance: Optional[EstimationProvenance]
    reason: str


MOVING_AVERAGE_WINDOW = 3  # Phase 5G Section 3's fixed tie-break, named here
                            # as a constant, not a hardcoded literal (Phase 6A Step 11 item 5)


def _validate_numeric_records(records: Sequence[float], label: str) -> None:
    """Raises ValidationError for any negative value. This is the exact
    D4 case (Phase 5G): a malformed/out-of-range submission, caught before
    any estimation logic runs."""
    for value in records:
        if value < 0:
            raise ValidationError(
                f"{label} contains a negative value ({value}) -- invalid demand quantity."
            )


def cold_start_estimate(peer_q_values: Sequence[float]) -> EstimationResult:
    """CASE 1 (Phase 5G D1): no usable vendor history, same-category peer
    information exists -> same-category peer average.
    Authoritative source: Phase 5C Section 6."""
    _validate_numeric_records(peer_q_values, "peer_q_values")
    if not peer_q_values:
        return EstimationResult(
            outcome=OutcomeKind.ABSTAIN,
            q_i=None,
            provenance=None,
            reason="no demand estimate available -- no own history and no same-category peers exist.",
        )
    avg = sum(peer_q_values) / len(peer_q_values)
    return EstimationResult(
        outcome=OutcomeKind.OK,
        q_i=avg,
        provenance=EstimationProvenance.ESTIMATE_COLD_START,
        reason=f"same-category peer average over {len(peer_q_values)} peer(s).",
    )


def limited_history_estimate(diary_records: Sequence[float]) -> EstimationResult:
    """CASE 2 (Phase 5G D2): limited usable history -> moving-average-3 if
    >=3 usable records exist, else last-observed-value.
    Authoritative source: Phase 5C Section 7; Phase 5D Section 3;
    tie-break fixed in Phase 5G Section 3."""
    _validate_numeric_records(diary_records, "diary_records")
    if not diary_records:
        return EstimationResult(
            outcome=OutcomeKind.ABSTAIN,
            q_i=None,
            provenance=None,
            reason="no demand estimate available -- no diary records exist.",
        )
    if len(diary_records) >= MOVING_AVERAGE_WINDOW:
        window = diary_records[-MOVING_AVERAGE_WINDOW:]
        q_i = sum(window) / MOVING_AVERAGE_WINDOW
        reason = f"moving average over the last {MOVING_AVERAGE_WINDOW} records (Phase 5G tie-break)."
    else:
        q_i = diary_records[-1]
        reason = f"last-observed-value ({len(diary_records)} record(s), below the moving-average threshold)."
    return EstimationResult(
        outcome=OutcomeKind.OK,
        q_i=q_i,
        provenance=EstimationProvenance.ESTIMATE_BASELINE,
        reason=reason,
    )


def estimate_demand(
    diary_records: Optional[Sequence[float]],
    peer_q_values: Optional[Sequence[float]],
) -> EstimationResult:
    """Top-level entry point implementing the full hierarchy (Phase 5C
    Sections 6-7; Phase 5D Section 3; Phase 5E Section 13 for ABSTAIN):

        1. diary_records has >= 1 usable record -> limited_history_estimate
        2. else, peer_q_values has >= 1 usable value -> cold_start_estimate
        3. else -> ABSTAIN (CASE 3, Phase 5G D3)

    CASE 4 (invalid input, Phase 5G D4) is handled by _validate_numeric_records
    raising ValidationError -- callers must catch this separately from a
    normal EstimationResult; ValidationError is never converted into an
    ABSTAIN outcome."""
    diary_records = diary_records or []
    peer_q_values = peer_q_values or []

    _validate_numeric_records(diary_records, "diary_records")
    _validate_numeric_records(peer_q_values, "peer_q_values")

    if diary_records:
        return limited_history_estimate(diary_records)
    if peer_q_values:
        return cold_start_estimate(peer_q_values)
    return EstimationResult(
        outcome=OutcomeKind.ABSTAIN,
        q_i=None,
        provenance=None,
        reason="no demand estimate available -- no own history and no same-category peers exist.",
    )
