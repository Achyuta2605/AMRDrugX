from pydantic import BaseModel, Field


class MoleculeCandidate(BaseModel):
    compound_name: str = Field(..., examples=["avibactam"])
    canonical_smiles: str = Field(..., examples=["CC1(C)S[C@@H]2[C@H](NC(=O)C(N)C3=CC=CC=C3)C(=O)N2C1C(=O)O"])
    source_database: str = Field(..., examples=["PubChem"])
    source_id: str = Field(..., examples=["9835049"])
    source_url: str = Field(..., examples=["https://pubchem.ncbi.nlm.nih.gov/compound/9835049"])


class VirtualScreeningRequest(BaseModel):
    target_protein: str = Field(..., examples=["KPC beta-lactamase"])
    gene: str = Field(..., examples=["blaKPC"])
    organism: str = Field(..., examples=["Klebsiella pneumoniae"])
    uniprot_accession: str = Field(..., examples=["Q9F663"])
    protein_sequence: str = Field(..., examples=["PASTE_PROTEIN_SEQUENCE_FROM_UNIPROT_HERE"])
    candidates: list[MoleculeCandidate]


class ScoredMoleculeCandidate(BaseModel):
    rank: int
    compound_name: str
    canonical_smiles: str
    source_database: str
    source_id: str
    source_url: str
    dti_score: float
    score_type: str
    model_name: str
    screening_note: str
    needs_docking_validation: bool
    needs_admet_validation: bool


class VirtualScreeningResponse(BaseModel):
    job_id: str
    storage_backend: str
    input_location: str
    output_location: str
    target_protein: str
    gene: str
    organism: str
    uniprot_accession: str
    total_candidates_screened: int
    ranked_candidates: list[ScoredMoleculeCandidate]
    model_backend: str
    next_pipeline_step: str
    safety_note: str