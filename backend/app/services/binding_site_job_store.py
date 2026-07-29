import json
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError


def _get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise ValueError(f"Missing required environment variable: {name}")

    return value


def _get_bucket_name() -> str:
    return _get_required_env("AMRDRUGX_SCREENING_BUCKET")


def _get_s3_client() -> Any:
    aws_region = _get_required_env("AWS_REGION")
    return boto3.client("s3", region_name=aws_region)


def build_binding_site_input_key(job_id: str) -> str:
    return f"binding_site_jobs/{job_id}/input.json"


def build_binding_site_output_key(job_id: str) -> str:
    return f"binding_site_jobs/{job_id}/output.json"


def save_binding_site_input(job_id: str, payload: Dict[str, Any]) -> str:
    bucket = _get_bucket_name()
    key = build_binding_site_input_key(job_id)

    _get_s3_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    return key


def binding_site_output_exists(job_id: str) -> bool:
    bucket = _get_bucket_name()
    key = build_binding_site_output_key(job_id)

    try:
        _get_s3_client().head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            return False

        raise


def get_binding_site_output(job_id: str) -> Dict[str, Any]:
    bucket = _get_bucket_name()
    key = build_binding_site_output_key(job_id)

    response = _get_s3_client().get_object(Bucket=bucket, Key=key)
    body = response["Body"].read().decode("utf-8")

    return json.loads(body)