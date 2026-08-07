from typing import Dict, List, Optional
from pydantic import BaseModel


class AMRWorkflowRequest(BaseModel):
    resistance_mechanism: str
    enzyme: Optional[str] = None
    organism: Optional[str] = None


class AMRWorkflowInput(BaseModel):
    resistance_mechanism: str
    enzyme: Optional[str] = None
    organism: Optional[str] = None


class AMRWorkflowTarget(BaseModel):
    target_name: str
    gene: Optional[str] = None
    organism: Optional[str] = None
    uniprot_accession: Optional[str] = None
    confidence: str
    source: str


class AMRWorkflowAvailableModules(BaseModel):
    protein_enrichment: bool = True
    structure_lookup: bool = True
    candidate_retrieval: bool = True
    deeppurpose_screening: bool = True
    binding_site_prediction: bool = True
    docking: bool = True
    interaction_analysis: bool = True

class AMRWorkflowKnownInputs(BaseModel):
    
    receptor_pdb_s3_key: Optional[str] = None
    ligand_name: Optional[str] = None
    bindingdb_monomer_id: Optional[str] = None
    ligand_sdf_s3_key: Optional[str] = None

class AMRWorkflowCompletedJobs(BaseModel):
    binding_site_job_id: Optional[str] = None
    docking_job_id: Optional[str] = None
    interaction_job_id: Optional[str] = None


class AMRWorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    input: AMRWorkflowInput
    target: AMRWorkflowTarget
    available_modules: AMRWorkflowAvailableModules
    known_inputs: AMRWorkflowKnownInputs
    completed_demo_jobs: AMRWorkflowCompletedJobs
    recommended_next_steps: List[str]
    action_endpoints: Dict[str, str]
    safety_note: str