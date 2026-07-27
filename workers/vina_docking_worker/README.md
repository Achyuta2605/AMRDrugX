# AMRDrugX AutoDock Vina Docking Worker

This worker runs a small CPU-focused AutoDock Vina docking job for AMRDrugX.

It is the current MVP docking backend because the earlier GNINA image was too large for practical Fargate extraction in the Day 19 test.

## Scope

This worker is intended for one-receptor, one-ligand docking tests.

It is not a full docking pipeline, not ADMET, not experimental validation, and not a clinical or therapeutic recommendation system.

## Required S3 Inputs

The backend writes an input JSON to S3 and passes its key to the worker.

The input JSON references:

- receptor PDB file in S3
- ligand SDF file in S3
- docking box center
- docking box size

Example:

```json
{
  "job_id": "manual-kpc-vina-test",
  "target_name": "KPC beta-lactamase",
  "target_uniprot_accession": "Q9F663",
  "receptor_pdb_s3_key": "docking_jobs/manual-kpc-vina-test/input/receptor.pdb",
  "ligand_name": "BindingDB monomer 50053173",
  "bindingdb_monomer_id": "50053173",
  "ligand_sdf_s3_key": "docking_jobs/manual-kpc-vina-test/input/ligand.sdf",
  "box_center": {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0
  },
  "box_size": {
    "x": 20.0,
    "y": 20.0,
    "z": 20.0
  },
  "docked_pose_s3_key": "docking_jobs/manual-kpc-vina-test/output/docked_pose.pdbqt"
}