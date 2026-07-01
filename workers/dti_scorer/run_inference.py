import hashlib
import json
import os
import sys
from typing import Any

import boto3


MODEL_BACKEND = "worker_baseline"
SCORE_TYPE = "non_biological_worker_test_score"
MODEL_NAME = "aws_worker_placeholder_not_biological"

SAFETY_NOTE = (
    "Worker scores are non-biological test scores only. They are not evidence "
    "of efficacy, binding, inhibition, or safety. Real DTI modeling, docking, "
    "ADMET analysis, literature review, and experimental validation are required."
)


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


def write_json_to_s3(
    client: Any,
    bucket: str,
    key: str,
    payload: dict[str, Any],
) -> None:
    print(f"Writing output to s3://{bucket}/{key}")

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
    )


def is_valid_smiles(smiles: str) -> bool:
    return bool(smiles and smiles.strip())


def baseline_score(protein_sequence: str, canonical_smiles: str) -> float:
    score_seed = f"{protein_sequence}|{canonical_smiles}"
    digest = hashlib.sha256(score_seed.encode("utf-8")).hexdigest()

    raw_value = int(digest[:8], 16)
    normalized_score = raw_value / 0xFFFFFFFF

    return round(normalized_score, 4)


def score_candidates(input_payload: dict[str, Any]) -> list[dict[str, Any]]:
    protein_sequence = input_payload.get("protein_sequence", "")
    candidates = input_payload.get("candidates", [])

    scored_candidates = []

    for candidate in candidates:
        smiles = candidate.get("canonical_smiles", "")

        if not is_valid_smiles(smiles):
            score = 0.0
            screening_note = (
                "Invalid or empty SMILES. Worker baseline score set to 0. "
                "This is not a biological prediction."
            )
        else:
            score = baseline_score(
                protein_sequence=protein_sequence,
                canonical_smiles=smiles,
            )
            screening_note = (
                "Worker baseline score for infrastructure testing only. "
                "This is not a biological DTI prediction."
            )

        scored_candidates.append(
            {
                "rank": 0,
                "compound_name": candidate.get("compound_name", "unknown"),
                "canonical_smiles": smiles,
                "source_database": candidate.get("source_database", "unknown"),
                "source_id": candidate.get("source_id", "unknown"),
                "source_url": candidate.get("source_url", "unknown"),
                "dti_score": score,
                "score_type": SCORE_TYPE,
                "model_name": MODEL_NAME,
                "screening_note": screening_note,
                "needs_docking_validation": True,
                "needs_admet_validation": True,
            }
        )

    ranked_candidates = sorted(
        scored_candidates,
        key=lambda item: item["dti_score"],
        reverse=True,
    )

    for index, candidate in enumerate(ranked_candidates, start=1):
        candidate["rank"] = index

    return ranked_candidates


def build_output_payload(input_payload: dict[str, Any]) -> dict[str, Any]:
    job_id = input_payload.get("job_id", os.getenv("JOB_ID", "unknown"))
    protein_sequence = input_payload.get("protein_sequence", "")
    candidates = input_payload.get("candidates", [])

    if not protein_sequence.strip():
        status = "failed_validation_missing_protein_sequence"
        ranked_candidates = []
    elif not candidates:
        status = "failed_validation_no_candidates"
        ranked_candidates = []
    else:
        status = "completed"
        ranked_candidates = score_candidates(input_payload)

    return {
        "job_id": job_id,
        "status": status,
        "model_backend": MODEL_BACKEND,
        "score_type": SCORE_TYPE,
        "ranked_candidates": ranked_candidates,
        "safety_note": SAFETY_NOTE,
    }


def main() -> int:
    try:
        aws_region = get_required_env("AWS_REGION")
        bucket = get_required_env("AMRDRUGX_SCREENING_BUCKET")
        job_id = get_required_env("JOB_ID")
        input_key = get_required_env("INPUT_KEY")
        output_key = get_required_env("OUTPUT_KEY")

        print("Starting AMRDrugX DTI worker")
        print(f"Job ID: {job_id}")
        print(f"AWS region: {aws_region}")
        print(f"Bucket: {bucket}")
        print(f"Input key: {input_key}")
        print(f"Output key: {output_key}")

        client = boto3.client("s3", region_name=aws_region)

        input_payload = read_json_from_s3(
            client=client,
            bucket=bucket,
            key=input_key,
        )

        if "job_id" not in input_payload:
            input_payload["job_id"] = job_id

        output_payload = build_output_payload(input_payload)

        write_json_to_s3(
            client=client,
            bucket=bucket,
            key=output_key,
            payload=output_payload,
        )

        print(f"Worker completed with status: {output_payload['status']}")
        return 0

    except Exception as exc:
        print(f"Worker failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())