import hashlib

from app.schemas.molecule_screening import MoleculeCandidate, ScoredMoleculeCandidate


MODEL_BACKEND = "baseline_local"
SCORE_TYPE = "non_biological_baseline_score"


def is_valid_smiles(smiles: str) -> bool:
    return bool(smiles and smiles.strip())


def deterministic_baseline_score(
    protein_sequence: str,
    canonical_smiles: str,
) -> float:
    score_seed = f"{protein_sequence}|{canonical_smiles}"
    digest = hashlib.sha256(score_seed.encode("utf-8")).hexdigest()

    raw_value = int(digest[:8], 16)
    normalized_score = raw_value / 0xFFFFFFFF

    return round(normalized_score, 4)


def score_molecules_against_target(
    protein_sequence: str,
    candidates: list[MoleculeCandidate],
) -> tuple[list[ScoredMoleculeCandidate], str]:
    scored_candidates = []

    for candidate in candidates:
        if not is_valid_smiles(candidate.canonical_smiles):
            score = 0.0
            screening_note = (
                "Invalid or empty SMILES. Baseline score set to 0. "
                "This is not a biological prediction."
            )
        else:
            score = deterministic_baseline_score(
                protein_sequence=protein_sequence,
                canonical_smiles=candidate.canonical_smiles,
            )
            screening_note = (
                "Deterministic local baseline score for API and storage testing only. "
                "This is not a biological DTI prediction."
            )

        scored_candidates.append(
            ScoredMoleculeCandidate(
                rank=0,
                compound_name=candidate.compound_name,
                canonical_smiles=candidate.canonical_smiles,
                source_database=candidate.source_database,
                source_id=candidate.source_id,
                source_url=candidate.source_url,
                dti_score=score,
                score_type=SCORE_TYPE,
                model_name=MODEL_BACKEND,
                screening_note=screening_note,
                needs_docking_validation=True,
                needs_admet_validation=True,
            )
        )

    return scored_candidates, MODEL_BACKEND