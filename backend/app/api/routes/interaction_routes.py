from uuid import uuid4

from fastapi import APIRouter

from app.schemas.interaction_schemas import (
    InteractionAnalysisRequest,
    InteractionAnalysisResult,
    InteractionAnalysisResultResponse,
    InteractionAnalysisSubmitResponse,
)
from app.services.interaction_job_store import (
    build_interaction_input_key,
    build_interaction_output_key,
    get_interaction_output,
    interaction_output_exists,
    save_interaction_input,
)
from app.services.interaction_task_launcher import start_interaction_fargate_task


router = APIRouter(prefix="/api/interactions", tags=["interactions"])

SAFETY_NOTE = (
    "Protein-ligand interaction analysis is computational only. It is not "
    "experimental validation and is not a medical or therapeutic claim."
)


@router.post("/analyze", response_model=InteractionAnalysisSubmitResponse)
def submit_interaction_analysis(
    request: InteractionAnalysisRequest,
) -> InteractionAnalysisSubmitResponse:
    job_id = request.job_id or str(uuid4())
    input_key = build_interaction_input_key(job_id)
    output_key = build_interaction_output_key(job_id)

    input_payload = request.model_dump()
    input_payload["job_id"] = job_id
    input_payload["interaction_backend"] = "plip"
    input_payload["complex_file_s3_key"] = (
        f"interaction_jobs/{job_id}/output/complex.pdb"
    )

    save_interaction_input(job_id=job_id, payload=input_payload)

    task = start_interaction_fargate_task(
        job_id=job_id,
        input_key=input_key,
        output_key=output_key,
    )

    return InteractionAnalysisSubmitResponse(
        job_id=job_id,
        status="submitted",
        interaction_backend="plip",
        input_s3_key=input_key,
        output_s3_key=output_key,
        task_arn=task["task_arn"],
        message="Interaction analysis job submitted to AWS Fargate.",
        safety_note=SAFETY_NOTE,
    )


@router.get(
    "/{job_id}/result",
    response_model=InteractionAnalysisResultResponse,
)
def get_interaction_analysis_result(
    job_id: str,
) -> InteractionAnalysisResultResponse:
    output_key = build_interaction_output_key(job_id)

    if not interaction_output_exists(job_id):
        return InteractionAnalysisResultResponse(
            job_id=job_id,
            status="not_ready",
            output_s3_key=output_key,
            result=None,
            safety_note=SAFETY_NOTE,
        )

    output_payload = get_interaction_output(job_id)

    result = InteractionAnalysisResult(
        job_id=output_payload["job_id"],
        docking_job_id=output_payload["docking_job_id"],
        interaction_backend=output_payload["interaction_backend"],
        analysis_status=output_payload["analysis_status"],
        target_name=output_payload.get("target_name"),
        target_uniprot_accession=output_payload.get(
            "target_uniprot_accession"
        ),
        ligand_name=output_payload.get("ligand_name"),
        bindingdb_monomer_id=output_payload.get("bindingdb_monomer_id"),
        summary=output_payload["summary"],
        interactions=output_payload.get("interactions", []),
        parser_note=output_payload.get("parser_note"),
        error_message=output_payload.get("error_message"),
        source_files=output_payload["source_files"],
        limitation_note=output_payload["limitation_note"],
    )

    return InteractionAnalysisResultResponse(
        job_id=job_id,
        status=output_payload["analysis_status"],
        output_s3_key=output_key,
        result=result,
        safety_note=SAFETY_NOTE,
    )