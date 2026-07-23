from fastapi import APIRouter

from app.schemas.bindingdb_evaluation import (
    BindingDBComparisonRequest,
    BindingDBEvaluationRequest,
    BindingDBEvaluationResponse,
)
from app.services.bindingdb_evaluation_service import (
    compare_bindingdb_with_deeppurpose_output,
    prepare_bindingdb_evaluation,
)


router = APIRouter(prefix="/api/evaluation/bindingdb", tags=["bindingdb-evaluation"])


@router.post("/prepare", response_model=BindingDBEvaluationResponse)
def prepare_bindingdb_candidates(
    request: BindingDBEvaluationRequest,
) -> BindingDBEvaluationResponse:
    return prepare_bindingdb_evaluation(request)


@router.post("/compare", response_model=BindingDBEvaluationResponse)
def compare_bindingdb_candidates(
    request: BindingDBComparisonRequest,
) -> BindingDBEvaluationResponse:
    return compare_bindingdb_with_deeppurpose_output(
        bindingdb_response=request.bindingdb_prepare_response,
        deeppurpose_output=request.deeppurpose_output,
    )