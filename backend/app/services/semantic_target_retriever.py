import math
import re

from app.data.target_knowledge_base import TARGET_KNOWLEDGE_BASE
from app.schemas.target import ResolvedTargetCandidate, TargetResolveRequest
from app.services.embedding_service import embed_text, get_target_record_embeddings


def normalize_text(value: str) -> str:
    return value.strip().lower()


def tokenize(value: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9]+", normalize_text(value)))


def build_query_text(request: TargetResolveRequest) -> str:
    return (
        f"Disease: {request.disease}. "
        f"Pathogen: {request.pathogen}. "
        f"Resistance mechanism: {request.resistance_mechanism}."
    )


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if len(vector_a) != len(vector_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    magnitude_a = math.sqrt(sum(a * a for a in vector_a))
    magnitude_b = math.sqrt(sum(b * b for b in vector_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def confidence_from_score(score: float, mode: str) -> str:
    if mode == "semantic":
        if score >= 0.75:
            return "semantic-high"
        if score >= 0.6:
            return "semantic-medium"
        return "semantic-low"

    if score >= 0.75:
        return "keyword-high"
    if score >= 0.45:
        return "keyword-medium"
    return "keyword-low"


def build_candidate(
    rank: int,
    record: dict[str, str],
    score: float,
    mode: str,
) -> ResolvedTargetCandidate:
    return ResolvedTargetCandidate(
        rank=rank,
        gene=record["gene"],
        protein=record["protein"],
        target_family=record["target_family"],
        mechanism_category=record["mechanism_category"],
        confidence=confidence_from_score(score, mode),
        retrieval_score=round(score, 4),
        evidence_source=record["evidence_source"],
        reason=(
            f"Matched by {mode} retrieval against local AMR target record: "
            f"{record['search_text']}"
        ),
        needs_external_verification=True,
    )


def semantic_retrieve_targets(
    request: TargetResolveRequest,
    top_k: int = 3,
) -> list[ResolvedTargetCandidate]:
    query_text = build_query_text(request)
    query_embedding = embed_text(
        text=query_text,
        task_type="RETRIEVAL_QUERY",
    )
    record_embeddings = get_target_record_embeddings()

    scored_records: list[tuple[float, dict[str, str]]] = []

    for record in TARGET_KNOWLEDGE_BASE:
        record_embedding = record_embeddings.get(record["id"])

        if not record_embedding:
            continue

        score = cosine_similarity(query_embedding, record_embedding)
        scored_records.append((score, record))

    scored_records.sort(key=lambda item: item[0], reverse=True)

    strong_matches = [
        (score, record)
        for score, record in scored_records
        if score >= 0.45
    ][:top_k]

    return [
        build_candidate(
            rank=index + 1,
            record=record,
            score=score,
            mode="semantic",
        )
        for index, (score, record) in enumerate(strong_matches)
    ]


def keyword_score(request: TargetResolveRequest, record: dict[str, str]) -> float:
    query_tokens = tokenize(
        f"{request.disease} {request.pathogen} {request.resistance_mechanism}"
    )
    record_tokens = tokenize(record["search_text"])

    if not query_tokens:
        return 0.0

    overlap_score = len(query_tokens.intersection(record_tokens)) / len(query_tokens)

    exact_pathogen_bonus = 0.35 if (
        normalize_text(request.pathogen) == normalize_text(record["pathogen"])
    ) else 0.0

    exact_mechanism_bonus = 0.35 if (
        normalize_text(request.resistance_mechanism)
        == normalize_text(record["resistance_mechanism"])
    ) else 0.0

    return min(overlap_score + exact_pathogen_bonus + exact_mechanism_bonus, 1.0)


def keyword_retrieve_targets(
    request: TargetResolveRequest,
    top_k: int = 3,
) -> list[ResolvedTargetCandidate]:
    scored_records = [
        (keyword_score(request, record), record)
        for record in TARGET_KNOWLEDGE_BASE
    ]

    scored_records.sort(key=lambda item: item[0], reverse=True)

    strong_matches = [
        (score, record)
        for score, record in scored_records
        if score >= 0.35
    ][:top_k]

    return [
        build_candidate(
            rank=index + 1,
            record=record,
            score=score,
            mode="keyword",
        )
        for index, (score, record) in enumerate(strong_matches)
    ]