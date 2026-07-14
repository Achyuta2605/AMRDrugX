import json
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
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


def search_chembl_molecule_by_name(
    compound_name: str,
    limit: int = 5,
) -> Dict[str, Any]:
    clean_name = compound_name.strip()

    if not clean_name:
        return {
            "source_database": "ChEMBL",
            "source_query": compound_name,
            "retrieval_status": "error",
            "error": "compound_name cannot be empty",
            "matches": [],
        }

    query_params = urlencode(
        {
            "q": clean_name,
            "limit": str(limit),
        }
    )
    url = f"{CHEMBL_BASE_URL}/molecule/search.json?{query_params}"

    try:
        payload = _get_json(url)
    except HTTPError as exc:
        return {
            "source_database": "ChEMBL",
            "source_query": clean_name,
            "retrieval_status": "error",
            "error": f"ChEMBL HTTP error: {exc.code}",
            "matches": [],
        }
    except URLError as exc:
        return {
            "source_database": "ChEMBL",
            "source_query": clean_name,
            "retrieval_status": "error",
            "error": f"ChEMBL URL error: {exc.reason}",
            "matches": [],
        }
    except TimeoutError:
        return {
            "source_database": "ChEMBL",
            "source_query": clean_name,
            "retrieval_status": "error",
            "error": "ChEMBL request timed out",
            "matches": [],
        }
    except Exception as exc:
        return {
            "source_database": "ChEMBL",
            "source_query": clean_name,
            "retrieval_status": "error",
            "error": f"ChEMBL request failed: {exc}",
            "matches": [],
        }

    molecules = payload.get("molecules", [])
    matches: List[Dict[str, Any]] = []

    for molecule in molecules:
        chembl_id = molecule.get("molecule_chembl_id")
        structures = molecule.get("molecule_structures") or {}

        matches.append(
            {
                "compound_name": molecule.get("pref_name") or clean_name,
                "chembl_id": chembl_id,
                "canonical_smiles": structures.get("canonical_smiles"),
                "source_database": "ChEMBL",
                "source_id": chembl_id,
                "source_url": (
                    f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/"
                    if chembl_id
                    else None
                ),
                "source_query": clean_name,
            }
        )

    return {
        "source_database": "ChEMBL",
        "source_query": clean_name,
        "retrieval_status": "found" if matches else "not_found",
        "matches": matches,
    }


def search_chembl_targets(
    target_query: str,
    limit: int = 5,
) -> Dict[str, Any]:
    clean_query = target_query.strip()

    if not clean_query:
        return {
            "source_database": "ChEMBL",
            "source_query": target_query,
            "retrieval_status": "error",
            "error": "target_query cannot be empty",
            "targets": [],
        }

    query_params = urlencode(
        {
            "q": clean_query,
            "limit": str(limit),
        }
    )
    url = f"{CHEMBL_BASE_URL}/target/search.json?{query_params}"

    try:
        payload = _get_json(url)
    except HTTPError as exc:
        return {
            "source_database": "ChEMBL",
            "source_query": clean_query,
            "retrieval_status": "error",
            "error": f"ChEMBL target search HTTP error: {exc.code}",
            "targets": [],
        }
    except Exception as exc:
        return {
            "source_database": "ChEMBL",
            "source_query": clean_query,
            "retrieval_status": "error",
            "error": f"ChEMBL target search failed: {exc}",
            "targets": [],
        }

    targets = []

    for target in payload.get("targets", []):
        target_chembl_id = target.get("target_chembl_id")

        targets.append(
            {
                "target_chembl_id": target_chembl_id,
                "pref_name": target.get("pref_name"),
                "target_type": target.get("target_type"),
                "organism": target.get("organism"),
                "source_url": (
                    f"https://www.ebi.ac.uk/chembl/target_report_card/{target_chembl_id}/"
                    if target_chembl_id
                    else None
                ),
            }
        )

    return {
        "source_database": "ChEMBL",
        "source_query": clean_query,
        "retrieval_status": "found" if targets else "not_found",
        "targets": targets,
    }


def get_chembl_activities_for_target(
    target_chembl_id: str,
    limit: int = 25,
) -> Dict[str, Any]:
    clean_target_id = target_chembl_id.strip()

    if not clean_target_id:
        return {
            "source_database": "ChEMBL",
            "source_query": target_chembl_id,
            "retrieval_status": "error",
            "error": "target_chembl_id cannot be empty",
            "activities": [],
        }

    query_params = urlencode(
        {
            "target_chembl_id": clean_target_id,
            "limit": str(limit),
        }
    )
    url = f"{CHEMBL_BASE_URL}/activity.json?{query_params}"

    try:
        payload = _get_json(url)
    except HTTPError as exc:
        return {
            "source_database": "ChEMBL",
            "source_query": clean_target_id,
            "retrieval_status": "error",
            "error": f"ChEMBL activity HTTP error: {exc.code}",
            "activities": [],
        }
    except Exception as exc:
        return {
            "source_database": "ChEMBL",
            "source_query": clean_target_id,
            "retrieval_status": "error",
            "error": f"ChEMBL activity search failed: {exc}",
            "activities": [],
        }

    activities = []

    for activity in payload.get("activities", []):
        molecule_chembl_id = activity.get("molecule_chembl_id")

        if not molecule_chembl_id:
            continue

        activities.append(
            {
                "molecule_chembl_id": molecule_chembl_id,
                "target_chembl_id": activity.get("target_chembl_id"),
                "standard_type": activity.get("standard_type"),
                "standard_value": activity.get("standard_value"),
                "standard_units": activity.get("standard_units"),
                "standard_relation": activity.get("standard_relation"),
                "assay_chembl_id": activity.get("assay_chembl_id"),
                "document_chembl_id": activity.get("document_chembl_id"),
                "source_database": "ChEMBL",
            }
        )

    return {
        "source_database": "ChEMBL",
        "source_query": clean_target_id,
        "retrieval_status": "found" if activities else "not_found",
        "activities": activities,
    }


def get_chembl_molecule_by_id(molecule_chembl_id: str) -> Dict[str, Any]:
    clean_molecule_id = molecule_chembl_id.strip()

    if not clean_molecule_id:
        return {
            "source_database": "ChEMBL",
            "source_query": molecule_chembl_id,
            "retrieval_status": "error",
            "error": "molecule_chembl_id cannot be empty",
            "match": None,
        }

    url = f"{CHEMBL_BASE_URL}/molecule/{clean_molecule_id}.json"

    try:
        molecule = _get_json(url)
    except HTTPError as exc:
        return {
            "source_database": "ChEMBL",
            "source_query": clean_molecule_id,
            "retrieval_status": "error",
            "error": f"ChEMBL molecule HTTP error: {exc.code}",
            "match": None,
        }
    except Exception as exc:
        return {
            "source_database": "ChEMBL",
            "source_query": clean_molecule_id,
            "retrieval_status": "error",
            "error": f"ChEMBL molecule lookup failed: {exc}",
            "match": None,
        }

    structures = molecule.get("molecule_structures") or {}
    chembl_id = molecule.get("molecule_chembl_id")

    return {
        "source_database": "ChEMBL",
        "source_query": clean_molecule_id,
        "retrieval_status": "found",
        "match": {
            "compound_name": molecule.get("pref_name") or chembl_id,
            "chembl_id": chembl_id,
            "canonical_smiles": structures.get("canonical_smiles"),
            "source_database": "ChEMBL",
            "source_id": chembl_id,
            "source_url": (
                f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/"
                if chembl_id
                else None
            ),
        },
    }