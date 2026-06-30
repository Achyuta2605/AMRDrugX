import json
import os
from typing import Any


class S3ScreeningJobStore:
    backend_name = "s3"

    def __init__(self) -> None:
        self.bucket = os.getenv("AMRDRUGX_SCREENING_BUCKET")
        self.region = os.getenv("AWS_REGION", "ap-southeast-2")

        if not self.bucket:
            raise RuntimeError(
                "AMRDRUGX_SCREENING_BUCKET is not set. "
                "Set it before using SCREENING_STORAGE_BACKEND=s3."
            )

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError as exc:
            raise RuntimeError(
                "boto3 is not installed. Run 'pip install -r requirements.txt'."
            ) from exc

        self.boto3 = boto3
        self.BotoCoreError = BotoCoreError
        self.ClientError = ClientError
        self.client = boto3.client("s3", region_name=self.region)

    def input_key(self, job_id: str) -> str:
        return f"screening_jobs/{job_id}/input.json"

    def output_key(self, job_id: str) -> str:
        return f"screening_jobs/{job_id}/output.json"

    def s3_location(self, key: str) -> str:
        return f"s3://{self.bucket}/{key}"

    def put_json(self, key: str, payload: dict[str, Any]) -> str:
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(payload, indent=2).encode("utf-8"),
                ContentType="application/json",
            )
        except (self.BotoCoreError, self.ClientError) as exc:
            raise RuntimeError(f"Failed to save S3 object {key}: {exc}") from exc

        return self.s3_location(key)

    def get_json(self, key: str) -> dict:
        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=key,
            )
            body = response["Body"].read().decode("utf-8")
            return json.loads(body)
        except (self.BotoCoreError, self.ClientError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Failed to read S3 object {key}: {exc}") from exc

    def save_input(self, job_id: str, payload: dict) -> str:
        return self.put_json(self.input_key(job_id), payload)

    def save_output(self, job_id: str, payload: dict) -> str:
        return self.put_json(self.output_key(job_id), payload)

    def get_input(self, job_id: str) -> dict:
        return self.get_json(self.input_key(job_id))

    def get_output(self, job_id: str) -> dict:
        return self.get_json(self.output_key(job_id))

    def output_exists(self, job_id: str) -> bool:
        key = self.output_key(job_id)

        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=key,
            )
            return True
        except self.ClientError:
            return False
        except self.BotoCoreError as exc:
            raise RuntimeError(f"Failed to check S3 object {key}: {exc}") from exc