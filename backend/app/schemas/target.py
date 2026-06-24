from pydantic import BaseModel, Field


class TargetResolveRequest(BaseModel):
    pathogen: str = Field(..., examples=["Klebsiella pneumoniae"])
    antibiotic: str = Field(..., examples=["meropenem"])
    resistance_mechanism: str = Field(..., examples=["carbapenem resistance"])
    known_resistance_protein: str | None = Field(
        default=None,
        examples=["KPC-2 beta-lactamase"],
    )


class TargetResolveResponse(BaseModel):
    pathogen: str
    antibiotic: str
    resistance_mechanism: str
    gene: str
    resolved_target_name: str
    target_type: str
    target_family: str
    mechanism_category: str
    organism: str
    confidence: str
    evidence_source: str
    explanation: str
    next_pipeline_step: str
    safety_note: str