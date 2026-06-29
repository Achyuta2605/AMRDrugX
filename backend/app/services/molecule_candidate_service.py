from app.data.molecule_candidates import BETA_LACTAMASE_CANDIDATES
from app.schemas.molecule_screening import MoleculeCandidate


def normalize_text(value: str) -> str:
    return value.strip().lower()


def is_beta_lactamase_target(target_protein: str, target_family: str | None = None) -> bool:
    protein_text = normalize_text(target_protein)
    family_text = normalize_text(target_family or "")

    return "beta-lactamase" in protein_text or "beta-lactamase" in family_text


def get_candidates_for_target(
    target_protein: str,
    target_family: str | None = None,
) -> list[MoleculeCandidate]:
    if is_beta_lactamase_target(
        target_protein=target_protein,
        target_family=target_family,
    ):
        return [
            MoleculeCandidate(**candidate)
            for candidate in BETA_LACTAMASE_CANDIDATES
        ]

    return []