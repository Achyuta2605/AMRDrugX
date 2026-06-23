from fastapi import FastAPI

from app.api.routes import health, targets

app = FastAPI(
    title="AMRDrugX API",
    description="Free-first AI-assisted antimicrobial resistance drug discovery prototype.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(targets.router, prefix="/api")