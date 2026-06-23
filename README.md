# AMRDrugX

AMRDrugX is a free-first AI-assisted antimicrobial resistance drug discovery prototype.

It helps screen and rank possible antibiotic adjuvant molecules that may inhibit resistance-causing bacterial proteins and help restore antibiotic effectiveness.

This is a computational research prototype only. It is not a medical product.

## Problem Statement

Antimicrobial resistance can make existing antibiotics ineffective. AMRDrugX explores whether known or candidate molecules may interact with resistance-causing bacterial proteins, such as beta-lactamases, and therefore may be worth further scientific investigation.

The system does not claim clinical effectiveness or safety.

## MVP Scope

The MVP will eventually support:

- target resolution
- candidate molecule retrieval
- ADMET-like filtering
- docking or interaction scoring
- final ranking
- scientific explanation
- 3D protein-ligand visualization

Day 1 includes only:

- FastAPI backend
- health check endpoint
- static mock target resolver for KPC-2 beta-lactamase

## Free-First Constraints

AMRDrugX is designed for a normal CPU-only laptop.

We avoid:

- paid APIs
- GPU-heavy models
- local training of large models
- huge downloads during the early MVP

We prefer:

- public databases
- lightweight backend logic
- cached results
- mock interfaces before expensive integrations

## Scientific Boundary

All outputs are computational predictions only.

AMRDrugX must always communicate:

- not medical advice
- not a treatment recommendation
- not experimentally confirmed
- requires wet-lab validation

## Backend Run Instructions

From the project root:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload