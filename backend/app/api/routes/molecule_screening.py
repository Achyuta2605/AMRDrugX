from fastapi import APIRouter, HTTPException

from app.schemas.molecule_screening import (
    ScreeningJobResultResponse,
    MoleculeCandidate,
    VirtualScreeningRequest,
    VirtualScreeningResponse,
)
from app.services.molecule_candidate_service import get_candidates_for_target
from app.services.virtual_screening_service import (
    get_screening_job_result,
    run_virtual_screening,
)

router = APIRouter(prefix="/molecules", tags=["molecules"])


@router.post("/screen", response_model=VirtualScreeningResponse)
def screen_molecules(
    request: VirtualScreeningRequest,
) -> VirtualScreeningResponse:
    try:
        return run_virtual_screening(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    
@router.get(
    "/screen/{job_id}/result",
    response_model=ScreeningJobResultResponse,
)
def get_virtual_screening_result(job_id: str) -> ScreeningJobResultResponse:
    return get_screening_job_result(job_id)


@router.get("/candidates/beta-lactamase", response_model=list[MoleculeCandidate])
def get_beta_lactamase_candidates() -> list[MoleculeCandidate]:
    return get_candidates_for_target(
        target_protein="beta-lactamase",
        target_family="class A beta-lactamase",
    )