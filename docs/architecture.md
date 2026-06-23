# AMRDrugX Architecture

## System Overview

AMRDrugX is an AI-assisted antimicrobial resistance drug discovery prototype.

It is not just a model. It is a full AI system made of APIs, retrieval, scoring logic, tool calls, storage, evaluation, observability, and guardrails.

## Layers

### Frontend Layer

The frontend will provide:

- input form
- candidate ranking dashboard
- score breakdowns
- scientific warnings
- 3D protein-ligand visualization

### Backend API Layer

The backend exposes stable HTTP endpoints.

Examples:

- `GET /health`
- `POST /api/targets/resolve`

### Inference Layer

The inference layer performs structured scientific prediction steps.

Early MVP inference includes:

- target resolution
- mock scoring
- final ranking logic later

### Data and Retrieval Layer

This layer will retrieve or cache information from:

- PubChem
- ChEMBL
- UniProt
- RCSB PDB
- AlphaFold DB
- local cache files

### Memory and State Layer

MVP memory includes:

- cached API responses
- saved target resolutions
- saved candidate rankings
- stored structure files

### Tool Layer

External tools and databases are treated as tools.

Examples:

- PubChem for compound data
- UniProt for protein metadata
- AutoDock Vina for docking
- RDKit for molecular properties

### Evaluation Layer

Evaluation checks whether the system:

- returns structured output
- resolves targets correctly
- ranks candidates consistently
- avoids unsafe claims

### Observability Layer

Observability will track:

- request ID
- tool calls
- latency
- scoring components
- errors
- warnings

### Safety and Guardrail Layer

Guardrails ensure the system communicates uncertainty and avoids medical claims.

## Day 1 Request Flow

```text
User request
  -> FastAPI endpoint
  -> Pydantic validation
  -> Target resolver service
  -> Static KPC-2 mock result
  -> JSON response with safety note