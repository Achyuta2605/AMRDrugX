import json
import urllib.error
import urllib.request
from typing import Any

RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"


def build_uniprot_search_payload(uniprot_accession: str) -> dict[str, Any]:
    return {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": uniprot_accession.strip(),
            },
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {
                "start": 0,
                "rows": 5,
            },
            "sort": [
                {
                    "sort_by": "score",
                    "direction": "desc",
                }
            ],
        },
    }


def search_pdb_structures(uniprot_accession: str) -> list[dict[str, str]]:
    accession = uniprot_accession.strip()

    if not accession:
        return []

    payload = build_uniprot_search_payload(accession)

    request = urllib.request.Request(
        RCSB_SEARCH_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AMRDrugX/0.1 research-prototype",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError:
        return []
    except urllib.error.URLError:
        return []

    if not response_body.strip():
     return []

    try:
       parsed = json.loads(response_body)
    except json.JSONDecodeError:
       return []
  
    result_set = parsed.get("result_set", [])

    structures = []

    for result in result_set:
        pdb_id = result.get("identifier")

        if not pdb_id:
            continue

        pdb_id = pdb_id.upper()

        structures.append(
            {
                "source": "PDB",
                "structure_id": pdb_id,
                "structure_url": f"https://www.rcsb.org/structure/{pdb_id}",
                "download_url": f"https://files.rcsb.org/download/{pdb_id}.pdb",
                "file_format": "PDB",
                "structure_type": "experimental",
                "confidence_note": "Experimental structure candidate from PDB.",
            }
        )

    return structures