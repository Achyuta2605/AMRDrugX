from fastapi import APIRouter

from app.schemas.workflow_schemas import (
    AMRWorkflowRequest,
    AMRWorkflowResponse,
)
from app.services.amr_workflow_service import prepare_amr_workflow


router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post("/amr", response_model=AMRWorkflowResponse)
def prepare_amr_workflow_endpoint(
    request: AMRWorkflowRequest,
) -> AMRWorkflowResponse:
    return prepare_amr_workflow(request)