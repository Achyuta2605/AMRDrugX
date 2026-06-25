from app.schemas.target import TargetResolveRequest, TargetResolveResponse
from app.services.embedding_service import gemini_embeddings_available
from app.services.semantic_target_retriever import (
    keyword_retrieve_targets,
    semantic_retrieve_targets,
)

SAFETY_NOTE = (
    "Computational target prioritization only. Not medical advice. "
    "Requires database verification and experimental validation."
)


def build_empty_response(
    request: TargetResolveRequest,
    retrieval_mode: str,
    explanation: str,
) -> TargetResolveResponse:
    return TargetResolveResponse(
        disease=request.disease,
        pathogen=request.pathogen,
        resistance_mechanism=request.resistance_mechanism,
        retrieval_mode=retrieval_mode,
        resolved_targets=[],
        explanation=explanation,
        safety_note=SAFETY_NOTE,
    )


def resolve_target(request: TargetResolveRequest) -> TargetResolveResponse:
    if gemini_embeddings_available():
        try:
            semantic_targets = semantic_retrieve_targets(request, top_k=3)

            if semantic_targets:
                return TargetResolveResponse(
                    disease=request.disease,
                    pathogen=request.pathogen,
                    resistance_mechanism=request.resistance_mechanism,
                    retrieval_mode="semantic_embedding",
                    resolved_targets=semantic_targets,
                    explanation=(
                        "Targets were ranked using Gemini text embeddings over "
                        "local AMR target records and cosine similarity. These "
                        "results still require external database verification."
                    ),
                    safety_note=SAFETY_NOTE,
                )

            return build_empty_response(
                request=request,
                retrieval_mode="semantic_embedding",
                explanation=(
                    "Gemini embedding retrieval ran successfully, but no strong "
                    "local AMR target match was found. Do not continue to molecule "
                    "screening until the target is verified."
                ),
            )

        except RuntimeError:
            keyword_targets = keyword_retrieve_targets(request, top_k=3)

            if keyword_targets:
                return TargetResolveResponse(
                    disease=request.disease,
                    pathogen=request.pathogen,
                    resistance_mechanism=request.resistance_mechanism,
                    retrieval_mode="keyword_fallback_after_embedding_failure",
                    resolved_targets=keyword_targets,
                    explanation=(
                        "Gemini embedding retrieval failed, so the resolver used "
                        "deterministic keyword fallback over the local AMR target "
                        "knowledge base."
                    ),
                    safety_note=SAFETY_NOTE,
                )

            return build_empty_response(
                request=request,
                retrieval_mode="keyword_fallback_after_embedding_failure",
                explanation=(
                    "Gemini embedding retrieval failed and deterministic keyword "
                    "fallback found no strong local AMR target match."
                ),
            )

    keyword_targets = keyword_retrieve_targets(request, top_k=3)

    if keyword_targets:
        return TargetResolveResponse(
            disease=request.disease,
            pathogen=request.pathogen,
            resistance_mechanism=request.resistance_mechanism,
            retrieval_mode="keyword_fallback_no_gemini_key",
            resolved_targets=keyword_targets,
            explanation=(
                "GEMINI_API_KEY is not set. The resolver used deterministic "
                "keyword fallback over the local AMR target knowledge base."
            ),
            safety_note=SAFETY_NOTE,
        )

    return build_empty_response(
        request=request,
        retrieval_mode="keyword_fallback_no_gemini_key",
        explanation=(
            "GEMINI_API_KEY is not set and deterministic keyword fallback found "
            "no strong local AMR target match."
        ),
    )