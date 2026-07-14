from fastapi import APIRouter

from app.schemas.candidate_retrieval import (
    CandidateRetrievalRequest,
    CandidateRetrievalResponse,
)
from app.services.candidate_retrieval_service import retrieve_candidates_for_target


router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.post("/retrieve", response_model=CandidateRetrievalResponse)
def retrieve_candidates(
    request: CandidateRetrievalRequest,
) -> CandidateRetrievalResponse:
    return retrieve_candidates_for_target(request)