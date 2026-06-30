import os
from typing import Protocol


class ScreeningJobStore(Protocol):
    backend_name: str

    def save_input(self, job_id: str, payload: dict) -> str:
        ...

    def save_output(self, job_id: str, payload: dict) -> str:
        ...

    def get_input(self, job_id: str) -> dict:
        ...

    def get_output(self, job_id: str) -> dict:
        ...

    def output_exists(self, job_id: str) -> bool:
        ...


def get_screening_storage_backend_name() -> str:
    return os.getenv("SCREENING_STORAGE_BACKEND", "local").strip().lower()


def get_screening_job_store() -> ScreeningJobStore:
    backend = get_screening_storage_backend_name()

    if backend == "s3":
        from app.services.s3_screening_job_store import S3ScreeningJobStore

        return S3ScreeningJobStore()

    if backend == "local":
        from app.services.local_screening_job_store import LocalScreeningJobStore

        return LocalScreeningJobStore()

    raise RuntimeError(
        "Invalid SCREENING_STORAGE_BACKEND. Expected 'local' or 's3'."
    )