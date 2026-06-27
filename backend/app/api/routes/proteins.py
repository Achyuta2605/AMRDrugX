from fastapi import APIRouter

from app.schemas.protein import ProteinEnrichmentRequest, ProteinEnrichmentResponse
from app.services.protein_enrichment_service import enrich_protein

router = APIRouter(prefix="/proteins", tags=["proteins"])


@router.post("/enrich", response_model=ProteinEnrichmentResponse)
def enrich_resistance_protein(
    request: ProteinEnrichmentRequest,
) -> ProteinEnrichmentResponse:
    return enrich_protein(request)