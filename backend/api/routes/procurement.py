"""
Phase 6F -- /procurement/analyze route.
Phase 6G -- persistence of each analysis, plus /procurement/runs and
/procurement/runs/{run_id} for retrieval.

Every handler below is intentionally thin: parse (FastAPI/Pydantic already
did this before the function body runs) -> convert to the existing domain
input contract -> call the Phase 6E public orchestration entry point
exactly once -> (Phase 6G) persist the already-computed result -> serialize
the response. No validation, eligibility, compatibility, group-formation,
decision-evaluation, selection, or SQL-embedded business rule appears here
or anywhere else in backend/api/ or backend/persistence/.

PERSISTENCE ORDERING (Phase 6G's own explicit requirement): the run is
persisted AFTER ProcurementRunService.run() has already produced its
result, and the persisted content is never allowed to change what is
returned to the caller -- the response below is built from the same
`result` object that was (already, separately) written to the database,
not re-read back from it.

Phase 8D -- authentication: all three routes below now additionally
require `current_user: AuthenticatedUser = Depends(get_current_user)`
(backend/security/auth.py). This proves the caller holds a valid,
cryptographically-verified Supabase access token; FastAPI rejects the
request with HTTP 401 before the handler body runs at all if not.

Phase 8F -- ownership: `current_user.user_id` (never anything from the
request body -- ProcurementAnalysisRequest has no user_id field) is now
passed explicitly into every repository call. Ownership enforcement lives
entirely inside the repository implementations' own SQL (`WHERE user_id =
...`, backend/persistence/{sqlite,supabase}_repository.py) -- these
handlers do no filtering of their own; they only thread the verified
identity through. No global or thread-local "current user" state is used
anywhere -- `current_user` is an ordinary function-local dependency
result, passed as a plain argument."""

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_repository
from backend.api.schemas import ProcurementAnalysisRequest, build_run_input
from backend.api.serialization import to_json_safe
from backend.persistence.repository import ProcurementRunRepository
from backend.security.auth import AuthenticatedUser, get_current_user
from backend.services.procurement_run import ProcurementRunService

router = APIRouter(prefix="/procurement", tags=["procurement"])


@router.post("/analyze", summary="Run one collaborative procurement analysis")
def analyze_procurement(
    payload: ProcurementAnalysisRequest,
    repository: ProcurementRunRepository = Depends(get_repository),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Runs the full Phase 6B -> 6C -> 6D pipeline, via Phase 6E's
    ProcurementRunService, for one (commodity, context, vendor universe),
    then persists the input/result (Phase 6G). Always returns HTTP 200 for
    a structurally valid request -- abstained vendors, validation-error
    vendors, zero eligible vendors, zero candidate groups, and zero
    selected groups are all valid analytical outcomes, not API errors
    (Phase 6F Section 11) -- and persistence never changes that outcome.
    Requires authentication (Phase 8D); the run is saved as owned by
    current_user.user_id (Phase 8F) -- never by any value in `payload`."""
    run_input = build_run_input(payload)
    result = ProcurementRunService().run(run_input)
    repository.save_run(current_user.user_id, run_input, result)
    return to_json_safe(result)


@router.get("/runs", summary="List previous procurement runs (newest first)")
def list_runs(
    repository: ProcurementRunRepository = Depends(get_repository),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list:
    """Lightweight run history only -- run_id/created_at/commodity/
    run_status per row, never the full stored input/result JSON. Requires
    authentication (Phase 8D) and returns only current_user.user_id's own
    runs (Phase 8F) -- filtering happens inside the repository's own
    query, not in this handler."""
    return [to_json_safe(summary) for summary in repository.list_runs(current_user.user_id)]


@router.get("/runs/{run_id}", summary="Retrieve one stored procurement run")
def get_run(
    run_id: str,
    repository: ProcurementRunRepository = Depends(get_repository),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Returns the exact input/result that were persisted for this run,
    but ONLY if it belongs to current_user.user_id (Phase 8F). A 404 is
    raised both for a genuinely unknown run_id AND for a run that exists
    but belongs to a different user -- these two cases are deliberately
    indistinguishable to the caller (repository.get_run's own contract),
    so this endpoint never confirms or denies that another user's run_id
    exists (IDOR/information-leakage avoidance, per
    reports/phase8a_architecture_decision_record.md). Never a raw SQLite
    error, and never a fabricated/empty result."""
    stored = repository.get_run(current_user.user_id, run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"procurement run not found: {run_id}")
    return {
        "run_id": stored.run_id,
        "created_at": stored.created_at,
        "commodity": stored.commodity,
        "run_status": stored.run_status,
        "input": stored.input,
        "result": stored.result,
    }
