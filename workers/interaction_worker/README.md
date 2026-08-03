# AMRDrugX PLIP Interaction Worker

This worker analyzes predicted protein-ligand interactions after docking.

It is intended to run after the AutoDock Vina worker has produced a docked pose file.

## Scope

Day 22 MVP:

- one receptor PDB
- one docked ligand pose
- one receptor-ligand complex file
- one interaction summary JSON

This worker does not run docking. It analyzes docking output.

## Required S3 Input

The backend writes an input JSON to S3 and passes its key to the worker.

Example:

```json
{
  "job_id": "manual-kpc-interaction-test",
  "docking_job_id": "manual-kpc-vina-p2rank-box-test",
  "target_name": "KPC beta-lactamase",
  "target_uniprot_accession": "Q9F663",
  "ligand_name": "BindingDB monomer 50053173",
  "bindingdb_monomer_id": "50053173",
  "receptor_pdb_s3_key": "docking_jobs/manual-kpc-gnina-test/input/receptor.pdb",
  "docked_pose_s3_key": "docking_jobs/manual-kpc-vina-p2rank-box-test/output/docked_pose.pdbqt"
}