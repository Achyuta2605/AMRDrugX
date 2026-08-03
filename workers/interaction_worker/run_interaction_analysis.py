import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3


WORK_DIR = Path("/tmp/amrdrugx_interactions")
RECEPTOR_PDB_FILENAME = "receptor.pdb"
DOCKED_POSE_PDBQT_FILENAME = "docked_pose.pdbqt"
LIGAND_PDB_FILENAME = "ligand.pdb"
COMPLEX_PDB_FILENAME = "complex.pdb"
PLIP_OUTPUT_DIR = WORK_DIR / "plip_output"

LIMITATION_NOTE = (
    "Computational interaction analysis only. Not experimental validation."
)


INTERACTION_COUNT_KEYS = {
    "hydrophobic_interactions": "hydrophobic_contact_count",
    "hydrogen_bonds": "hydrogen_bond_count",
    "salt_bridges": "salt_bridge_count",
    "pi_stacks": "pi_stacking_count",
}


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def read_json_from_s3(client: Any, bucket: str, key: str) -> Dict[str, Any]:
    print(f"Reading interaction input from s3://{bucket}/{key}")
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
    print(f"Writing interaction output to s3://{bucket}/{key}")
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


def convert_pdbqt_to_pdb(pdbqt_path: Path, pdb_path: Path) -> None:
    run_command(
        [
            "obabel",
            str(pdbqt_path),
            "-O",
            str(pdb_path),
        ]
    )


def build_complex_pdb(
    receptor_pdb_path: Path,
    ligand_pdb_path: Path,
    complex_pdb_path: Path,
) -> None:
    receptor_lines = receptor_pdb_path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).splitlines()

    ligand_lines = ligand_pdb_path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).splitlines()

    output_lines = []

    for line in receptor_lines:
        if line.startswith(("ATOM", "HETATM", "TER")):
            output_lines.append(line)

    output_lines.append("TER")

    for line in ligand_lines:
        if line.startswith(("ATOM", "HETATM")):
            ligand_line = line[:17] + "LIG" + line[20:]
            output_lines.append(ligand_line)

    output_lines.append("END")

    complex_pdb_path.write_text(
        "\n".join(output_lines) + "\n",
        encoding="utf-8",
    )


def run_plip(complex_pdb_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    run_command(
        [
            "plip",
            "-f",
            str(complex_pdb_path),
            "-o",
            str(output_dir),
            "-x",
        ]
    )


def find_plip_xml(output_dir: Path) -> Optional[Path]:
    xml_files = list(output_dir.rglob("*.xml"))

    if not xml_files:
        return None

    return xml_files[0]


def count_xml_tags(xml_text: str, tag_name: str) -> int:
    return len(re.findall(fr"<{tag_name}\b", xml_text))


def parse_plip_summary(output_dir: Path) -> Dict[str, Any]:
    xml_path = find_plip_xml(output_dir)

    if xml_path is None:
        return {
            "summary": {
                "hydrogen_bond_count": 0,
                "hydrophobic_contact_count": 0,
                "salt_bridge_count": 0,
                "pi_stacking_count": 0,
                "total_interactions": 0,
            },
            "interactions": [],
            "parser_note": "PLIP XML output was not found.",
        }

    xml_text = xml_path.read_text(encoding="utf-8", errors="ignore")

    summary = {
        "hydrogen_bond_count": count_xml_tags(xml_text, "hydrogen_bond"),
        "hydrophobic_contact_count": count_xml_tags(
            xml_text,
            "hydrophobic_interaction",
        ),
        "salt_bridge_count": count_xml_tags(xml_text, "salt_bridge"),
        "pi_stacking_count": count_xml_tags(xml_text, "pi_stack"),
    }

    summary["total_interactions"] = sum(summary.values())

    return {
        "summary": summary,
        "interactions": [],
        "parser_note": (
            "Day 22 MVP counts interaction types from PLIP XML. "
            "Detailed residue-level parsing will be added later."
        ),
    }


def build_success_output(
    input_payload: Dict[str, Any],
    output_key: str,
    complex_file_s3_key: str,
    parsed_result: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "job_id": input_payload["job_id"],
        "docking_job_id": input_payload["docking_job_id"],
        "interaction_backend": "plip",
        "analysis_status": "completed",
        "target_name": input_payload["target_name"],
        "target_uniprot_accession": input_payload["target_uniprot_accession"],
        "ligand_name": input_payload["ligand_name"],
        "bindingdb_monomer_id": input_payload.get("bindingdb_monomer_id"),
        "summary": parsed_result["summary"],
        "interactions": parsed_result["interactions"],
        "parser_note": parsed_result["parser_note"],
        "source_files": {
            "receptor_pdb_s3_key": input_payload["receptor_pdb_s3_key"],
            "docked_pose_s3_key": input_payload["docked_pose_s3_key"],
            "complex_file_s3_key": complex_file_s3_key,
            "interaction_summary_s3_key": output_key,
        },
        "limitation_note": LIMITATION_NOTE,
    }


def build_failed_output(
    input_payload: Dict[str, Any],
    output_key: str,
    error_message: str,
) -> Dict[str, Any]:
    return {
        "job_id": input_payload.get("job_id"),
        "docking_job_id": input_payload.get("docking_job_id"),
        "interaction_backend": "plip",
        "analysis_status": "failed",
        "target_name": input_payload.get("target_name"),
        "target_uniprot_accession": input_payload.get("target_uniprot_accession"),
        "ligand_name": input_payload.get("ligand_name"),
        "bindingdb_monomer_id": input_payload.get("bindingdb_monomer_id"),
        "summary": {
            "hydrogen_bond_count": 0,
            "hydrophobic_contact_count": 0,
            "salt_bridge_count": 0,
            "pi_stacking_count": 0,
            "total_interactions": 0,
        },
        "interactions": [],
        "error_message": error_message,
        "source_files": {
            "receptor_pdb_s3_key": input_payload.get("receptor_pdb_s3_key"),
            "docked_pose_s3_key": input_payload.get("docked_pose_s3_key"),
            "complex_file_s3_key": None,
            "interaction_summary_s3_key": output_key,
        },
        "limitation_note": LIMITATION_NOTE,
    }


def main() -> int:
    input_payload: Dict[str, Any] = {}

    try:
        aws_region = get_required_env("AWS_REGION")
        bucket = get_required_env("AMRDRUGX_SCREENING_BUCKET")
        input_key = get_required_env("INPUT_KEY")
        output_key = get_required_env("OUTPUT_KEY")

        print("Starting AMRDrugX PLIP interaction worker")
        print(f"AWS region: {aws_region}")
        print(f"Bucket: {bucket}")
        print(f"Input key: {input_key}")
        print(f"Output key: {output_key}")

        WORK_DIR.mkdir(parents=True, exist_ok=True)

        client = boto3.client("s3", region_name=aws_region)

        input_payload = read_json_from_s3(client, bucket, input_key)

        receptor_pdb_path = WORK_DIR / RECEPTOR_PDB_FILENAME
        docked_pose_path = WORK_DIR / DOCKED_POSE_PDBQT_FILENAME
        ligand_pdb_path = WORK_DIR / LIGAND_PDB_FILENAME
        complex_pdb_path = WORK_DIR / COMPLEX_PDB_FILENAME

        download_s3_file(
            client,
            bucket,
            input_payload["receptor_pdb_s3_key"],
            receptor_pdb_path,
        )
        download_s3_file(
            client,
            bucket,
            input_payload["docked_pose_s3_key"],
            docked_pose_path,
        )

        convert_pdbqt_to_pdb(docked_pose_path, ligand_pdb_path)
        build_complex_pdb(receptor_pdb_path, ligand_pdb_path, complex_pdb_path)

        run_plip(complex_pdb_path, PLIP_OUTPUT_DIR)

        parsed_result = parse_plip_summary(PLIP_OUTPUT_DIR)

        complex_file_s3_key = input_payload.get(
            "complex_file_s3_key",
            f"interaction_jobs/{input_payload['job_id']}/output/complex.pdb",
        )

        upload_s3_file(client, bucket, complex_file_s3_key, complex_pdb_path)

        output_payload = build_success_output(
            input_payload=input_payload,
            output_key=output_key,
            complex_file_s3_key=complex_file_s3_key,
            parsed_result=parsed_result,
        )

        write_json_to_s3(client, bucket, output_key, output_payload)

        print("PLIP interaction worker completed successfully")
        return 0

    except Exception as exc:
        print(f"PLIP interaction worker failed: {exc}", file=sys.stderr)

        try:
            aws_region = get_required_env("AWS_REGION")
            bucket = get_required_env("AMRDRUGX_SCREENING_BUCKET")
            output_key = get_required_env("OUTPUT_KEY")
            client = boto3.client("s3", region_name=aws_region)

            failed_payload = build_failed_output(
                input_payload=input_payload,
                output_key=output_key,
                error_message=str(exc),
            )

            write_json_to_s3(client, bucket, output_key, failed_payload)
        except Exception as write_exc:
            print(
                f"Failed to write PLIP failure output: {write_exc}",
                file=sys.stderr,
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())