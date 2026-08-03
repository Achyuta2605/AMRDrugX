from typing import List, Optional

from pydantic import BaseModel


class InteractionAnalysisRequest(BaseModel):
    job_id: Optional[str] = None
    docking_job_id: str
    target_name: str
    target_uniprot_accession: str
    ligand_name: str
    bindingdb_monomer_id: Optional[str] = None
    receptor_pdb_s3_key: str
    docked_pose_s3_key: str


class InteractionAnalysisSubmitResponse(BaseModel):
    job_id: str
    status: str
    interaction_backend: str
    input_s3_key: str
    output_s3_key: str
    task_arn: Optional[str] = None
    message: str
    safety_note: str


class InteractionSummary(BaseModel):
    hydrogen_bond_count: int = 0
    hydrophobic_contact_count: int = 0
    salt_bridge_count: int = 0
    pi_stacking_count: int = 0
    total_interactions: int = 0


class InteractionDetail(BaseModel):
    interaction_type: str
    protein_chain: Optional[str] = None
    residue_name: Optional[str] = None
    residue_number: Optional[int] = None
    protein_atom: Optional[str] = None
    ligand_atom: Optional[str] = None
    distance_angstrom: Optional[float] = None


class InteractionSourceFiles(BaseModel):
    receptor_pdb_s3_key: Optional[str] = None
    docked_pose_s3_key: Optional[str] = None
    complex_file_s3_key: Optional[str] = None
    interaction_summary_s3_key: Optional[str] = None


class InteractionAnalysisResult(BaseModel):
    job_id: str
    docking_job_id: str
    interaction_backend: str
    analysis_status: str
    target_name: Optional[str] = None
    target_uniprot_accession: Optional[str] = None
    ligand_name: Optional[str] = None
    bindingdb_monomer_id: Optional[str] = None
    summary: InteractionSummary
    interactions: List[InteractionDetail] = []
    parser_note: Optional[str] = None
    error_message: Optional[str] = None
    source_files: InteractionSourceFiles
    limitation_note: str


class InteractionAnalysisResultResponse(BaseModel):
    job_id: str
    status: str
    output_s3_key: str
    result: Optional[InteractionAnalysisResult] = None
    safety_note: str