from pydantic import BaseModel, Field


class TargetResolveRequest(BaseModel):
    disease: str = Field(..., examples=["carbapenem-resistant infection"])
    pathogen: str = Field(..., examples=["Klebsiella pneumoniae"])
    resistance_mechanism: str = Field(..., examples=["carbapenem resistance"])


class ResolvedTargetCandidate(BaseModel):
    rank: int
    gene: str
    protein: str
    target_family: str
    mechanism_category: str
    confidence: str
    retrieval_score: float
    evidence_source: str
    reason: str
    needs_external_verification: bool


class TargetResolveResponse(BaseModel):
    disease: str
    pathogen: str
    resistance_mechanism: str
    retrieval_mode: str
    resolved_targets: list[ResolvedTargetCandidate]
    explanation: str
    safety_note: str