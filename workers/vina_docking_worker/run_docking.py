import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import boto3


WORK_DIR = Path("/tmp/amrdrugx_vina")
INPUT_FILENAME = "input.json"
RECEPTOR_PDB_FILENAME = "receptor.pdb"
RECEPTOR_PDBQT_FILENAME = "receptor.pdbqt"
LIGAND_INPUT_FILENAME = "ligand.sdf"
LIGAND_PDBQT_FILENAME = "ligand.pdbqt"
DOCKED_POSE_PDBQT_FILENAME = "docked_pose.pdbqt"
VINA_LOG_FILENAME = "vina.log"

LIMITATION_NOTE = (
    "Computational docking result only. Not experimental or clinical validation."
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


def download_s3_file(client: Any, bucket: str, key: str, local_path: Path) -> None:
    print(f"Downloading s3://{bucket}/{key} to {local_path}")
    client.download_file(bucket, key, str(local_path))


def upload_s3_file(client: Any, bucket: str, key: str, local_path: Path) -> None:
    print(f"Uploading {local_path} to s3://{bucket}/{key}")
    client.upload_file(str(local_path), bucket, key)


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


def run_command(command: list) -> str:
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


def prepare_receptor(receptor_pdb_path: Path, receptor_pdbqt_path: Path) -> None:
    run_command(
        [
            "obabel",
            str(receptor_pdb_path),
            "-O",
            str(receptor_pdbqt_path),
            "-xr",
        ]
    )


def prepare_ligand(ligand_input_path: Path, ligand_pdbqt_path: Path) -> None:
    run_command(
        [
            "obabel",
            str(ligand_input_path),
            "-O",
            str(ligand_pdbqt_path),
            "--gen3d",
        ]
    )


def parse_best_affinity(vina_output: str) -> Optional[float]:
    for line in vina_output.splitlines():
        match = re.match(r"\s*1\s+(-?\d+(?:\.\d+)?)\s+", line)
        if match:
            return float(match.group(1))

    return None


def run_vina(
    receptor_pdbqt_path: Path,
    ligand_pdbqt_path: Path,
    docked_pose_path: Path,
    box_center: Dict[str, float],
    box_size: Dict[str, float],
) -> str:
    command = [
        "vina",
        "--receptor",
        str(receptor_pdbqt_path),
        "--ligand",
        str(ligand_pdbqt_path),
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

    return run_command(command)


def build_output_payload(
    input_payload: Dict[str, Any],
    output_key: str,
    docked_pose_s3_key: str,
    best_affinity: Optional[float],
) -> Dict[str, Any]:
    return {
        "job_id": input_payload["job_id"],
        "target_name": input_payload["target_name"],
        "target_uniprot_accession": input_payload["target_uniprot_accession"],
        "ligand_name": input_payload["ligand_name"],
        "bindingdb_monomer_id": input_payload.get("bindingdb_monomer_id"),
        "docking_backend": "autodock_vina",
        "docking_status": "completed",
        "best_affinity_kcal_mol": best_affinity,
        "receptor_pdb_s3_key": input_payload["receptor_pdb_s3_key"],
        "ligand_input_s3_key": input_payload["ligand_sdf_s3_key"],
        "docked_pose_s3_key": docked_pose_s3_key,
        "output_s3_key": output_key,
        "viewer_url": f"/api/docking/jobs/{input_payload['job_id']}/view",
        "limitation_note": LIMITATION_NOTE,
    }


def main() -> int:
    try:
        aws_region = get_required_env("AWS_REGION")
        bucket = get_required_env("AMRDRUGX_SCREENING_BUCKET")
        input_key = get_required_env("INPUT_KEY")
        output_key = get_required_env("OUTPUT_KEY")

        print("Starting AMRDrugX AutoDock Vina docking worker")
        print(f"AWS region: {aws_region}")
        print(f"Bucket: {bucket}")
        print(f"Input key: {input_key}")
        print(f"Output key: {output_key}")

        WORK_DIR.mkdir(parents=True, exist_ok=True)

        client = boto3.client("s3", region_name=aws_region)

        input_payload = read_json_from_s3(client, bucket, input_key)

        receptor_pdb_path = WORK_DIR / RECEPTOR_PDB_FILENAME
        receptor_pdbqt_path = WORK_DIR / RECEPTOR_PDBQT_FILENAME
        ligand_input_path = WORK_DIR / LIGAND_INPUT_FILENAME
        ligand_pdbqt_path = WORK_DIR / LIGAND_PDBQT_FILENAME
        docked_pose_path = WORK_DIR / DOCKED_POSE_PDBQT_FILENAME
        # vina_log_path = WORK_DIR / VINA_LOG_FILENAME

        download_s3_file(
            client,
            bucket,
            input_payload["receptor_pdb_s3_key"],
            receptor_pdb_path,
        )
        download_s3_file(
            client,
            bucket,
            input_payload["ligand_sdf_s3_key"],
            ligand_input_path,
        )

        prepare_receptor(receptor_pdb_path, receptor_pdbqt_path)
        prepare_ligand(ligand_input_path, ligand_pdbqt_path)

        vina_output = run_vina(
            receptor_pdbqt_path=receptor_pdbqt_path,
            ligand_pdbqt_path=ligand_pdbqt_path,
            docked_pose_path=docked_pose_path,
            box_center=input_payload["box_center"],
            box_size=input_payload["box_size"],
        )

        best_affinity = parse_best_affinity(vina_output)

        docked_pose_s3_key = input_payload.get(
            "docked_pose_s3_key",
            f"docking_jobs/{input_payload['job_id']}/output/docked_pose.pdbqt",
        )

        upload_s3_file(client, bucket, docked_pose_s3_key, docked_pose_path)

        output_payload = build_output_payload(
            input_payload=input_payload,
            output_key=output_key,
            docked_pose_s3_key=docked_pose_s3_key,
            best_affinity=best_affinity,
        )

        write_json_to_s3(client, bucket, output_key, output_payload)

        print("Vina docking worker completed successfully")
        return 0

    except Exception as exc:
        print(f"Vina docking worker failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())