from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.schemas.docking_schemas import (
    DockingJobRequest,
    DockingJobResult,
    DockingJobResultResponse,
    DockingJobSubmitResponse,
)
from app.services.docking_job_store import (
    build_docked_pose_key,
    build_docking_input_key,
    build_docking_output_key,
    build_s3_uri,
    create_presigned_s3_url,
    docking_output_exists,
    get_docking_output,
    save_docking_input,
)
from app.services.docking_task_launcher import start_docking_fargate_task


router = APIRouter(prefix="/api/docking", tags=["docking"])

SAFETY_NOTE = (
    "Docking results are computational predictions only. They are not experimental "
    "validation and are not medical or therapeutic claims."
)

LIMITATION_NOTE = (
    "Computational docking result only. Not experimental validation. Docking quality "
    "depends on receptor preparation, ligand preparation, binding box choice, and scoring limitations."
)


@router.post("/jobs", response_model=DockingJobSubmitResponse)
def submit_docking_job(request: DockingJobRequest) -> DockingJobSubmitResponse:
    job_id = request.job_id or str(uuid4())
    input_key = build_docking_input_key(job_id)
    output_key = build_docking_output_key(job_id)

    input_payload = request.model_dump()
    input_payload["job_id"] = job_id
    input_payload["docking_backend"] = "autodock_vina"
    input_payload["docked_pose_s3_key"] = f"docking_jobs/{job_id}/output/docked_pose.pdbqt"

    save_docking_input(job_id=job_id, payload=input_payload)

    task = start_docking_fargate_task(
        job_id=job_id,
        input_key=input_key,
        output_key=output_key,
    )

    return DockingJobSubmitResponse(
        job_id=job_id,
        status="submitted",
        docking_backend="autodock_vina",
        input_s3_key=input_key,
        output_s3_key=output_key,
        task_arn=task["task_arn"],
        message="Docking job submitted to AWS Fargate.",
        safety_note=SAFETY_NOTE,
    )


@router.get("/jobs/{job_id}/result", response_model=DockingJobResultResponse)
def get_docking_job_result(job_id: str) -> DockingJobResultResponse:
    output_key = build_docking_output_key(job_id)

    if not docking_output_exists(job_id):
        return DockingJobResultResponse(
            job_id=job_id,
            status="not_ready",
            output_s3_key=output_key,
            result=None,
            safety_note=SAFETY_NOTE,
        )

    output_payload = get_docking_output(job_id)

    result = DockingJobResult(
        job_id=output_payload["job_id"],
        target_name=output_payload["target_name"],
        target_uniprot_accession=output_payload["target_uniprot_accession"],
        ligand_name=output_payload["ligand_name"],
        bindingdb_monomer_id=output_payload.get("bindingdb_monomer_id"),
        docking_backend=output_payload["docking_backend"],
        docking_status=output_payload["docking_status"],
        best_affinity_kcal_mol=output_payload.get("best_affinity_kcal_mol"),
        docking_score=output_payload.get("docking_score"),
        cnn_score=output_payload.get("cnn_score"),
        cnn_affinity=output_payload.get("cnn_affinity"),
        receptor_pdb_s3_key=output_payload["receptor_pdb_s3_key"],
        ligand_sdf_s3_key=output_payload.get(
            "ligand_sdf_s3_key",
            output_payload.get("ligand_input_s3_key", ""),
        ),
        docked_pose_sdf_s3_key=output_payload.get("docked_pose_sdf_s3_key"),
        docked_pose_s3_key=output_payload.get("docked_pose_s3_key"),
        viewer_url=f"/api/docking/jobs/{job_id}/view",
        limitation_note=output_payload.get("limitation_note", LIMITATION_NOTE),
    )

    return DockingJobResultResponse(
        job_id=job_id,
        status="completed",
        output_s3_key=output_key,
        result=result,
        safety_note=SAFETY_NOTE,
    )


@router.get("/jobs/{job_id}/view", response_class=HTMLResponse)
def view_docking_result(job_id: str) -> HTMLResponse:
    if not docking_output_exists(job_id):
        raise HTTPException(status_code=404, detail="Docking output is not ready.")

    output_payload = get_docking_output(job_id)

    receptor_key = output_payload["receptor_pdb_s3_key"]
    docked_pose_key = output_payload.get("docked_pose_s3_key") or output_payload.get(
        "docked_pose_sdf_s3_key"
    )

    if not docked_pose_key:
        raise HTTPException(
            status_code=404,
            detail="Docked pose file is missing from docking output.",
        )

    receptor_url = create_presigned_s3_url(receptor_key)
    docked_pose_url = create_presigned_s3_url(docked_pose_key)

    html = f"""
    <!doctype html>
    <html>
      <head>
        <title>AMRDrugX Docking Viewer</title>
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
        <style>
          body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e5e7eb;
          }}
          header {{
            padding: 12px 16px;
            background: #111827;
            border-bottom: 1px solid #374151;
          }}
          #viewer {{
            width: 100vw;
            height: calc(100vh - 72px);
          }}
          .meta {{
            font-size: 12px;
            color: #cbd5e1;
          }}
        </style>
      </head>
      <body>
        <header>
          <strong>AMRDrugX Docking Viewer</strong>
          <div class="meta">
            Job: {job_id} | Receptor: {receptor_key} | Docked pose: {docked_pose_key}
          </div>
        </header>
        <div id="viewer"></div>
        <script>
          const viewer = $3Dmol.createViewer("viewer", {{ backgroundColor: "#0f172a" }});

          Promise.all([
            fetch("{receptor_url}").then(response => response.text()),
            fetch("{docked_pose_url}").then(response => response.text())
          ]).then(([receptorData, ligandData]) => {{
            viewer.addModel(receptorData, "pdb");
            viewer.setStyle({{}}, {{ cartoon: {{ color: "spectrum" }} }});

            viewer.addModel(ligandData, "{'pdbqt' if output_payload.get('docked_pose_s3_key') else 'sdf'}");
            viewer.setStyle({{ model: 1 }}, {{ stick: {{ colorscheme: "greenCarbon", radius: 0.22 }} }});

            viewer.zoomTo();
            viewer.render();
          }}).catch(error => {{
            document.getElementById("viewer").innerHTML =
              "<div style='padding:16px'>Failed to load docking files: " + error + "</div>";
          }});
        </script>
      </body>
    </html>
    """

    return HTMLResponse(content=html)


def _unused_reference_for_lint() -> str:
    return build_s3_uri("docking_jobs/example/output.json")