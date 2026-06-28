from urllib.parse import quote

from app.schemas.protein_structure import (
    ProteinStructureLookupRequest,
    ProteinStructureLookupResponse,
    ProteinStructureMatch,
)
from app.tools.alphafold_client import search_alphafold_structure
from app.tools.pdb_client import search_pdb_structures

SAFETY_NOTE = (
    "Protein structure lookup is for computational research only. "
    "Docking and experimental validation are still required."
)

BACKEND_VIEWER_PATH = "/api/proteins/structures/view"


def build_viewer_url(download_url: str) -> str:
    encoded_url = quote(download_url, safe="")
    return f"http://127.0.0.1:8000{BACKEND_VIEWER_PATH}?structure_url={encoded_url}"


def build_structure_match(raw_structure: dict[str, str]) -> ProteinStructureMatch:
    download_url = raw_structure["download_url"]

    return ProteinStructureMatch(
        source=raw_structure["source"],
        structure_id=raw_structure["structure_id"],
        structure_url=raw_structure["structure_url"],
        download_url=download_url,
        viewer_url=build_viewer_url(download_url),
        file_format=raw_structure["file_format"],
        structure_type=raw_structure["structure_type"],
        confidence_note=raw_structure["confidence_note"],
    )


def lookup_protein_structures(
    request: ProteinStructureLookupRequest,
) -> ProteinStructureLookupResponse:
    pdb_structures = search_pdb_structures(request.uniprot_accession)
    alphafold_structures = search_alphafold_structure(request.uniprot_accession)

    combined_structures = pdb_structures + alphafold_structures

    structure_matches = [
        build_structure_match(raw_structure)
        for raw_structure in combined_structures
        if raw_structure.get("download_url")
    ]

    return ProteinStructureLookupResponse(
        uniprot_accession=request.uniprot_accession,
        protein_name=request.protein_name,
        organism=request.organism,
        structures=structure_matches,
        next_pipeline_step="candidate_molecule_retrieval",
        safety_note=SAFETY_NOTE,
    )