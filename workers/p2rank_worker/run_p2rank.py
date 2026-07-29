import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3


WORK_DIR = Path("/tmp/amrdrugx_p2rank")
RECEPTOR_FILENAME = "receptor.pdb"
OUTPUT_DIR = WORK_DIR / "p2rank_output"

RECOMMENDED_BOX_SIZE = {
    "x": 20.0,
    "y": 20.0,
    "z": 20.0,
}

LIMITATION_NOTE = (
    "Binding-site prediction is computational only and requires docking, "
    "literature review, and experimental validation."
)


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def read_json_from_s3(client: Any, bucket: str, key: str) -> Dict[str, Any]:
    print(f"Reading P2Rank input from s3://{bucket}/{key}")
    response = client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read().decode("utf-8")
    return json.loads(body)


def download_s3_file(client: Any, bucket: str, key: str, local_path: Path) -> None:
    print(f"Downloading s3://{bucket}/{key} to {local_path}")
    client.download_file(bucket, key, str(local_path))


def write_json_to_s3(
    client: Any,
    bucket: str,
    key: str,
    payload: Dict[str, Any],
) -> None:
    print(f"Writing P2Rank output to s3://{bucket}/{key}")
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
    )


def run_command(command: List[str]) -> str:
    print("Running command:", " ".join(command))
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.stdout:
        print(completed.stdout)

    if completed.stderr:
        print(completed.stderr, file=sys.stderr)

    if completed.returncode != 0:
        raise RuntimeError(
            "Command failed with exit code "
            f"{completed.returncode}: {' '.join(command)}"
        )

    return completed.stdout


def run_p2rank(receptor_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    run_command(
        [
            "prank",
            "predict",
            "-f",
            str(receptor_path),
            "-o",
            str(output_dir),
        ]
    )


def find_prediction_csv(output_dir: Path) -> Path:
    csv_files = list(output_dir.rglob("*_predictions.csv"))

    if not csv_files:
        raise RuntimeError("P2Rank did not produce a *_predictions.csv file.")

    return csv_files[0]


def parse_float(row: Dict[str, str], names: List[str]) -> Optional[float]:
    for name in names:
        value = row.get(name)
        if value is None or value == "":
            continue

        try:
            return float(value)
        except ValueError:
            continue

    return None


def parse_top_pocket(output_dir: Path) -> Dict[str, Any]:
    prediction_csv = find_prediction_csv(output_dir)

    print(f"Parsing P2Rank predictions from {prediction_csv}")

    with prediction_csv.open("r", encoding="utf-8", newline="") as file_obj:
        reader = csv.DictReader(file_obj)

        rows = list(reader)

    if not rows:
        raise RuntimeError("P2Rank predictions CSV is empty.")

    top_row = rows[0]

    score = parse_float(top_row, ["score", "Score"])
    probability = parse_float(top_row, ["probability", "Probability", "prob"])

    center_x = parse_float(top_row, ["center_x", "x", "Center X"])
    center_y = parse_float(top_row, ["center_y", "y", "Center Y"])
    center_z = parse_float(top_row, ["center_z", "z", "Center Z"])

    if center_x is None or center_y is None or center_z is None:
        raise RuntimeError(
            "P2Rank top pocket is missing center coordinates in predictions CSV."
        )

    return {
        "rank": 1,
        "score": score,
        "probability": probability,
        "center": {
            "x": round(center_x, 4),
            "y": round(center_y, 4),
            "z": round(center_z, 4),
        },
    }


def build_output_payload(
    input_payload: Dict[str, Any],
    output_key: str,
    top_pocket: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "job_id": input_payload["job_id"],
        "target_name": input_payload["target_name"],
        "target_uniprot_accession": input_payload["target_uniprot_accession"],
        "receptor_pdb_s3_key": input_payload["receptor_pdb_s3_key"],
        "binding_site_backend": "p2rank",
        "status": "completed",
        "top_pocket": top_pocket,
        "recommended_box_center": top_pocket["center"],
        "recommended_box_size": RECOMMENDED_BOX_SIZE,
        "output_s3_key": output_key,
        "next_pipeline_step": "run_vina_docking_with_predicted_box",
        "limitation_note": LIMITATION_NOTE,
    }


def main() -> int:
    try:
        aws_region = get_required_env("AWS_REGION")
        bucket = get_required_env("AMRDRUGX_SCREENING_BUCKET")
        input_key = get_required_env("INPUT_KEY")
        output_key = get_required_env("OUTPUT_KEY")

        print("Starting AMRDrugX P2Rank binding-site worker")
        print(f"AWS region: {aws_region}")
        print(f"Bucket: {bucket}")
        print(f"Input key: {input_key}")
        print(f"Output key: {output_key}")

        WORK_DIR.mkdir(parents=True, exist_ok=True)

        client = boto3.client("s3", region_name=aws_region)

        input_payload = read_json_from_s3(client, bucket, input_key)

        receptor_path = WORK_DIR / RECEPTOR_FILENAME

        download_s3_file(
            client,
            bucket,
            input_payload["receptor_pdb_s3_key"],
            receptor_path,
        )

        run_p2rank(receptor_path, OUTPUT_DIR)

        top_pocket = parse_top_pocket(OUTPUT_DIR)

        output_payload = build_output_payload(
            input_payload=input_payload,
            output_key=output_key,
            top_pocket=top_pocket,
        )

        write_json_to_s3(client, bucket, output_key, output_payload)

        print("P2Rank binding-site worker completed successfully")
        return 0

    except Exception as exc:
        print(f"P2Rank binding-site worker failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())