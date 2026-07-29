# AMRDrugX P2Rank Binding-Site Worker

This worker predicts likely ligand-binding pockets from a receptor PDB file using P2Rank.

It is used before AutoDock Vina so AMRDrugX can dock ligands into a predicted binding site instead of using placeholder box coordinates.

## Scope

This worker is for a small MVP binding-site prediction flow:

- one receptor structure
- one predicted top pocket
- one recommended docking box center
- one recommended docking box size

It does not run docking itself.

## Required S3 Input

The backend writes an input JSON to S3 and passes its key to the worker.

Example:

```json
{
  "job_id": "manual-kpc-p2rank-test",
  "target_name": "KPC beta-lactamase",
  "target_uniprot_accession": "Q9F663",
  "receptor_pdb_s3_key": "docking_jobs/manual-kpc-gnina-test/input/receptor.pdb"
}