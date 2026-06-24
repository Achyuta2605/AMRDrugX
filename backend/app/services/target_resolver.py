from app.data.target_knowledge_base import TARGET_KNOWLEDGE_BASE
from app.schemas.target import TargetResolveRequest, TargetResolveResponse


SAFETY_NOTE = (
    "Computational prediction only. Not medical advice. "
    "Requires wet-lab validation."
)


def normalize_text(value: str) -> str:
    return value.strip().lower()


def is_matching_record(
    request: TargetResolveRequest,
    record: dict[str, str],
) -> bool:
    return (
        normalize_text(request.pathogen) == normalize_text(record["pathogen"])
        and normalize_text(request.antibiotic) == normalize_text(record["antibiotic"])
        and normalize_text(request.resistance_mechanism)
        == normalize_text(record["resistance_mechanism"])
    )


def build_known_target_response(
    request: TargetResolveRequest,
    record: dict[str, str],
) -> TargetResolveResponse:
    return TargetResolveResponse(
        pathogen=request.pathogen,
        antibiotic=request.antibiotic,
        resistance_mechanism=request.resistance_mechanism,
        gene=record["gene"],
        resolved_target_name=record["resolved_target_name"],
        target_type=record["target_type"],
        target_family=record["target_family"],
        mechanism_category=record["mechanism_category"],
        organism=record["pathogen"],
        confidence="local-kb-match",
        evidence_source=record["evidence_source"],
        explanation=record["explanation"],
        next_pipeline_step=(
            "Use the resolved resistance target to retrieve candidate inhibitor "
            "molecules in the next pipeline stage."
        ),
        safety_note=SAFETY_NOTE,
    )


def build_unknown_target_response(
    request: TargetResolveRequest,
) -> TargetResolveResponse:
    return TargetResolveResponse(
        pathogen=request.pathogen,
        antibiotic=request.antibiotic,
        resistance_mechanism=request.resistance_mechanism,
        gene="unknown",
        resolved_target_name="unknown",
        target_type="unknown",
        target_family="unknown",
        mechanism_category="unknown",
        organism=request.pathogen,
        confidence="none",
        evidence_source="local curated AMR target knowledge base",
        explanation=(
            "No deterministic local knowledge base match was found for this input. "
            "Future versions will query curated AMR databases and protein resources "
            "such as CARD, UniProt, PDB, and AlphaFold."
        ),
        next_pipeline_step=(
            "Do not run molecule screening until a resistance target is resolved "
            "with sufficient evidence."
        ),
        safety_note=SAFETY_NOTE,
    )


def resolve_target(request: TargetResolveRequest) -> TargetResolveResponse:
    for record in TARGET_KNOWLEDGE_BASE:
        if is_matching_record(request, record):
            return build_known_target_response(request, record)

    return build_unknown_target_response(request)