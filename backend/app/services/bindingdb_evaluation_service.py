from typing import Any, Dict, List, Optional

from app.schemas.bindingdb_evaluation import (
    BindingDBCandidate,
    BindingDBEvaluationRequest,
    BindingDBEvaluationResponse,
    BindingDBEvaluationSummary,
)
from app.services.bindingdb_client import get_bindingdb_ligands_by_uniprot


SAFETY_NOTE = (
    "BindingDB evaluation is a small computational sanity-check only. BindingDB affinity "
    "values are experimental database records, but DeepPurpose predictions are model outputs "
    "and are not medical or therapeutic claims. Docking, ADMET analysis, literature review, "
    "and experimental validation are required."
)

EVALUATION_NOTE = (
    "Small BindingDB sanity-check only. This is not a full benchmark and should not be "
    "treated as model validation."
)

LIMITATION_NOTE = (
    "Tiny BindingDB sanity-check only. The number of molecules may be very small, "
    "so this should not be interpreted as a full benchmark or model validation."
)


def _make_ground_truth_ranking(
    candidates: List[BindingDBCandidate],
) -> List[Dict[str, Any]]:
    sorted_candidates = sorted(
        candidates,
        key=lambda candidate: candidate.p_affinity,
        reverse=True,
    )

    ranking = []

    for rank, candidate in enumerate(sorted_candidates, start=1):
        ranking.append(
            {
                "rank": rank,
                "compound_name": candidate.compound_name,
                "bindingdb_monomer_id": candidate.bindingdb_monomer_id,
                "affinity_type": candidate.affinity_type,
                "affinity_value_nm": candidate.affinity_value_nm,
                "p_affinity": candidate.p_affinity,
                "source_database": candidate.source_database,
                "source_url": candidate.source_url,
            }
        )

    return ranking


def _get_strongest_candidate(
    ground_truth_ranking: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not ground_truth_ranking:
        return None

    return ground_truth_ranking[0]

def _build_screening_input_from_bindingdb_candidates(
    job_id: str,
    target_name: str,
    protein_sequence: Optional[str],
    candidates: List[BindingDBCandidate],
) -> Dict[str, Any]:
    return {
        "job_id": job_id,
        "target_protein": target_name,
        "gene": None,
        "organism": None,
        "uniprot_accession": candidates[0].uniprot_accession if candidates else None,
        "protein_sequence": protein_sequence or "",
        "candidates": [
            {
                "compound_name": candidate.compound_name,
                "canonical_smiles": candidate.canonical_smiles,
                "source_database": candidate.source_database,
                "source_id": candidate.bindingdb_monomer_id,
                "source_url": candidate.source_url,
                "ground_truth_interaction": "known_bindingdb_affinity",
                "bindingdb_monomer_id": candidate.bindingdb_monomer_id,
                "affinity_type": candidate.affinity_type,
                "affinity_value_nm": candidate.affinity_value_nm,
                "affinity_unit": candidate.affinity_unit,
                "p_affinity": candidate.p_affinity,
                "label_source": "BindingDB experimental affinity record",
                "control_type": "bindingdb_affinity_candidate",
            }
            for candidate in candidates
        ],
    }

def _candidate_key(candidate: Dict[str, Any]) -> Optional[str]:
    for key in ["bindingdb_monomer_id", "source_id", "compound_name"]:
        value = candidate.get(key)

        if value:
            return str(value).strip().lower()

    return None


def _make_deeppurpose_ranking(
    ranked_candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    ranking = []

    for candidate in ranked_candidates:
        ranking.append(
            {
                "rank": candidate.get("rank"),
                "compound_name": candidate.get("compound_name"),
                "bindingdb_monomer_id": candidate.get(
                    "bindingdb_monomer_id"
                )
                or candidate.get("source_id"),
                "dti_score": candidate.get("dti_score"),
                "model_name": candidate.get("model_name"),
                "source_database": candidate.get("source_database"),
                "source_url": candidate.get("source_url"),
            }
        )

    return ranking


def _find_rank_of_strongest_candidate(
    strongest_ground_truth_candidate: Optional[Dict[str, Any]],
    deeppurpose_ranking: List[Dict[str, Any]],
) -> Optional[int]:
    if not strongest_ground_truth_candidate:
        return None

    strongest_key = _candidate_key(strongest_ground_truth_candidate)

    if not strongest_key:
        return None

    for candidate in deeppurpose_ranking:
        if _candidate_key(candidate) == strongest_key:
            return candidate.get("rank")

    return None


def _spearman_rank_correlation(
    ground_truth_ranking: List[Dict[str, Any]],
    deeppurpose_ranking: List[Dict[str, Any]],
) -> Optional[float]:
    ground_truth_ranks = {}
    deeppurpose_ranks = {}

    for candidate in ground_truth_ranking:
        key = _candidate_key(candidate)
        if key and candidate.get("rank") is not None:
            ground_truth_ranks[key] = candidate["rank"]

    for candidate in deeppurpose_ranking:
        key = _candidate_key(candidate)
        if key and candidate.get("rank") is not None:
            deeppurpose_ranks[key] = candidate["rank"]

    shared_keys = [
        key for key in ground_truth_ranks.keys() if key in deeppurpose_ranks
    ]

    n = len(shared_keys)

    if n < 2:
        return None

    squared_rank_diffs = [
        (ground_truth_ranks[key] - deeppurpose_ranks[key]) ** 2
        for key in shared_keys
    ]

    spearman = 1 - (
        (6 * sum(squared_rank_diffs)) / (n * ((n * n) - 1))
    )

    return round(spearman, 4)


def compare_bindingdb_with_deeppurpose_output(
    bindingdb_response: BindingDBEvaluationResponse,
    deeppurpose_output: Dict[str, Any],
) -> BindingDBEvaluationResponse:
    ground_truth_ranking = bindingdb_response.summary.ground_truth_ranking
    deeppurpose_ranking = _make_deeppurpose_ranking(
        deeppurpose_output.get("ranked_candidates", [])
    )
    strongest_candidate = bindingdb_response.summary.strongest_ground_truth_candidate

    bindingdb_response.summary.deeppurpose_ranking = deeppurpose_ranking
    rank_of_strongest = _find_rank_of_strongest_candidate(
        strongest_ground_truth_candidate=strongest_candidate,
        deeppurpose_ranking=deeppurpose_ranking,
    )

    bindingdb_response.summary.rank_of_strongest_candidate_in_deeppurpose = (
        rank_of_strongest
    )

    if rank_of_strongest == 1:
        bindingdb_response.summary.ranking_agreement = (
            "strongest_bindingdb_candidate_ranked_first_by_deeppurpose"
        )
    elif rank_of_strongest is None:
        bindingdb_response.summary.ranking_agreement = (
            "strongest_bindingdb_candidate_not_found_in_deeppurpose_output"
        )
    else:
        bindingdb_response.summary.ranking_agreement = (
            "strongest_bindingdb_candidate_not_ranked_first_by_deeppurpose"
        )

    bindingdb_response.summary.spearman_rank_correlation = (
        _spearman_rank_correlation(
            ground_truth_ranking=ground_truth_ranking,
            deeppurpose_ranking=deeppurpose_ranking,
        )
    )

    return bindingdb_response

def prepare_bindingdb_evaluation(
    request: BindingDBEvaluationRequest,
) -> BindingDBEvaluationResponse:
    bindingdb_result = get_bindingdb_ligands_by_uniprot(
        uniprot_accession=request.uniprot_accession,
    )

    records = bindingdb_result.get("records", [])[: request.max_records]

    candidates = [
        BindingDBCandidate(
            compound_name=record["compound_name"],
            canonical_smiles=record["canonical_smiles"],
            bindingdb_monomer_id=record.get("bindingdb_monomer_id"),
            uniprot_accession=record["uniprot_accession"],
            affinity_type=record["affinity_type"],
            affinity_value_nm=record["affinity_value_nm"],
            affinity_unit=record["affinity_unit"],
            p_affinity=record["p_affinity"],
            source_database=record["source_database"],
            source_url=record.get("source_url"),
            retrieval_status=record["retrieval_status"],
        )
        for record in records
    ]

    ground_truth_ranking = _make_ground_truth_ranking(candidates)

    summary = BindingDBEvaluationSummary(
        bindingdb_records_found=bindingdb_result.get("raw_records_found", 0),
        valid_records_used=len(candidates),
        unique_molecules_used=len(candidates),
        affinity_types_used=bindingdb_result.get("affinity_types_used", []),
        ground_truth_ranking=ground_truth_ranking,
        deeppurpose_ranking=None,
        strongest_ground_truth_candidate=_get_strongest_candidate(
            ground_truth_ranking
        ),
        rank_of_strongest_candidate_in_deeppurpose=None,
        ranking_agreement=None,
        spearman_rank_correlation=None,
        evaluation_note=EVALUATION_NOTE,
        limitation_note=LIMITATION_NOTE,
    )

    screening_input_preview = _build_screening_input_from_bindingdb_candidates(
        job_id=f"bindingdb-{request.uniprot_accession.lower()}-sanity-check",
        target_name=request.target_name or request.uniprot_accession,
        protein_sequence=request.protein_sequence,
        candidates=candidates,
    )

    return BindingDBEvaluationResponse(
        uniprot_accession=request.uniprot_accession,
        target_name=request.target_name,
        candidates=candidates,
        summary=summary,
        screening_input_preview=screening_input_preview,
        next_pipeline_step="submit_bindingdb_candidates_to_deeppurpose_screening",
        safety_note=SAFETY_NOTE,
    )