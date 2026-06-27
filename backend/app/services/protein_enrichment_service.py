from app.schemas.protein import (
    ProteinEnrichmentMatch,
    ProteinEnrichmentRequest,
    ProteinEnrichmentResponse,
)
from app.tools.uniprot_client import search_uniprot_proteins

SAFETY_NOTE = (
    "Computational protein metadata enrichment only. Not medical advice. "
    "Requires database verification and experimental validation."
)


def build_match(
    request: ProteinEnrichmentRequest,
    uniprot_record: dict,
) -> ProteinEnrichmentMatch:
    return ProteinEnrichmentMatch(
        protein=request.protein,
        gene=request.gene,
        organism=request.organism,
        accession=uniprot_record["accession"],
        protein_name=uniprot_record["protein_name"],
        gene_name=uniprot_record["gene_name"],
        organism_name=uniprot_record["organism_name"],
        sequence_length=uniprot_record["sequence_length"],
        source_database=uniprot_record["source_database"],
        source_url=uniprot_record["source_url"],
        structure_lookup_ready=uniprot_record["structure_lookup_ready"],
        next_pipeline_step=uniprot_record["next_pipeline_step"],
        safety_note=SAFETY_NOTE,
    )


def enrich_protein(
    request: ProteinEnrichmentRequest,
) -> ProteinEnrichmentResponse:
    try:
        records = search_uniprot_proteins(
            protein=request.protein,
            gene=request.gene,
            organism=request.organism,
            size=5,
        )
    except RuntimeError as exc:
        return ProteinEnrichmentResponse(
            protein=request.protein,
            gene=request.gene,
            organism=request.organism,
            matches=[],
            explanation=(
                "UniProt enrichment could not be completed because the external "
                f"UniProt request failed: {exc}"
            ),
            safety_note=SAFETY_NOTE,
        )

    if not records:
        return ProteinEnrichmentResponse(
            protein=request.protein,
            gene=request.gene,
            organism=request.organism,
            matches=[],
            explanation=(
                "No UniProt matches were found for the provided protein, gene, "
                "and organism. AMRDrugX did not infer or hallucinate metadata."
            ),
            safety_note=SAFETY_NOTE,
        )

    matches = [
        build_match(request=request, uniprot_record=record)
        for record in records
    ]

    return ProteinEnrichmentResponse(
        protein=request.protein,
        gene=request.gene,
        organism=request.organism,
        matches=matches,
        explanation=(
            "Possible UniProt protein metadata matches were retrieved. These "
            "matches should be reviewed before structure lookup or downstream "
            "molecular screening."
        ),
        safety_note=SAFETY_NOTE,
    )