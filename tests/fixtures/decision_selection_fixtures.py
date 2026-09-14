"""
Phase 6D fixtures: candidate-group decision evaluation, WAIT_OR_EXPAND_GROUP
superset resolution, and final overlap-resolved selection.

SIMULATED ILLUSTRATIVE FIXTURE DATA -- every value below is invented for
testing only and does not represent a real vendor.

REUSE, NOT DUPLICATION: the V1/V2/V3/V4/V7 vendors and their COMMODITY/
CONTEXT/CONFIG are Phase 5E Section 15's own worked example, already
verified and regression-tested in
tests/unit/test_decision_engine_regression.py (see that file's header for
the coordinate-conversion note). This module imports them rather than
re-deriving new geography, because that scenario already exhibits exactly
the structural relationships Phase 6D needs to test:
  - G_all = {V1,V2,V3,V4,V7} evaluates to BUY_TOGETHER
  - G1 = {V1,V2,V3,V4}, G2 = {V1,V2,V7}, G3 = {V3,V4} each evaluate to
    WAIT_OR_EXPAND_GROUP on their own, and each is a STRICT SUBSET of
    G_all -- i.e. G_all is a real, already-known resolving superset.
  - G4 = {V3,V7} evaluates to DO_NOT_BUY_TOGETHER outright.

New fixtures are added below only for structural scenarios that worked
example does not cover: a group that ABSTAINs (missing q_i), a pool too
small to contain any superset (T6's termination case), and hand-built
EvaluatedGroupResult instances for exercising the pure selection layer
(selection.py) without re-deriving new economics for every combination.
"""

from backend.models.contracts import (
    CandidateGroup,
    CommodityParams,
    ConfigParams,
    GroupDecisionResult,
    ProcurementContext,
    TaggedLocation,
    TaggedPrice,
    TransportTier,
    VendorInput,
)
from backend.models.decision_contracts import EvaluatedGroupResult
from backend.models.enums import DecisionState, PriceGeographicLevel, VendorLocationStatus
from backend.models.group_formation_contracts import CandidateGroupRecord
from tests.fixtures.group_formation_fixtures import V1, V2, V3, V4, V7

COMMODITY_ID = "potato"
CONTEXT_DATE = "2026-illustrative"

COMMODITY = CommodityParams(commodity_id=COMMODITY_ID, freshness_window_days=None, moq_kg=200.0)
CONTEXT = ProcurementContext(
    commodity_id=COMMODITY_ID,
    date=CONTEXT_DATE,
    wholesale_price=TaggedPrice(value_rs_per_kg=15.0, geographic_level=PriceGeographicLevel.MANDI_LEVEL),
)
CONFIG = ConfigParams(
    d_max_km=2.0,
    trader_margin=0.10,
    transport_tiers=(TransportTier(capacity_kg=100_000, cost_rs=800.0),),
)


def _record(candidate: CandidateGroup, pool_id: str, pool_vendor_ids) -> CandidateGroupRecord:
    return CandidateGroupRecord(
        candidate=candidate,
        commodity_id=COMMODITY_ID,
        context_date=CONTEXT_DATE,
        source_pool_id=pool_id,
        pool_vendor_ids=tuple(sorted(pool_vendor_ids)),
    )


# --- T1 / T5 / T4: shared pool reproducing Phase 5E Section 15's worked
# example in full -- G_all is BUY_TOGETHER; G1/G2/G3 are WAIT_OR_EXPAND_GROUP
# on their own and are each a strict subset of G_all (a real, already-
# generated resolving superset in the SAME pool). ---
FULL_POOL_ID = "pool:T1_T4_T5:V1+V2+V3+V4+V7"
FULL_POOL_VENDOR_IDS = ("V1", "V2", "V3", "V4", "V7")

G1 = CandidateGroup(group_id="G1", members=(V1, V2, V3, V4))
G2 = CandidateGroup(group_id="G2", members=(V1, V2, V7))
G3 = CandidateGroup(group_id="G3", members=(V3, V4))
G4 = CandidateGroup(group_id="G4", members=(V3, V7))
G_ALL = CandidateGroup(group_id="G_all", members=(V1, V2, V3, V4, V7))

RECORD_G1 = _record(G1, FULL_POOL_ID, FULL_POOL_VENDOR_IDS)
RECORD_G2 = _record(G2, FULL_POOL_ID, FULL_POOL_VENDOR_IDS)
RECORD_G3 = _record(G3, FULL_POOL_ID, FULL_POOL_VENDOR_IDS)
RECORD_G4 = _record(G4, FULL_POOL_ID, FULL_POOL_VENDOR_IDS)
RECORD_G_ALL = _record(G_ALL, FULL_POOL_ID, FULL_POOL_VENDOR_IDS)

# All five candidates as Phase 6C would have generated them for one pool
# (a strict subset of the pool's full 2^5 - 5 - 1 = 26 nominal candidates --
# only the ones this scenario's assertions need are listed explicitly;
# resolve_wait_or_expand only ever needs same-pool candidates to be present
# in the list passed to it, not a complete enumeration).
FULL_POOL_RECORDS = (RECORD_G1, RECORD_G2, RECORD_G3, RECORD_G4, RECORD_G_ALL)


# --- T2: DO_NOT_BUY_TOGETHER outright, in its own single-candidate pool ---
POOL_T2_ID = "pool:T2:V3+V7"
RECORD_T2_DO_NOT_BUY = _record(G4, POOL_T2_ID, ("V3", "V7"))


# --- T3: ABSTAIN -- one member has no demand estimate (q_i=None) ---
ABSTAIN_VENDOR = VendorInput(
    vendor_id="ABSTAIN_V",
    location=TaggedLocation(status=VendorLocationStatus.VENDOR_SPECIFIC_APPROXIMATE, lat=17.45, lon=78.47),
    q_i=None,
    estimation_provenance=None,
    individual_price_rs_per_kg=20.0,
    practical_horizon_days=5,
)
POOL_T3_ID = "pool:T3:ABSTAIN_V+V1"
G_ABSTAIN = CandidateGroup(group_id="G_abstain", members=(ABSTAIN_VENDOR, V1))
RECORD_T3_ABSTAIN = _record(G_ABSTAIN, POOL_T3_ID, ("ABSTAIN_V", "V1"))


# --- T6: WAIT_OR_EXPAND_GROUP with NO possible superset -- the pool has
# only the 2 vendors that make up the group itself, so no larger candidate
# can exist in this pool at all (Phase 5E Section 12 termination case). ---
POOL_T6_ID = "pool:T6:V3+V4"
RECORD_T6_NO_SUPERSET = _record(G3, POOL_T6_ID, ("V3", "V4"))


# ============================================================================
# Hand-built EvaluatedGroupResult fixtures for the pure selection layer
# (selection.py). These bypass evaluate_group entirely -- selection.py only
# ever reads .decision.group_id, .decision.savings_rs, .vendor_ids, and
# .final_decision_state, so a minimal GroupDecisionResult with just those
# fields populated is a faithful, non-fabricated test double for THIS
# layer's contract (it is never passed back into decision_engine or
# presented as a real economic outcome).
# ============================================================================

def make_result(group_id, state, savings_rs, vendor_ids, pool_id="pool:selection-fixture"):
    decision = GroupDecisionResult(
        group_id=group_id,
        decision_state=state,
        reason=f"fixture: {group_id} fixed at {state} for selection-layer testing",
        savings_rs=savings_rs,
    )
    sorted_ids = tuple(sorted(vendor_ids))
    return EvaluatedGroupResult(
        decision=decision,
        final_decision_state=state,
        commodity_id=COMMODITY_ID,
        context_date=CONTEXT_DATE,
        source_pool_id=pool_id,
        pool_vendor_ids=sorted_ids,
        vendor_ids=sorted_ids,
    )


def make_buy_together(group_id, savings_rs, vendor_ids, pool_id="pool:selection-fixture"):
    return make_result(group_id, DecisionState.BUY_TOGETHER.value, savings_rs, vendor_ids, pool_id)


def make_wait_or_expand(group_id, savings_rs, vendor_ids, pool_id="pool:selection-fixture"):
    return make_result(group_id, DecisionState.WAIT_OR_EXPAND_GROUP.value, savings_rs, vendor_ids, pool_id)


def make_do_not_buy(group_id, vendor_ids, pool_id="pool:selection-fixture"):
    return make_result(group_id, DecisionState.DO_NOT_BUY_TOGETHER.value, -10.0, vendor_ids, pool_id)


def make_abstain(group_id, vendor_ids, pool_id="pool:selection-fixture"):
    decision = GroupDecisionResult(
        group_id=group_id,
        decision_state=DecisionState.ABSTAIN.value,
        reason=f"fixture: {group_id} fixed at ABSTAIN for selection-layer testing",
    )
    sorted_ids = tuple(sorted(vendor_ids))
    return EvaluatedGroupResult(
        decision=decision,
        final_decision_state=DecisionState.ABSTAIN.value,
        commodity_id=COMMODITY_ID,
        context_date=CONTEXT_DATE,
        source_pool_id=pool_id,
        pool_vendor_ids=sorted_ids,
        vendor_ids=sorted_ids,
    )
