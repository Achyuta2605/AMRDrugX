import urllib.error
import urllib.request


def build_alphafold_structure_id(uniprot_accession: str) -> str:
    return f"AF-{uniprot_accession.strip()}-F1"


def build_alphafold_entry_url(uniprot_accession: str) -> str:
    return f"https://alphafold.ebi.ac.uk/entry/{uniprot_accession.strip()}"


def build_alphafold_pdb_url(uniprot_accession: str) -> str:
    structure_id = build_alphafold_structure_id(uniprot_accession)
    return f"https://alphafold.ebi.ac.uk/files/{structure_id}-model_v4.pdb"


def url_exists(url: str) -> bool:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AMRDrugX/0.1 research-prototype",
        },
        method="HEAD",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return 200 <= response.status < 400
    except urllib.error.HTTPError:
        return False
    except urllib.error.URLError:
        return False


def search_alphafold_structure(uniprot_accession: str) -> list[dict[str, str]]:
    accession = uniprot_accession.strip()

    if not accession:
        return []

    structure_id = build_alphafold_structure_id(accession)
    structure_url = build_alphafold_entry_url(accession)
    download_url = build_alphafold_pdb_url(accession)

    if not url_exists(download_url):
        return []

    return [
        {
            "source": "AlphaFoldDB",
            "structure_id": structure_id,
            "structure_url": structure_url,
            "download_url": download_url,
            "file_format": "PDB",
            "structure_type": "predicted",
            "confidence_note": (
                "Predicted structure candidate from AlphaFoldDB. "
                "This is not an experimentally determined structure."
            ),
        }
    ]