import hashlib
from typing import Any, Dict, List

MODEL_BACKEND = "worker_baseline"
SCORE_TYPE = "non_biological_worker_test_score"
MODEL_NAME = "aws_worker_placeholder_not_biological"

SAFETY_NOTE = (
    "Worker baseline scores are non-biological test scores only. They are not "
    "evidence of efficacy, binding, inhibition, or safety."
)


def is_valid_smiles(smiles: str) -> bool:
    return bool(smiles and smiles.strip())


def baseline_score(protein_sequence: str, canonical_smiles: str) -> float:
    score_seed = f"{protein_sequence}|{canonical_smiles}"
    digest = hashlib.sha256(score_seed.encode("utf-8")).hexdigest()
    raw_value = int(digest[:8], 16)
    return round(raw_value / 0xFFFFFFFF, 4)


def score(job_id: str, protein_sequence: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    scored = []

    for candidate in candidates:
        smiles = candidate.get("canonical_smiles", "")

        if is_valid_smiles(smiles):
            dti_score = baseline_score(protein_sequence, smiles)
            note = "Non-biological worker baseline score for infrastructure testing only."
        else:
            dti_score = 0.0
            note = "Invalid or empty SMILES. Baseline score set to 0."

        scored.append(
            {
                "rank": 0,
                "compound_name": candidate.get("compound_name", "unknown"),
                "canonical_smiles": smiles,
                "source_database": candidate.get("source_database", "unknown"),
                "source_id": candidate.get("source_id", "unknown"),
                "source_url": candidate.get("source_url", "unknown"),
                "dti_score": dti_score,
                "score_type": SCORE_TYPE,
                "model_name": MODEL_NAME,
                "screening_note": note,
                "needs_docking_validation": True,
                "needs_admet_validation": True,
            }
        )

    ranked = sorted(scored, key=lambda item: item["dti_score"], reverse=True)

    for index, candidate in enumerate(ranked, start=1):
        candidate["rank"] = index

    return {
        "job_id": job_id,
        "status": "completed",
        "model_backend": MODEL_BACKEND,
        "score_type": SCORE_TYPE,
        "model_name": MODEL_NAME,
        "ranked_candidates": ranked,
        "safety_note": SAFETY_NOTE,
    }