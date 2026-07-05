import json
import os
import sys
from typing import Any

import boto3

from scorers import baseline_scorer, deeppurpose_scorer


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value


def read_json_from_s3(client: Any, bucket: str, key: str) -> dict[str, Any]:
    print(f"Reading input from s3://{bucket}/{key}")
    response = client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read().decode("utf-8")
    return json.loads(body)


def write_json_to_s3(client: Any, bucket: str, key: str, payload: dict[str, Any]) -> None:
    print(f"Writing output to s3://{bucket}/{key}")
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
    )


def run_scorer(
    backend: str,
    job_id: str,
    protein_sequence: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    if backend == "baseline":
        print("Using baseline scorer")
        return baseline_scorer.score(job_id, protein_sequence, candidates)

    if backend == "deeppurpose":
        print("Using DeepPurpose scorer")
        return deeppurpose_scorer.score(job_id, protein_sequence, candidates)

    raise RuntimeError(
        "Invalid DTI_SCORER_BACKEND. Expected 'baseline' or 'deeppurpose'."
    )


def main() -> int:
    try:
        aws_region = get_required_env("AWS_REGION")
        bucket = get_required_env("AMRDRUGX_SCREENING_BUCKET")
        job_id = get_required_env("JOB_ID")
        input_key = get_required_env("INPUT_KEY")
        output_key = get_required_env("OUTPUT_KEY")
        scorer_backend = os.getenv("DTI_SCORER_BACKEND", "baseline").strip().lower()

        print("Starting AMRDrugX DTI worker")
        print(f"Job ID: {job_id}")
        print(f"AWS region: {aws_region}")
        print(f"Bucket: {bucket}")
        print(f"Input key: {input_key}")
        print(f"Output key: {output_key}")
        print(f"DTI scorer backend: {scorer_backend}")

        client = boto3.client("s3", region_name=aws_region)

        input_payload = read_json_from_s3(client, bucket, input_key)

        protein_sequence = input_payload.get("protein_sequence", "")
        candidates = input_payload.get("candidates", [])

        output_payload = run_scorer(
            backend=scorer_backend,
            job_id=input_payload.get("job_id", job_id),
            protein_sequence=protein_sequence,
            candidates=candidates,
        )

        write_json_to_s3(client, bucket, output_key, output_payload)

        print(f"Worker completed with status: {output_payload['status']}")
        return 0

    except Exception as exc:
        print(f"Worker failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())