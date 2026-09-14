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
not re-read back from it."""

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_repository
from backend.api.schemas import ProcurementAnalysisRequest, build_run_input
from backend.api.serialization import to_json_safe
from backend.persistence.repository import ProcurementRunRepository
from backend.services.procurement_run import ProcurementRunService

router = APIRouter(prefix="/procurement", tags=["procurement"])


@router.post("/analyze", summary="Run one collaborative procurement analysis")
def analyze_procurement(
    payload: ProcurementAnalysisRequest,
    repository: ProcurementRunRepository = Depends(get_repository),
) -> dict:
    """Runs the full Phase 6B -> 6C -> 6D pipeline, via Phase 6E's
    ProcurementRunService, for one (commodity, context, vendor universe),
    then persists the input/result (Phase 6G). Always returns HTTP 200 for
    a structurally valid request -- abstained vendors, validation-error
    vendors, zero eligible vendors, zero candidate groups, and zero
    selected groups are all valid analytical outcomes, not API errors
    (Phase 6F Section 11) -- and persistence never changes that outcome."""
    run_input = build_run_input(payload)
    result = ProcurementRunService().run(run_input)
    repository.save_run(run_input, result)
    return to_json_safe(result)


@router.get("/runs", summary="List previous procurement runs (newest first)")
def list_runs(repository: ProcurementRunRepository = Depends(get_repository)) -> list:
    """Lightweight run history only -- run_id/created_at/commodity/
    run_status per row, never the full stored input/result JSON."""
    return [to_json_safe(summary) for summary in repository.list_runs()]


@router.get("/runs/{run_id}", summary="Retrieve one stored procurement run")
def get_run(run_id: str, repository: ProcurementRunRepository = Depends(get_repository)) -> dict:
    """Returns the exact input/result that were persisted for this run.
    A 404 is raised for an unknown run_id -- never a raw SQLite error, and
    never a fabricated/empty result."""
    stored = repository.get_run(run_id)
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
