import json
from pathlib import Path


class LocalScreeningJobStore:
    backend_name = "local"

    def __init__(self) -> None:
        self.base_path = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "screening_jobs"
        )

    def build_job_dir(self, job_id: str) -> Path:
        return self.base_path / job_id

    def build_input_path(self, job_id: str) -> Path:
        return self.build_job_dir(job_id) / "input.json"

    def build_output_path(self, job_id: str) -> Path:
        return self.build_job_dir(job_id) / "output.json"

    def save_json(self, path: Path, payload: dict) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)

        return str(path)

    def read_json(self, path: Path) -> dict:
        if not path.exists():
            raise RuntimeError(f"Local screening job file not found: {path}")

        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save_input(self, job_id: str, payload: dict) -> str:
        return self.save_json(self.build_input_path(job_id), payload)

    def save_output(self, job_id: str, payload: dict) -> str:
        return self.save_json(self.build_output_path(job_id), payload)

    def get_input(self, job_id: str) -> dict:
        return self.read_json(self.build_input_path(job_id))

    def get_output(self, job_id: str) -> dict:
        return self.read_json(self.build_output_path(job_id))

    def output_exists(self, job_id: str) -> bool:
        return self.build_output_path(job_id).exists()