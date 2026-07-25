import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import boto3


WORK_DIR = Path("/tmp/amrdrugx_docking")
RECEPTOR_FILENAME = "receptor.pdb"
LIGAND_FILENAME = "ligand.sdf"
DOCKED_POSE_FILENAME = "docked_pose.sdf"

LIMITATION_NOTE = (
    "Computational docking result only. Not experimental validation. Docking quality "
    "depends on receptor preparation, ligand preparation, binding box choice, and scoring limitations."
)


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value


def read_json_from_s3(client: Any, bucket: str, key: str) -> Dict[str, Any]:
    print(f"Reading docking input from s3://{bucket}/{key}")
    response = client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read().decode("utf-8")
    return json.loads(body)


def write_json_to_s3(
    client: Any,
    bucket: str,
    key: str,
    payload: Dict[str, Any],
) -> None:
    print(f"Writing docking output to s3://{bucket}/{key}")
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
    )


def download_s3_file(client: Any, bucket: str, key: str, local_path: Path) -> None:
    print(f"Downloading s3://{bucket}/{key} to {local_path}")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(bucket, key, str(local_path))


def upload_s3_file(client: Any, bucket: str, key: str, local_path: Path) -> None:
    print(f"Uploading {local_path} to s3://{bucket}/{key}")
    client.upload_file(str(local_path), bucket, key)


def parse_gnina_output(text: str) -> Dict[str, Optional[float]]:
    parsed = {
        "docking_score": None,
        "cnn_score": None,
        "cnn_affinity": None,
    }

    affinity_match = re.search(r"Affinity:\s*([-+]?\d*\.?\d+)", text)
    cnn_score_match = re.search(r"CNNscore:\s*([-+]?\d*\.?\d+)", text)
    cnn_affinity_match = re.search(r"CNNaffinity:\s*([-+]?\d*\.?\d+)", text)

    if affinity_match:
        parsed["docking_score"] = float(affinity_match.group(1))

    if cnn_score_match:
        parsed["cnn_score"] = float(cnn_score_match.group(1))

    if cnn_affinity_match:
        parsed["cnn_affinity"] = float(cnn_affinity_match.group(1))

    return parsed


def run_gnina(input_payload: Dict[str, Any]) -> Dict[str, Optional[float]]:
    receptor_path = WORK_DIR / RECEPTOR_FILENAME
    ligand_path = WORK_DIR / LIGAND_FILENAME
    docked_pose_path = WORK_DIR / DOCKED_POSE_FILENAME

    box_center = input_payload["box_center"]
    box_size = input_payload["box_size"]

    command = [
        "gnina",
        "--receptor",
        str(receptor_path),
        "--ligand",
        str(ligand_path),
        "--center_x",
        str(box_center["x"]),
        "--center_y",
        str(box_center["y"]),
        "--center_z",
        str(box_center["z"]),
        "--size_x",
        str(box_size["x"]),
        "--size_y",
        str(box_size["y"]),
        "--size_z",
        str(box_size["z"]),
        "--out",
        str(docked_pose_path),
    ]

    print("Running GNINA docking command")
    print(" ".join(command))

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )

    print("GNINA stdout:")
    print(completed.stdout)

    print("GNINA stderr:")
    print(completed.stderr)

    if completed.returncode != 0:
        raise RuntimeError(
            "GNINA failed with exit code "
            f"{completed.returncode}: {completed.stderr}"
        )

    if not docked_pose_path.exists():
        raise RuntimeError("GNINA completed but docked_pose.sdf was not created.")

    return parse_gnina_output(completed.stdout + "\n" + completed.stderr)


def build_output_payload(
    input_payload: Dict[str, Any],
    docked_pose_sdf_s3_key: str,
    parsed_scores: Dict[str, Optional[float]],
) -> Dict[str, Any]:
    return {
        "job_id": input_payload["job_id"],
        "target_name": input_payload["target_name"],
        "target_uniprot_accession": input_payload["target_uniprot_accession"],
        "ligand_name": input_payload["ligand_name"],
        "bindingdb_monomer_id": input_payload.get("bindingdb_monomer_id"),
        "docking_backend": "gnina",
        "docking_status": "completed",
        "docking_score": parsed_scores.get("docking_score"),
        "cnn_score": parsed_scores.get("cnn_score"),
        "cnn_affinity": parsed_scores.get("cnn_affinity"),
        "receptor_pdb_s3_key": input_payload["receptor_pdb_s3_key"],
        "ligand_sdf_s3_key": input_payload["ligand_sdf_s3_key"],
        "docked_pose_sdf_s3_key": docked_pose_sdf_s3_key,
        "limitation_note": LIMITATION_NOTE,
    }


def main() -> int:
    try:
        aws_region = get_required_env("AWS_REGION")
        bucket = get_required_env("AMRDRUGX_SCREENING_BUCKET")
        job_id = get_required_env("JOB_ID")
        input_key = get_required_env("INPUT_KEY")
        output_key = get_required_env("OUTPUT_KEY")

        WORK_DIR.mkdir(parents=True, exist_ok=True)

        client = boto3.client("s3", region_name=aws_region)

        input_payload = read_json_from_s3(client, bucket, input_key)
        input_payload["job_id"] = input_payload.get("job_id") or job_id

        receptor_path = WORK_DIR / RECEPTOR_FILENAME
        ligand_path = WORK_DIR / LIGAND_FILENAME
        docked_pose_path = WORK_DIR / DOCKED_POSE_FILENAME

        download_s3_file(
            client,
            bucket,
            input_payload["receptor_pdb_s3_key"],
            receptor_path,
        )
        download_s3_file(
            client,
            bucket,
            input_payload["ligand_sdf_s3_key"],
            ligand_path,
        )

        parsed_scores = run_gnina(input_payload)

        docked_pose_sdf_s3_key = input_payload["docked_pose_sdf_s3_key"]
        upload_s3_file(
            client,
            bucket,
            docked_pose_sdf_s3_key,
            docked_pose_path,
        )

        output_payload = build_output_payload(
            input_payload=input_payload,
            docked_pose_sdf_s3_key=docked_pose_sdf_s3_key,
            parsed_scores=parsed_scores,
        )

        write_json_to_s3(client, bucket, output_key, output_payload)

        print("Docking worker completed successfully")
        return 0

    except Exception as exc:
        print(f"Docking worker failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())