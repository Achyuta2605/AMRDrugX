import json
import math
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BINDINGDB_BASE_URL = "https://bindingdb.org/rest"
DEFAULT_TIMEOUT_SECONDS = 30
SUPPORTED_AFFINITY_TYPES = {"IC50", "Ki", "Kd"}


def _get_text(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> str:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AMRDrugX/0.1 research-prototype",
        },
    )

    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _safe_json_loads(text: str) -> Any:
    if not text or not text.strip():
        return None

    return json.loads(text)


def _as_record_list(payload: Any) -> List[Dict[str, Any]]:
    if payload is None:
        return []

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    for key in [
            "getLindsByUniprotsResponse",
            "getLigandsByUniprotsResponse",
            "getLigandsByUniprotResponse",
            "response",
            "data",
            "results",
            "records",
            "ligands",
            "affinities",
        ]:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested_records = _as_record_list(value)
                if nested_records:
                    return nested_records

    return [payload]

    return []


def _first_present(record: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    for key in keys:
        if key in record and record[key] not in [None, ""]:
            return record[key]

    lower_key_map = {key.lower(): key for key in record.keys()}

    for key in keys:
        actual_key = lower_key_map.get(key.lower())
        if actual_key and record[actual_key] not in [None, ""]:
            return record[actual_key]

    return None


def _clean_affinity_type(value: Any) -> Optional[str]:
    if value is None:
        return None

    cleaned = str(value).strip()

    for supported_type in SUPPORTED_AFFINITY_TYPES:
        if cleaned.lower() == supported_type.lower():
            return supported_type

    return None


def _clean_affinity_unit(value: Any) -> Optional[str]:
    if value is None:
        return None

    cleaned = str(value).strip()

    if cleaned.lower() in {"nm", "nanomolar", "nanomol/l", "nanomole"}:
        return "nM"

    return cleaned


def _parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    cleaned = (
        str(value)
        .strip()
        .replace(",", "")
        .replace("<", "")
        .replace(">", "")
        .replace("=", "")
    )

    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def _calculate_p_affinity(value_nm: float) -> Optional[float]:
    if value_nm <= 0:
        return None

    return round(9 - math.log10(value_nm), 4)


def _normalize_bindingdb_record(
    record: Dict[str, Any],
    uniprot_accession: str,
    request_url: str,
) -> Optional[Dict[str, Any]]:
    affinity_type = _clean_affinity_type(
        _first_present(
            record,
            [
                "affinity_type",
                "Affinity Type",
                "affinityType",
                "standard_type",
            ],
        )
    )

    if affinity_type not in SUPPORTED_AFFINITY_TYPES:
        return None

    affinity_unit = _clean_affinity_unit(
        _first_present(
            record,
            [
                "affinity_unit",
                "Affinity Unit",
                "affinityUnit",
                "units",
                "standard_units",
            ],
        )
    )

    if affinity_unit is None and _first_present(record, ["affinity"]) is not None:
        affinity_unit = "nM"

    if affinity_unit != "nM":
        return None

    affinity_value_nm = _parse_float(
        _first_present(
            record,
            [
                "affinity",
                "affinity_value",
                "Affinity Value",
                "affinityValue",
                "value",
                "standard_value",
            ],
        )
    )

    if affinity_value_nm is None:
        return None

    p_affinity = _calculate_p_affinity(affinity_value_nm)

    if p_affinity is None:
        return None

    smiles = _first_present(
        record,
        [
            "smile",
            "smiles",
            "SMILES",
            "Ligand SMILES",
            "monomer_smiles",
        ],
    )

    if not smiles:
        return None

    monomer_id = _first_present(
        record,
        [
            "monomerid",
            "monomerID",
            "MonomerID",
            "BindingDB MonomerID",
            "bindingdb_monomer_id",
        ],
    )

    compound_name = _first_present(
        record,
        [
            "compound_name",
            "Compound Name",
            "ligand_name",
            "Ligand Name",
            "Name",
        ],
    )

    return {
        "compound_name": str(compound_name or f"BindingDB monomer {monomer_id}"),
        "canonical_smiles": str(smiles),
        "bindingdb_monomer_id": str(monomer_id) if monomer_id is not None else None,
        "uniprot_accession": uniprot_accession,
        "affinity_type": affinity_type,
        "affinity_value_nm": affinity_value_nm,
        "affinity_unit": affinity_unit,
        "p_affinity": p_affinity,
        "source_database": "BindingDB",
        "source_url": request_url,
        "retrieval_status": "found",
        "raw_record": record,
    }

def _dedupe_records_by_molecule(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    best_records_by_key: Dict[str, Dict[str, Any]] = {}

    for record in records:
        molecule_key = (
            record.get("bindingdb_monomer_id")
            or record.get("canonical_smiles")
            or record.get("compound_name")
        )

        if not molecule_key:
            continue

        molecule_key = str(molecule_key).strip().lower()
        existing_record = best_records_by_key.get(molecule_key)

        if existing_record is None:
            best_records_by_key[molecule_key] = record
            continue

        if record["p_affinity"] > existing_record["p_affinity"]:
            best_records_by_key[molecule_key] = record

    return sorted(
        best_records_by_key.values(),
        key=lambda record: record["p_affinity"],
        reverse=True,
    )

def get_bindingdb_ligands_by_uniprot(
    uniprot_accession: str,
    cutoff_nm: int = 100000,
) -> Dict[str, Any]:
    clean_accession = uniprot_accession.strip()

    if not clean_accession:
        return {
            "source_database": "BindingDB",
            "source_query": uniprot_accession,
            "retrieval_status": "error",
            "error": "uniprot_accession cannot be empty",
            "records": [],
        }

    query_params = urlencode(
        {
            "uniprot": clean_accession,
            "cutoff": str(cutoff_nm),
            "response": "application/json",
        }
    )
    url = f"{BINDINGDB_BASE_URL}/getLigandsByUniprots?{query_params}"

    try:
        text = _get_text(url)
        payload = _safe_json_loads(text)
    except HTTPError as exc:
        return {
            "source_database": "BindingDB",
            "source_query": clean_accession,
            "retrieval_status": "error",
            "error": f"BindingDB HTTP error: {exc.code}",
            "records": [],
        }
    except URLError as exc:
        return {
            "source_database": "BindingDB",
            "source_query": clean_accession,
            "retrieval_status": "error",
            "error": f"BindingDB URL error: {exc.reason}",
            "records": [],
        }
    except TimeoutError:
        return {
            "source_database": "BindingDB",
            "source_query": clean_accession,
            "retrieval_status": "error",
            "error": "BindingDB request timed out",
            "records": [],
        }
    except json.JSONDecodeError as exc:
        return {
            "source_database": "BindingDB",
            "source_query": clean_accession,
            "retrieval_status": "error",
            "error": f"BindingDB returned non-JSON response: {exc}",
            "records": [],
        }
    except Exception as exc:
        return {
            "source_database": "BindingDB",
            "source_query": clean_accession,
            "retrieval_status": "error",
            "error": f"BindingDB request failed: {exc}",
            "records": [],
        }

    raw_records = _as_record_list(payload)
    normalized_records = []

    for raw_record in raw_records:
        normalized_record = _normalize_bindingdb_record(
            record=raw_record,
            uniprot_accession=clean_accession,
            request_url=url,
        )

        if normalized_record:
            normalized_records.append(normalized_record)

        normalized_records = _dedupe_records_by_molecule(normalized_records)

    return {
        "source_database": "BindingDB",
        "source_query": clean_accession,
        "retrieval_status": "found" if normalized_records else "not_found",
        "raw_records_found": len(raw_records),
        "valid_records_used": len(normalized_records),
        "affinity_types_used": sorted(
            list({record["affinity_type"] for record in normalized_records})
        ),
        # "debug_first_raw_record_keys": (
        #     sorted(list(raw_records[0].keys())) if raw_records else []
        # ),
        # "debug_first_raw_record": raw_records[0] if raw_records else None,
        "records": normalized_records,
    }