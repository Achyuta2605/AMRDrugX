# AMRDrugX GNINA Docking Worker

This worker runs one GNINA docking job inside an AWS ECS/Fargate container.

It is separate from the DeepPurpose DTI worker.

## Purpose

The worker:

1. Reads a docking `input.json` file from S3.
2. Downloads a receptor PDB file from S3.
3. Downloads a ligand SDF file from S3.
4. Runs GNINA.
5. Uploads the docked ligand pose SDF to S3.
6. Writes `output.json` back to S3.

## Required Environment Variables

```text
AWS_REGION
AMRDRUGX_SCREENING_BUCKET
JOB_ID
INPUT_KEY
OUTPUT_KEY