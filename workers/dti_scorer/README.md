# AMRDrugX DTI Scorer Worker

This folder contains the scaffold for a future AWS Fargate worker that will run DTI scoring jobs.

The worker is designed to:

1. Read a screening job input JSON file from S3.
2. Run molecule scoring.
3. Write an output JSON file back to S3.

## Current Status

The current scorer is a non-biological baseline scorer.

It is only for testing:

- container execution flow
- S3 input/output contract
- job orchestration design
- future AWS Fargate readiness

It is not a real DTI model.

It does not predict binding, inhibition, efficacy, or safety.

## Required Environment Variables

The worker expects:

```text
AWS_REGION
AMRDRUGX_SCREENING_BUCKET
JOB_ID
INPUT_KEY
OUTPUT_KEY