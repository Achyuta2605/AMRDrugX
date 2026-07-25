import json
import os
from typing import Any, Dict

import boto3


DOCKING_JOBS_PREFIX = "docking_jobs"


def _get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise ValueError(f"Missing required environment variable: {name}")

    return value


def build_docking_input_key(job_id: str) -> str:
    return f"{DOCKING_JOBS_PREFIX}/{job_id}/input.json"


def build_docking_output_key(job_id: str) -> str:
    return f"{DOCKING_JOBS_PREFIX}/{job_id}/output.json"


def build_docked_pose_key(job_id: str) -> str:
    return f"{DOCKING_JOBS_PREFIX}/{job_id}/output/docked_pose.sdf"


def save_docking_input(job_id: str, payload: Dict[str, Any]) -> str:
    bucket = _get_required_env("AMRDRUGX_SCREENING_BUCKET")
    region = _get_required_env("AWS_REGION")
    key = build_docking_input_key(job_id)

    client = boto3.client("s3", region_name=region)
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    return key


def get_docking_output(job_id: str) -> Dict[str, Any]:
    bucket = _get_required_env("AMRDRUGX_SCREENING_BUCKET")
    region = _get_required_env("AWS_REGION")
    key = build_docking_output_key(job_id)

    client = boto3.client("s3", region_name=region)
    response = client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read().decode("utf-8")

    return json.loads(body)


def docking_output_exists(job_id: str) -> bool:
    bucket = _get_required_env("AMRDRUGX_SCREENING_BUCKET")
    region = _get_required_env("AWS_REGION")
    key = build_docking_output_key(job_id)

    client = boto3.client("s3", region_name=region)

    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except client.exceptions.ClientError:
        return False


def build_s3_uri(key: str) -> str:
    bucket = _get_required_env("AMRDRUGX_SCREENING_BUCKET")
    return f"s3://{bucket}/{key}"


def create_presigned_s3_url(key: str, expires_in: int = 3600) -> str:
    bucket = _get_required_env("AMRDRUGX_SCREENING_BUCKET")
    region = _get_required_env("AWS_REGION")

    client = boto3.client("s3", region_name=region)

    return client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ExpiresIn=expires_in,
    )