from uuid import uuid4

from app.schemas.molecule_screening import (
    VirtualScreeningRequest,
    VirtualScreeningResponse,
)
from app.services.dti_scoring_service import score_molecules_against_target
from app.services.screening_job_store import get_screening_job_store

SAFETY_NOTE = (
    "Virtual screening scores are computational estimates only. They are not "
    "evidence of efficacy or safety. Docking, ADMET analysis, literature review, "
    "and experimental validation are required."
)

NEXT_PIPELINE_STEP = "molecular_filtering_or_docking"


def build_empty_response(
    job_id: str,
    request: VirtualScreeningRequest,
    storage_backend: str,
    input_location: str,
    output_location: str,
    model_backend: str,
) -> VirtualScreeningResponse:
    return VirtualScreeningResponse(
        job_id=job_id,
        storage_backend=storage_backend,
        input_location=input_location,
        output_location=output_location,
        target_protein=request.target_protein,
        gene=request.gene,
        organism=request.organism,
        uniprot_accession=request.uniprot_accession,
        total_candidates_screened=0,
        ranked_candidates=[],
        model_backend=model_backend,
        next_pipeline_step=NEXT_PIPELINE_STEP,
        safety_note=SAFETY_NOTE,
    )


def run_virtual_screening(
    request: VirtualScreeningRequest,
) -> VirtualScreeningResponse:
    job_id = str(uuid4())
    store = get_screening_job_store()

    input_payload = request.model_dump()
    input_location = store.save_input(job_id, input_payload)

    output_location = ""

    if not request.protein_sequence.strip():
        response = build_empty_response(
            job_id=job_id,
            request=request,
            storage_backend=store.backend_name,
            input_location=input_location,
            output_location=output_location,
            model_backend="baseline_local",
        )
        output_location = store.save_output(job_id, response.model_dump())
        response.output_location = output_location
        return response

    if not request.candidates:
        response = build_empty_response(
            job_id=job_id,
            request=request,
            storage_backend=store.backend_name,
            input_location=input_location,
            output_location=output_location,
            model_backend="baseline_local",
        )
        output_location = store.save_output(job_id, response.model_dump())
        response.output_location = output_location
        return response

    scored_candidates, model_backend = score_molecules_against_target(
        protein_sequence=request.protein_sequence,
        candidates=request.candidates,
    )

    ranked_candidates = sorted(
        scored_candidates,
        key=lambda candidate: candidate.dti_score,
        reverse=True,
    )

    for index, candidate in enumerate(ranked_candidates, start=1):
        candidate.rank = index

    response = VirtualScreeningResponse(
        job_id=job_id,
        storage_backend=store.backend_name,
        input_location=input_location,
        output_location=output_location,
        target_protein=request.target_protein,
        gene=request.gene,
        organism=request.organism,
        uniprot_accession=request.uniprot_accession,
        total_candidates_screened=len(request.candidates),
        ranked_candidates=ranked_candidates,
        model_backend=model_backend,
        next_pipeline_step=NEXT_PIPELINE_STEP,
        safety_note=SAFETY_NOTE,
    )

    output_location = store.save_output(job_id, response.model_dump())
    response.output_location = output_location

    return response