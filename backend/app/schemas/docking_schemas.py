from typing import Optional

from pydantic import BaseModel


class DockingBoxCenter(BaseModel):
    x: float
    y: float
    z: float


class DockingBoxSize(BaseModel):
    x: float
    y: float
    z: float


class DockingJobRequest(BaseModel):
    job_id: Optional[str] = None
    target_name: str
    target_uniprot_accession: str
    receptor_pdb_s3_key: str
    ligand_name: str
    bindingdb_monomer_id: Optional[str] = None
    ligand_sdf_s3_key: str
    box_center: DockingBoxCenter
    box_size: DockingBoxSize


class DockingJobSubmitResponse(BaseModel):
    job_id: str
    status: str
    docking_backend: str
    input_s3_key: str
    output_s3_key: str
    task_arn: Optional[str] = None
    message: str
    safety_note: str


class DockingJobResult(BaseModel):
    job_id: str
    target_name: str
    target_uniprot_accession: str
    ligand_name: str
    bindingdb_monomer_id: Optional[str] = None
    docking_backend: str
    docking_status: str
    docking_score: Optional[float] = None
    cnn_score: Optional[float] = None
    cnn_affinity: Optional[float] = None
    receptor_pdb_s3_key: str
    ligand_sdf_s3_key: str
    docked_pose_sdf_s3_key: Optional[str] = None
    viewer_url: Optional[str] = None
    limitation_note: str


class DockingJobResultResponse(BaseModel):
    job_id: str
    status: str
    output_s3_key: str
    result: Optional[DockingJobResult] = None
    safety_note: str