from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class BindingDBEvaluationRequest(BaseModel):
    uniprot_accession: str
    target_name: Optional[str] = None
    protein_sequence: Optional[str] = None
    max_records: int = 10




class BindingDBCandidate(BaseModel):
    compound_name: str
    canonical_smiles: str
    bindingdb_monomer_id: Optional[str] = None
    uniprot_accession: str
    affinity_type: str
    affinity_value_nm: float
    affinity_unit: str
    p_affinity: float
    source_database: str
    source_url: Optional[str] = None
    retrieval_status: str


class BindingDBEvaluationSummary(BaseModel):
    bindingdb_records_found: int
    valid_records_used: int
    affinity_types_used: List[str]
    ground_truth_ranking: List[Dict[str, Any]]
    deeppurpose_ranking: Optional[List[Dict[str, Any]]] = None
    strongest_ground_truth_candidate: Optional[Dict[str, Any]] = None
    rank_of_strongest_candidate_in_deeppurpose: Optional[int] = None
    spearman_rank_correlation: Optional[float] = None
    evaluation_note: str
    # debug_first_raw_record_keys: Optional[List[str]] = None
    # debug_first_raw_record: Optional[Dict[str, Any]] = None


class BindingDBEvaluationResponse(BaseModel):
    uniprot_accession: str
    target_name: Optional[str] = None
    candidates: List[BindingDBCandidate]
    summary: BindingDBEvaluationSummary
    screening_input_preview: Optional[Dict[str, Any]] = None
    next_pipeline_step: str
    safety_note: str


class BindingDBComparisonRequest(BaseModel):
    bindingdb_prepare_response: BindingDBEvaluationResponse
    deeppurpose_output: Dict[str, Any]