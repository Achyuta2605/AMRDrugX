from pydantic import BaseModel, Field


class ProteinEnrichmentRequest(BaseModel):
    protein: str = Field(..., examples=["KPC beta-lactamase"])
    gene: str = Field(..., examples=["blaKPC"])
    organism: str = Field(..., examples=["Klebsiella pneumoniae"])


class ProteinEnrichmentMatch(BaseModel):
    protein: str
    gene: str
    organism: str
    accession: str
    protein_name: str
    gene_name: str
    organism_name: str
    sequence_length: int | None
    source_database: str
    source_url: str
    structure_lookup_ready: bool
    next_pipeline_step: str
    safety_note: str


class ProteinEnrichmentResponse(BaseModel):
    protein: str
    gene: str
    organism: str
    matches: list[ProteinEnrichmentMatch]
    explanation: str
    safety_note: str