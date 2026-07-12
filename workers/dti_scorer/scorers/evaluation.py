from typing import Any, Dict, List, Optional


POSITIVE_LABEL = "positive"
NEGATIVE_LABEL = "negative"


def _normalize_label(value: Optional[str]) -> str:
    if not value:
        return ""

    return value.strip().lower()


def _build_label_lookup(
    candidates: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    label_lookup = {}

    for candidate in candidates:
        compound_name = candidate.get("compound_name", "")
        normalized_name = compound_name.strip().lower()

        if not normalized_name:
            continue

        label_lookup[normalized_name] = {
            "ground_truth_interaction": _normalize_label(
                candidate.get("ground_truth_interaction")
            ),
            "label_source": candidate.get("label_source", ""),
            "control_type": candidate.get("control_type", ""),
        }

    return label_lookup


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None

    return round(sum(values) / len(values), 4)


def evaluate_ranked_candidates(
    ranked_candidates: List[Dict[str, Any]],
    original_candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    label_lookup = _build_label_lookup(original_candidates)

    positive_scores = []
    negative_scores = []
    positive_ranks = []

    labeled_ranked_candidates = []

    for candidate in ranked_candidates:
        compound_name = candidate.get("compound_name", "")
        normalized_name = compound_name.strip().lower()
        label_info = label_lookup.get(normalized_name, {})

        ground_truth = label_info.get("ground_truth_interaction", "")
        dti_score = candidate.get("dti_score")
        rank = candidate.get("rank")

        if ground_truth == POSITIVE_LABEL:
            positive_ranks.append(rank)
            if dti_score is not None:
                positive_scores.append(float(dti_score))

        if ground_truth == NEGATIVE_LABEL and dti_score is not None:
            negative_scores.append(float(dti_score))

        enriched_candidate = dict(candidate)
        enriched_candidate["ground_truth_interaction"] = ground_truth or "unknown"
        enriched_candidate["label_source"] = label_info.get("label_source", "")
        enriched_candidate["control_type"] = label_info.get("control_type", "")
        labeled_ranked_candidates.append(enriched_candidate)

    num_positives = sum(
        1
        for candidate in original_candidates
        if _normalize_label(candidate.get("ground_truth_interaction")) == POSITIVE_LABEL
    )
    num_negatives = sum(
        1
        for candidate in original_candidates
        if _normalize_label(candidate.get("ground_truth_interaction")) == NEGATIVE_LABEL
    )

    top_3 = labeled_ranked_candidates[:3]
    top_3_positive_count = sum(
        1
        for candidate in top_3
        if candidate.get("ground_truth_interaction") == POSITIVE_LABEL
    )

    top_1_is_positive = False
    if labeled_ranked_candidates:
        top_1_is_positive = (
            labeled_ranked_candidates[0].get("ground_truth_interaction")
            == POSITIVE_LABEL
        )

    precision_at_3 = None
    if top_3:
        precision_at_3 = round(top_3_positive_count / len(top_3), 4)

    recall_at_3 = None
    if num_positives > 0:
        recall_at_3 = round(top_3_positive_count / num_positives, 4)

    best_positive_rank = None
    valid_positive_ranks = [rank for rank in positive_ranks if rank is not None]
    if valid_positive_ranks:
        best_positive_rank = min(valid_positive_ranks)

    return {
        "evaluation_type": "small_labeled_sanity_check",
        "num_candidates": len(original_candidates),
        "num_positives": num_positives,
        "num_negatives": num_negatives,
        "top_1_is_positive": top_1_is_positive,
        "precision_at_3": precision_at_3,
        "recall_at_3": recall_at_3,
        "best_positive_rank": best_positive_rank,
        "mean_positive_score": _mean(positive_scores),
        "mean_negative_score": _mean(negative_scores),
        "ranked_candidates_with_labels": labeled_ranked_candidates,
        "evaluation_note": (
            "Small labeled sanity-check only. This is not a full benchmark and is "
            "not sufficient for ROC-AUC, PR-AUC, or biological validation."
        ),
    }