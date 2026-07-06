import os
from typing import Any, Dict, List, Tuple

MODEL_BACKEND = "deeppurpose"
SCORE_TYPE = "ai_dti_prediction_score"
DEFAULT_MODEL_NAME = "MPNN_CNN_DAVIS"

SAFETY_NOTE = (
    "Research prototype only. Scores are computational predictions, not clinical "
    "or therapeutic claims. Docking, ADMET analysis, literature review, and "
    "experimental validation are required."
)


def get_model_reference() -> Tuple[str, str]:
    model_path = os.getenv("DEEPPURPOSE_MODEL_PATH")
    model_name = os.getenv("DEEPPURPOSE_MODEL_NAME", DEFAULT_MODEL_NAME)

    if model_path:
        return "path", model_path.strip()

    if model_name:
        return "name", model_name.strip()

    raise RuntimeError(
        "DeepPurpose requires either DEEPPURPOSE_MODEL_PATH or DEEPPURPOSE_MODEL_NAME."
    )


def get_model_encoding(model: Any, key: str, fallback: str) -> str:
    config = getattr(model, "config", {})

    if isinstance(config, dict):
        return config.get(key, fallback)

    return fallback


def load_deeppurpose_model() -> Tuple[Any, str]:
    try:
        from DeepPurpose import DTI as models
    except ImportError as exc:
        raise RuntimeError(
            "DeepPurpose is not installed in this worker image. "
            "Build with INSTALL_DEEPPURPOSE=true."
        ) from exc

    reference_type, reference_value = get_model_reference()

    try:
        if reference_type == "path":
            model = models.model_pretrained(path_dir=reference_value)
            model_label = f"DeepPurpose:path:{reference_value}"
        else:
            model = models.model_pretrained(model=reference_value)
            model_label = f"DeepPurpose:model:{reference_value}"
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load DeepPurpose pretrained model {reference_value}: {exc}"
        ) from exc

    return model, model_label


def score(
    job_id: str,
    protein_sequence: str,
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    try:
        from DeepPurpose import utils
    except ImportError as exc:
        raise RuntimeError(
            "DeepPurpose utilities are not installed in this worker image."
        ) from exc

    if not protein_sequence.strip():
        raise RuntimeError("protein_sequence is required for DeepPurpose scoring.")

    valid_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("canonical_smiles", "").strip()
    ]

    if not valid_candidates:
        raise RuntimeError("At least one valid candidate SMILES is required for DeepPurpose scoring.")

    model, model_label = load_deeppurpose_model()

    drug_smiles = [candidate["canonical_smiles"] for candidate in valid_candidates]
    target_sequences = [protein_sequence for _ in valid_candidates]
    labels = [0 for _ in valid_candidates]

    drug_encoding = get_model_encoding(model, "drug_encoding", "Morgan")
    target_encoding = get_model_encoding(model, "target_encoding", "CNN")

    try:
        prediction_data = utils.data_process(
            X_drug=drug_smiles,
            X_target=target_sequences,
            y=labels,
            drug_encoding=drug_encoding,
            target_encoding=target_encoding,
            split_method="no_split",
        )
        predictions = model.predict(prediction_data)
    except Exception as exc:
        raise RuntimeError(f"DeepPurpose prediction failed: {exc}") from exc

    scored = []

    for candidate, prediction in zip(valid_candidates, predictions):
        scored.append(
            {
                "rank": 0,
                "compound_name": candidate.get("compound_name", "unknown"),
                "canonical_smiles": candidate.get("canonical_smiles", ""),
                "source_database": candidate.get("source_database", "unknown"),
                "source_id": candidate.get("source_id", "unknown"),
                "source_url": candidate.get("source_url", "unknown"),
                "dti_score": round(float(prediction), 4),
                "score_type": SCORE_TYPE,
                "model_name": model_label,
                "screening_note": (
                    "DeepPurpose DTI prediction score. Computational research estimate only."
                ),
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
        "model_name": model_label,
        "ranked_candidates": ranked,
        "safety_note": SAFETY_NOTE,
    }