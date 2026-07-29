from typing import Optional

from pydantic import BaseModel


class BindingSiteBoxCenter(BaseModel):
    x: float
    y: float
    z: float


class BindingSiteBoxSize(BaseModel):
    x: float
    y: float
    z: float


class BindingSitePredictionRequest(BaseModel):
    job_id: Optional[str] = None
    target_name: str
    target_uniprot_accession: str
    receptor_pdb_s3_key: str


class BindingSitePredictionSubmitResponse(BaseModel):
    job_id: str
    status: str
    binding_site_backend: str
    input_s3_key: str
    output_s3_key: str
    task_arn: Optional[str] = None
    message: str
    safety_note: str


class BindingSitePocket(BaseModel):
    rank: int
    score: Optional[float] = None
    probability: Optional[float] = None
    center: BindingSiteBoxCenter


class BindingSitePredictionResult(BaseModel):
    job_id: str
    target_name: str
    target_uniprot_accession: str
    receptor_pdb_s3_key: str
    binding_site_backend: str
    status: str
    top_pocket: BindingSitePocket
    recommended_box_center: BindingSiteBoxCenter
    recommended_box_size: BindingSiteBoxSize
    next_pipeline_step: str
    limitation_note: str


class BindingSitePredictionResultResponse(BaseModel):
    job_id: str
    status: str
    output_s3_key: str
    result: Optional[BindingSitePredictionResult] = None
    safety_note: str