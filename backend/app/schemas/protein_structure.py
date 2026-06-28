from pydantic import BaseModel, Field


class ProteinStructureLookupRequest(BaseModel):
    uniprot_accession: str = Field(..., examples=["Q9F663"])
    protein_name: str = Field(..., examples=["KPC beta-lactamase"])
    organism: str = Field(..., examples=["Klebsiella pneumoniae"])


class ProteinStructureMatch(BaseModel):
    source: str
    structure_id: str
    structure_url: str
    download_url: str
    viewer_url: str
    file_format: str
    structure_type: str
    confidence_note: str


class ProteinStructureLookupResponse(BaseModel):
    uniprot_accession: str
    protein_name: str
    organism: str
    structures: list[ProteinStructureMatch]
    next_pipeline_step: str
    safety_note: str