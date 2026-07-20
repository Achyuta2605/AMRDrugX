from fastapi import APIRouter

from app.schemas.bindingdb_evaluation import (
    BindingDBEvaluationRequest,
    BindingDBEvaluationResponse,
)
from app.services.bindingdb_evaluation_service import prepare_bindingdb_evaluation


router = APIRouter(prefix="/api/evaluation/bindingdb", tags=["bindingdb-evaluation"])


@router.post("/prepare", response_model=BindingDBEvaluationResponse)
def prepare_bindingdb_candidates(
    request: BindingDBEvaluationRequest,
) -> BindingDBEvaluationResponse:
    return prepare_bindingdb_evaluation(request)