"""
Placeholder CARD client.

Future versions of AMRDrugX may use CARD (Comprehensive Antibiotic
Resistance Database) to retrieve evidence-backed antimicrobial resistance
genes, mechanisms, ontology terms, and associated resistance targets.

This file intentionally does not make external API calls on Day 2.

Expected future responsibilities:
- search resistance genes by pathogen and mechanism
- retrieve resistance mechanism metadata
- normalize CARD records into AMRDrugX target records
- provide evidence sources for resolver output
"""


def search_card_targets() -> None:
    raise NotImplementedError(
        "CARD integration is planned for a future phase. "
        "Day 2 uses a deterministic local knowledge base only."
    )