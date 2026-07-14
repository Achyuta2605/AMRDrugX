from typing import Any, Dict, List, Optional, Set

from app.data.candidate_seed_sets import get_seed_set_for_target
from app.schemas.candidate_retrieval import (
    CandidateRetrievalRequest,
    CandidateRetrievalResponse,
    RetrievedCandidate,
)
from app.services.chembl_client import (
    get_chembl_activities_for_target,
    get_chembl_molecule_by_id,
    search_chembl_molecule_by_name,
    search_chembl_targets,
)
from app.services.pubchem_client import lookup_pubchem_compound_by_name


SAFETY_NOTE = (
    "Candidate retrieval uses public database metadata for computational research only. "
    "Retrieved molecules are not therapeutic recommendations and require evidence review, "
    "docking, ADMET analysis, and experimental validation."
)


def _build_target_query(request: CandidateRetrievalRequest) -> str:
    query_parts = [
        request.target_name,
        request.gene or "",
        request.organism or "",
        request.resistance_mechanism or "",
    ]

    return " ".join(part.strip() for part in query_parts if part and part.strip())

def _parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _make_candidate_from_chembl_activity(
    molecule: Dict[str, Any],
    activity: Dict[str, Any],
    source_query: str,
) -> Optional[RetrievedCandidate]:
    match = molecule.get("match")

    if not match:
        return None

    canonical_smiles = match.get("canonical_smiles")
    compound_name = match.get("compound_name")
    source_id = match.get("source_id")

    if not compound_name or not source_id:
        return None

    activity_summary = (
        f"ChEMBL activity evidence: {activity.get('standard_type')} "
        f"{activity.get('standard_relation') or ''} "
        f"{activity.get('standard_value') or ''} "
        f"{activity.get('standard_units') or ''}".strip()
    )

    return RetrievedCandidate(
        compound_name=compound_name,
        canonical_smiles=canonical_smiles,
        candidate_role="chembl_bioactivity_candidate",
        evidence_type="chembl_target_activity",
        activity_type=activity.get("standard_type"),
        activity_value=_parse_float(activity.get("standard_value")),
        activity_units=activity.get("standard_units"),
        activity_relation=activity.get("standard_relation"),
        source_database="ChEMBL",
        source_id=source_id,
        source_url=match.get("source_url"),
        source_query=source_query,
        label_status="to_be_verified",
        ground_truth_interaction="unknown",
        control_type="candidate",
        retrieval_status="found",
        notes=activity_summary,
    )


def _make_candidate_from_seed(seed: Dict[str, Any], target_name: str) -> RetrievedCandidate:
    compound_name = seed["compound_name"]

    chembl_result = search_chembl_molecule_by_name(compound_name, limit=1)
    chembl_matches = chembl_result.get("matches", [])

    if chembl_matches:
        match = chembl_matches[0]

        if match.get("canonical_smiles"):
            return RetrievedCandidate(
                compound_name=match.get("compound_name") or compound_name,
                canonical_smiles=match.get("canonical_smiles"),
                candidate_role=seed["candidate_role"],
                evidence_type=seed["evidence_type"],
                source_database="ChEMBL",
                source_id=match.get("source_id"),
                source_url=match.get("source_url"),
                source_query=compound_name,
                label_status=seed["label_status"],
                ground_truth_interaction=seed["ground_truth_interaction"],
                control_type=seed["control_type"],
                retrieval_status="found",
                notes=seed["notes"],
            )

    pubchem_result = lookup_pubchem_compound_by_name(compound_name)
    pubchem_match = pubchem_result.get("match")

    if pubchem_match:
        return RetrievedCandidate(
            compound_name=compound_name,
            canonical_smiles=pubchem_match.get("canonical_smiles"),
            candidate_role=seed["candidate_role"],
            evidence_type=seed["evidence_type"],
            source_database="PubChem",
            source_id=pubchem_match.get("source_id"),
            source_url=pubchem_match.get("source_url"),
            source_query=compound_name,
            label_status=seed["label_status"],
            ground_truth_interaction=seed["ground_truth_interaction"],
            control_type=seed["control_type"],
            retrieval_status="found",
            notes=seed["notes"],
        )

    return RetrievedCandidate(
        compound_name=compound_name,
        canonical_smiles=None,
        candidate_role=seed["candidate_role"],
        evidence_type=seed["evidence_type"],
        source_database="local_seed",
        source_id=None,
        source_url=None,
        source_query=compound_name,
        label_status=seed["label_status"],
        ground_truth_interaction=seed["ground_truth_interaction"],
        control_type=seed["control_type"],
        retrieval_status="metadata_not_found",
        notes=seed["notes"],
    )


def _dedupe_candidates(candidates: List[RetrievedCandidate]) -> List[RetrievedCandidate]:
    seen: Set[str] = set()
    deduped = []

    for candidate in candidates:
        key = (
            candidate.canonical_smiles
            or candidate.source_id
            or candidate.compound_name
        ).strip().lower()

        if key in seen:
            continue

        seen.add(key)
        deduped.append(candidate)

    return deduped

def _activity_sort_key(candidate: RetrievedCandidate):
    preferred_activity_types = {
        "IC50": 1,
        "Ki": 2,
        "Kd": 3,
        "EC50": 4,
    }

    activity_type = candidate.activity_type or ""
    activity_rank = preferred_activity_types.get(activity_type, 99)

    if candidate.activity_value is None:
        return (activity_rank, 1, float("inf"))

    return (activity_rank, 0, candidate.activity_value)

def retrieve_candidates_for_target(
    request: CandidateRetrievalRequest,
) -> CandidateRetrievalResponse:
    target_query = _build_target_query(request)
    candidates: List[RetrievedCandidate] = []

    target_result = search_chembl_targets(target_query, limit=5)
    targets = target_result.get("targets", [])

    for target in targets:
        target_chembl_id = target.get("target_chembl_id")

        if not target_chembl_id:
            continue

        activity_result = get_chembl_activities_for_target(
            target_chembl_id=target_chembl_id,
            limit=25,
        )

        for activity in activity_result.get("activities", []):
            molecule_chembl_id = activity.get("molecule_chembl_id")

            if not molecule_chembl_id:
                continue

            molecule_result = get_chembl_molecule_by_id(molecule_chembl_id)
            candidate = _make_candidate_from_chembl_activity(
                molecule=molecule_result,
                activity=activity,
                source_query=target_query,
            )

            if candidate:
                candidates.append(candidate)

    candidates = _dedupe_candidates(candidates)
    candidates = sorted(candidates, key=_activity_sort_key)

    retrieval_mode = "chembl_target_activity"

    if not candidates:
        seed_candidates = [
            _make_candidate_from_seed(seed, request.target_name)
            for seed in get_seed_set_for_target(request.target_name)
        ]
        candidates = _dedupe_candidates(seed_candidates)
        retrieval_mode = "seed_query_with_chembl_pubchem_metadata_fallback"

    if retrieval_mode == "chembl_target_activity":
        primary_source = "ChEMBL"
        retrieval_notes = (
            "Candidates were retrieved from ChEMBL target/activity records and sorted "
            "with simple activity-evidence prioritization. Labels remain to_be_verified."
        )
    else:
        primary_source = "ChEMBL/PubChem/local_seed"
        retrieval_notes = (
            "No ChEMBL target/activity candidates were found. Returned target-specific "
            "seed queries enriched with ChEMBL or PubChem metadata where available."
        )

    return CandidateRetrievalResponse(
        target_name=request.target_name,
        gene=request.gene,
        organism=request.organism,
        resistance_mechanism=request.resistance_mechanism,
        candidates=candidates,
        total_candidates=len(candidates),
        retrieval_mode=retrieval_mode,
        primary_source=primary_source,
        retrieval_notes=retrieval_notes,
        safety_note=SAFETY_NOTE,
    )