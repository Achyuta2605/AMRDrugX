from app.schemas.target import TargetResolveRequest, TargetResolveResponse


def normalize_text(value: str) -> str:
    return value.strip().lower()


def resolve_target(request: TargetResolveRequest) -> TargetResolveResponse:
    pathogen = normalize_text(request.pathogen)
    antibiotic = normalize_text(request.antibiotic)
    mechanism = normalize_text(request.resistance_mechanism)

    is_mock_kpc2_case = (
        pathogen == "klebsiella pneumoniae"
        and antibiotic == "meropenem"
        and mechanism == "carbapenem resistance"
    )

    if is_mock_kpc2_case:
        return TargetResolveResponse(
            pathogen=request.pathogen,
            antibiotic=request.antibiotic,
            resistance_mechanism=request.resistance_mechanism,
            resolved_target_name="KPC-2 beta-lactamase",
            target_type="carbapenemase enzyme",
            organism="Klebsiella pneumoniae",
            confidence="mock-high",
            evidence_source="static Day 1 mock resolver",
            explanation=(
                "KPC-2 beta-lactamase is a carbapenemase associated with "
                "carbapenem resistance in Klebsiella pneumoniae. In this Day 1 "
                "prototype, the resolver returns this target from a static mock rule."
            ),
            safety_note=(
                "Computational prediction only. Not medical advice. "
                "Requires wet-lab validation."
            ),
        )

    return TargetResolveResponse(
        pathogen=request.pathogen,
        antibiotic=request.antibiotic,
        resistance_mechanism=request.resistance_mechanism,
        resolved_target_name="unknown",
        target_type="unknown",
        organism=request.pathogen,
        confidence="none",
        evidence_source="static Day 1 mock resolver",
        explanation=(
            "No static mock target is available for this input yet. "
            "Future versions will use curated resistance databases and protein APIs."
        ),
        safety_note=(
            "Computational prediction only. Not medical advice. "
            "Requires wet-lab validation."
        ),
    )