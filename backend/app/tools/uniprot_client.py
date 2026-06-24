"""
Placeholder UniProt client.

Future versions of AMRDrugX may use UniProt to retrieve protein metadata
for resolved resistance targets, including protein names, organisms,
accession identifiers, sequences, and functional annotations.

This file intentionally does not make external API calls on Day 2.

Expected future responsibilities:
- search proteins by gene or target name
- retrieve UniProt accession IDs
- fetch protein metadata and sequence information
- connect resolved targets to PDB or AlphaFold structure lookup
"""


def search_uniprot_proteins() -> None:
    raise NotImplementedError(
        "UniProt integration is planned for a future phase. "
        "Day 2 uses a deterministic local knowledge base only."
    )