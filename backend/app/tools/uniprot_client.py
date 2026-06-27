import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"


def build_uniprot_query(protein: str, gene: str, organism: str) -> str:
    query_parts = []

    if protein.strip():
        query_parts.append(f"({protein.strip()})")

    if gene.strip():
        query_parts.append(f"({gene.strip()})")

    if organism.strip():
        query_parts.append(f'organism_name:"{organism.strip()}"')

    return " AND ".join(query_parts)


def get_primary_gene_name(entry: dict[str, Any]) -> str:
    genes = entry.get("genes", [])

    if not genes:
        return "unknown"

    first_gene = genes[0]

    if "geneName" in first_gene:
        return first_gene["geneName"].get("value", "unknown")

    if "orderedLocusNames" in first_gene and first_gene["orderedLocusNames"]:
        return first_gene["orderedLocusNames"][0].get("value", "unknown")

    return "unknown"


def get_protein_name(entry: dict[str, Any]) -> str:
    protein_description = entry.get("proteinDescription", {})

    recommended_name = protein_description.get("recommendedName")
    if recommended_name:
        full_name = recommended_name.get("fullName", {})
        if "value" in full_name:
            return full_name["value"]

    submission_names = protein_description.get("submissionNames", [])
    if submission_names:
        full_name = submission_names[0].get("fullName", {})
        if "value" in full_name:
            return full_name["value"]

    return entry.get("uniProtkbId", "unknown")


def normalize_uniprot_entry(entry: dict[str, Any]) -> dict[str, Any]:
    accession = entry.get("primaryAccession", "unknown")
    organism = entry.get("organism", {})
    sequence = entry.get("sequence", {})

    return {
        "accession": accession,
        "protein_name": get_protein_name(entry),
        "gene_name": get_primary_gene_name(entry),
        "organism_name": organism.get("scientificName", "unknown"),
        "sequence_length": sequence.get("length"),
        "source_database": "UniProtKB",
        "source_url": f"https://www.uniprot.org/uniprotkb/{accession}/entry"
        if accession != "unknown"
        else "unknown",
        "structure_lookup_ready": accession != "unknown",
        "next_pipeline_step": "protein_structure_lookup",
    }


def search_uniprot_proteins(
    protein: str,
    gene: str,
    organism: str,
    size: int = 5,
) -> list[dict[str, Any]]:
    query = build_uniprot_query(
        protein=protein,
        gene=gene,
        organism=organism,
    )

    if not query:
        return []

    params = urllib.parse.urlencode(
        {
            "query": query,
            "format": "json",
            "size": str(size),
        }
    )

    request = urllib.request.Request(
        f"{UNIPROT_SEARCH_URL}?{params}",
        headers={
            "Accept": "application/json",
            "User-Agent": "AMRDrugX/0.1 research-prototype",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"UniProt request failed: {exc}") from exc

    parsed = json.loads(response_body)
    results = parsed.get("results", [])

    return [normalize_uniprot_entry(entry) for entry in results]