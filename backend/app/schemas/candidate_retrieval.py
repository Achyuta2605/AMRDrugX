from typing import List, Optional

from pydantic import BaseModel


class CandidateRetrievalRequest(BaseModel):
    target_name: str
    gene: Optional[str] = None
    organism: Optional[str] = None
    resistance_mechanism: Optional[str] = None


class RetrievedCandidate(BaseModel):
    compound_name: str
    canonical_smiles: Optional[str] = None
    candidate_role: str
    evidence_type: str
    activity_type: Optional[str] = None
    activity_value: Optional[float] = None
    activity_units: Optional[str] = None
    activity_relation: Optional[str] = None
    source_database: str
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    source_query: str
    label_status: str
    ground_truth_interaction: str
    control_type: str
    retrieval_status: str
    notes: str


class CandidateRetrievalResponse(BaseModel):
    target_name: str
    gene: Optional[str] = None
    organism: Optional[str] = None
    resistance_mechanism: Optional[str] = None
    candidates: List[RetrievedCandidate]
    total_candidates: int
    retrieval_mode: str
    primary_source: str
    retrieval_notes: str
    safety_note: str