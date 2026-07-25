from fastapi import FastAPI

from app.api.routes import (
    bindingdb_evaluation,
    candidate_retrieval,
    docking_routes,
    health,
    molecule_screening,
    protein_structures,
    proteins,
    targets,
)

app = FastAPI(
    title="AMRDrugX API",
    description="Free-first AI-assisted antimicrobial resistance drug discovery prototype.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(targets.router, prefix="/api")
app.include_router(proteins.router, prefix="/api")
app.include_router(protein_structures.router, prefix="/api")
app.include_router(molecule_screening.router, prefix="/api")
app.include_router(candidate_retrieval.router)
app.include_router(bindingdb_evaluation.router)
app.include_router(docking_routes.router)