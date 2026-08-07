from uuid import uuid4

from app.schemas.workflow_schemas import (
    AMRWorkflowAvailableModules,
    AMRWorkflowInput,
    AMRWorkflowRequest,
    AMRWorkflowResponse,
    AMRWorkflowTarget,
    AMRWorkflowKnownInputs,
    AMRWorkflowCompletedJobs,
)


SAFETY_NOTE = (
    "Research-only computational workflow. Results are not experimental validation "
    "and are not medical or therapeutic claims."
)


def _normalize(value: str) -> str:
    return value.strip().lower()


def _resolve_initial_target(request: AMRWorkflowRequest) -> AMRWorkflowTarget:
    resistance_mechanism = _normalize(request.resistance_mechanism)
    enzyme = _normalize(request.enzyme or "")
    organism = request.organism or "Klebsiella pneumoniae"

    if "carbapenem" in resistance_mechanism or "kpc" in enzyme:
        return AMRWorkflowTarget(
            target_name="KPC beta-lactamase",
            gene="blaKPC",
            organism=organism,
            uniprot_accession="Q9F663",
            confidence="high",
            source="AMRDrugX curated MVP mapping",
        )

    return AMRWorkflowTarget(
        target_name=request.enzyme or request.resistance_mechanism,
        gene=None,
        organism=request.organism,
        uniprot_accession=None,
        confidence="needs_review",
        source="AMRDrugX fallback workflow mapping",
    )


def prepare_amr_workflow(
    request: AMRWorkflowRequest,
) -> AMRWorkflowResponse:
    target = _resolve_initial_target(request)

    return AMRWorkflowResponse(
        workflow_id=str(uuid4()),
        status="prepared",
        input=AMRWorkflowInput(
            resistance_mechanism=request.resistance_mechanism,
            enzyme=request.enzyme,
            organism=request.organism,
        ),
        target=target,
        available_modules=AMRWorkflowAvailableModules(),
        known_inputs=AMRWorkflowKnownInputs(
            receptor_pdb_s3_key="docking_jobs/manual-kpc-gnina-test/input/receptor.pdb",
            ligand_name="BindingDB monomer 50053173",
            bindingdb_monomer_id="50053173",
            ligand_sdf_s3_key="docking_jobs/manual-kpc-gnina-test/input/ligand.sdf",
        ),
        completed_demo_jobs=AMRWorkflowCompletedJobs(
            binding_site_job_id="manual-kpc-p2rank-test-3",
            docking_job_id="manual-kpc-vina-p2rank-box-test",
            interaction_job_id="manual-kpc-plip-interaction-test-2",
        ),
        recommended_next_steps=[
            "retrieve_candidates",
            "run_deeppurpose_screening",
            "run_binding_site_prediction",
            "run_docking",
            "run_interaction_analysis",
        ],
        action_endpoints={
            "retrieve_candidates": "/api/candidates/retrieve",
            "run_deeppurpose_screening": "/api/molecules/screen",
            "run_binding_site_prediction": "/api/binding-sites/predict",
            "run_docking": "/api/docking/jobs",
            "run_interaction_analysis": "/api/interactions/analyze",
        },
        safety_note=SAFETY_NOTE,
    )