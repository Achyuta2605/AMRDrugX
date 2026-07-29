from uuid import uuid4

from fastapi import APIRouter

from app.schemas.binding_site_schemas import (
    BindingSitePredictionRequest,
    BindingSitePredictionResult,
    BindingSitePredictionResultResponse,
    BindingSitePredictionSubmitResponse,
)
from app.services.binding_site_job_store import (
    binding_site_output_exists,
    build_binding_site_input_key,
    build_binding_site_output_key,
    get_binding_site_output,
    save_binding_site_input,
)
from app.services.binding_site_task_launcher import start_binding_site_fargate_task


router = APIRouter(prefix="/api/binding-sites", tags=["binding-sites"])

SAFETY_NOTE = (
    "Binding-site prediction is computational only. It is not experimental "
    "validation and is not a medical or therapeutic claim."
)


@router.post("/predict", response_model=BindingSitePredictionSubmitResponse)
def submit_binding_site_prediction(
    request: BindingSitePredictionRequest,
) -> BindingSitePredictionSubmitResponse:
    job_id = request.job_id or str(uuid4())
    input_key = build_binding_site_input_key(job_id)
    output_key = build_binding_site_output_key(job_id)

    input_payload = request.model_dump()
    input_payload["job_id"] = job_id
    input_payload["binding_site_backend"] = "p2rank"

    save_binding_site_input(job_id=job_id, payload=input_payload)

    task = start_binding_site_fargate_task(
        job_id=job_id,
        input_key=input_key,
        output_key=output_key,
    )

    return BindingSitePredictionSubmitResponse(
        job_id=job_id,
        status="submitted",
        binding_site_backend="p2rank",
        input_s3_key=input_key,
        output_s3_key=output_key,
        task_arn=task["task_arn"],
        message="Binding-site prediction job submitted to AWS Fargate.",
        safety_note=SAFETY_NOTE,
    )


@router.get(
    "/{job_id}/result",
    response_model=BindingSitePredictionResultResponse,
)
def get_binding_site_prediction_result(
    job_id: str,
) -> BindingSitePredictionResultResponse:
    output_key = build_binding_site_output_key(job_id)

    if not binding_site_output_exists(job_id):
        return BindingSitePredictionResultResponse(
            job_id=job_id,
            status="not_ready",
            output_s3_key=output_key,
            result=None,
            safety_note=SAFETY_NOTE,
        )

    output_payload = get_binding_site_output(job_id)

    result = BindingSitePredictionResult(
        job_id=output_payload["job_id"],
        target_name=output_payload["target_name"],
        target_uniprot_accession=output_payload["target_uniprot_accession"],
        receptor_pdb_s3_key=output_payload["receptor_pdb_s3_key"],
        binding_site_backend=output_payload["binding_site_backend"],
        status=output_payload["status"],
        top_pocket=output_payload["top_pocket"],
        recommended_box_center=output_payload["recommended_box_center"],
        recommended_box_size=output_payload["recommended_box_size"],
        next_pipeline_step=output_payload["next_pipeline_step"],
        limitation_note=output_payload["limitation_note"],
    )

    return BindingSitePredictionResultResponse(
        job_id=job_id,
        status="completed",
        output_s3_key=output_key,
        result=result,
        safety_note=SAFETY_NOTE,
    )