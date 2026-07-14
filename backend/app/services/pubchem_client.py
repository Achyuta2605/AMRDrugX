import json
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
DEFAULT_TIMEOUT_SECONDS = 15


def _get_json(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AMRDrugX/0.1 research-prototype",
        },
    )

    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def lookup_pubchem_compound_by_name(compound_name: str) -> Dict[str, Any]:
    clean_name = compound_name.strip()

    if not clean_name:
        return {
            "source_database": "PubChem",
            "source_query": compound_name,
            "retrieval_status": "error",
            "error": "compound_name cannot be empty",
            "match": None,
        }

    encoded_name = quote(clean_name)
    url = (
        f"{PUBCHEM_BASE_URL}/compound/name/{encoded_name}"
        "/property/CanonicalSMILES/JSON"
    )

    try:
        payload = _get_json(url)
    except HTTPError as exc:
        if exc.code == 404:
            return {
                "source_database": "PubChem",
                "source_query": clean_name,
                "retrieval_status": "not_found",
                "match": None,
            }

        return {
            "source_database": "PubChem",
            "source_query": clean_name,
            "retrieval_status": "error",
            "error": f"PubChem HTTP error: {exc.code}",
            "match": None,
        }
    except URLError as exc:
        return {
            "source_database": "PubChem",
            "source_query": clean_name,
            "retrieval_status": "error",
            "error": f"PubChem URL error: {exc.reason}",
            "match": None,
        }
    except TimeoutError:
        return {
            "source_database": "PubChem",
            "source_query": clean_name,
            "retrieval_status": "error",
            "error": "PubChem request timed out",
            "match": None,
        }
    except Exception as exc:
        return {
            "source_database": "PubChem",
            "source_query": clean_name,
            "retrieval_status": "error",
            "error": f"PubChem request failed: {exc}",
            "match": None,
        }

    properties = payload.get("PropertyTable", {}).get("Properties", [])

    if not properties:
        return {
            "source_database": "PubChem",
            "source_query": clean_name,
            "retrieval_status": "not_found",
            "match": None,
        }

    first_match = properties[0]
    cid = first_match.get("CID")

    return {
        "source_database": "PubChem",
        "source_query": clean_name,
        "retrieval_status": "found",
        "match": {
            "compound_name": clean_name,
            "cid": cid,
            "canonical_smiles": first_match.get("CanonicalSMILES"),
            "source_database": "PubChem",
            "source_id": str(cid) if cid is not None else None,
            "source_url": (
                f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
                if cid is not None
                else None
            ),
            "source_query": clean_name,
        },
    }

