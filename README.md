# AMRDrugX

AMRDrugX is a research prototype for AI-assisted antimicrobial resistance drug discovery.

The project connects target resolution, candidate molecule retrieval, DTI prediction, binding-site prediction, docking, interaction analysis, and visualization into one early-stage computational workflow.

> Research prototype only. AMRDrugX does not make clinical, therapeutic, safety, or efficacy claims. All outputs require literature review, docking/ADMET follow-up, and experimental validation.

---

## Current MVP Focus

The current vertical slice focuses on:

- Resistance mechanism: carbapenem resistance
- Target: KPC beta-lactamase
- UniProt accession: Q9F663
- Organism context: Klebsiella pneumoniae
- Candidate source: BindingDB / ChEMBL / PubChem
- DTI model: DeepPurpose MPNN_CNN_DAVIS
- Binding-site prediction: P2Rank
- Docking: AutoDock Vina
- Interaction analysis: PLIP
- Frontend: Angular research console
- Backend: FastAPI
- Worker orchestration: AWS ECS/Fargate
- Storage: AWS S3

---

## What AMRDrugX Does

AMRDrugX currently supports the following research workflow:

1. Resolve an AMR target from resistance mechanism, enzyme, and organism context.
2. Retrieve candidate molecules from external public databases.
3. Run DeepPurpose DTI screening against the selected protein target.
4. Compare predictions against BindingDB affinity records where available.
5. Predict binding pockets using P2Rank.
6. Dock a selected ligand using AutoDock Vina.
7. Analyze predicted protein-ligand interactions using PLIP.
8. Display the workflow and saved demo outputs in an Angular frontend.

---

## Current Pipeline

```text
AMR Input
  ↓
Target Resolution
  ↓
Candidate Retrieval
  ↓
DeepPurpose DTI Screening
  ↓
Candidate Selection
  ↓
P2Rank Binding-Site Prediction
  ↓
AutoDock Vina Docking
  ↓
PLIP Interaction Analysis
  ↓
3D Visualization / Result Console

Current Demo Outputs
The current saved demo workflow uses KPC beta-lactamase / Q9F663 and BindingDB monomer 50053173.
Example completed demo outputs:
P2Rank top pocket:
Score: 9.55
Probability: 0.513
Center: x=58.5187, y=-23.5423, z=-2.413

AutoDock Vina docking:
Best affinity: -4.633 kcal/mol

PLIP interaction analysis:
Hydrogen bonds: 25
Hydrophobic contacts: 2
Salt bridges: 6
Total predicted interactions: 33

These are computational outputs only and are not biological validation.
Tech Stack
Backend
Python
FastAPI
Pydantic
boto3
AWS S3
AWS ECS/Fargate
AI / Computational Tools
DeepPurpose
BindingDB
ChEMBL
PubChem
P2Rank
AutoDock Vina
PLIP
Open Babel
3Dmol.js
Frontend
Angular
TypeScript
SCSS

AMRDrugX/
  backend/
    app/
      api/
        routes/
      schemas/
      services/
      data/
    requirements.txt

  frontend/
    src/
      app/
        app.html
        app.scss
        app.ts
        amr-api.service.ts

  workers/
    dti_scorer/
    vina_docking_worker/
    p2rank_worker/
    interaction_worker/

  docs/
  README.md

Current Frontend
The Angular frontend is a research console that currently displays saved demo workflow outputs.
It shows:
AMR target context
Known receptor and ligand inputs
Saved P2Rank, Vina, and PLIP demo jobs
Result summary band
Candidate selection placeholder
DeepPurpose ranking placeholder
3D docking viewer link
Live pipeline action placeholders
The current frontend does not launch AWS jobs when clicking Prepare workflow. It reads saved demo outputs from backend APIs.
Scientific Limitations
AMRDrugX is not a validation platform yet.
Current limitations:
BindingDB sanity checks are tiny and target-specific.
DeepPurpose outputs are model predictions, not experimental evidence.
Docking score is computational and sensitive to receptor preparation, ligand preparation, and binding box selection.
PLIP interaction counts are currently MVP-level summaries.
ADMET, toxicity, molecular dynamics, wet-lab validation, and expert literature review are not yet included.
Results should be interpreted as candidate prioritization signals only.
Roadmap
Planned next steps:
Add live candidate selection in the frontend.
Connect retrieved candidates to DeepPurpose ranking controls.
Let users select ranked molecules for docking.
Improve PLIP residue-level interaction parsing.
Add binding pocket visualization overlays.
Add better receptor and ligand preparation workflow.
Add ADMET filtering.
Add benchmark/evaluation datasets beyond tiny BindingDB sanity checks.
Add job history and result persistence UI.
Deploy backend and frontend with secure runtime configuration.