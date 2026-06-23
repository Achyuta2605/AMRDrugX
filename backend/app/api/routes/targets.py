from fastapi import APIRouter

from app.schemas.target import TargetResolveRequest, TargetResolveResponse
from app.services.target_resolver import resolve_target

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post("/resolve", response_model=TargetResolveResponse)
def resolve_resistance_target(
    request: TargetResolveRequest,
) -> TargetResolveResponse:
    return resolve_target(request)