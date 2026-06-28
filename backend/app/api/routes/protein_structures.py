from html import escape
from urllib.parse import urlparse

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from app.schemas.protein_structure import (
    ProteinStructureLookupRequest,
    ProteinStructureLookupResponse,
)
from app.services.protein_structure_service import lookup_protein_structures

router = APIRouter(prefix="/proteins/structures", tags=["protein structures"])


@router.post("", response_model=ProteinStructureLookupResponse)
def find_protein_structures(
    request: ProteinStructureLookupRequest,
) -> ProteinStructureLookupResponse:
    return lookup_protein_structures(request)


@router.get("/view", response_class=HTMLResponse)
def view_protein_structure(
    structure_url: str = Query(..., description="HTTP/HTTPS URL to a PDB file"),
) -> HTMLResponse:
    parsed_url = urlparse(structure_url)

    if parsed_url.scheme not in {"http", "https"}:
        return HTMLResponse(
            content="<h1>Invalid structure URL</h1><p>Only http and https URLs are allowed.</p>",
            status_code=400,
        )

    safe_structure_url = escape(structure_url)

    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>AMRDrugX Protein Structure Viewer</title>
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
        <style>
          body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f6f8fa;
            color: #1f2933;
          }}

          header {{
            padding: 16px 24px;
            background: #0f172a;
            color: white;
          }}

          main {{
            padding: 16px 24px;
          }}

          #viewer {{
            width: 100%;
            height: 620px;
            border: 1px solid #d0d7de;
            background: white;
          }}

          .meta {{
            margin-top: 12px;
            font-size: 14px;
            word-break: break-all;
          }}

          .warning {{
            margin-top: 12px;
            padding: 12px;
            background: #fff7ed;
            border: 1px solid #fed7aa;
            color: #7c2d12;
          }}
        </style>
      </head>
      <body>
        <header>
          <h1>AMRDrugX Protein Structure Viewer</h1>
        </header>

        <main>
          <div id="viewer"></div>

          <p class="meta">
            <strong>Structure URL:</strong> {safe_structure_url}
          </p>

          <div class="warning">
            Computational research viewer only. Structure interpretation, docking,
            and experimental validation are still required.
          </div>
        </main>

        <script>
          const structureUrl = "{safe_structure_url}";
          const viewer = $3Dmol.createViewer("viewer", {{ backgroundColor: "white" }});

          fetch(structureUrl)
            .then(response => {{
              if (!response.ok) {{
                throw new Error("Could not fetch structure file.");
              }}
              return response.text();
            }})
            .then(data => {{
              viewer.addModel(data, "pdb");
              viewer.setStyle({{}}, {{ cartoon: {{ color: "spectrum" }} }});
              viewer.zoomTo();
              viewer.render();
            }})
            .catch(error => {{
              document.getElementById("viewer").innerHTML =
                "<p style='padding: 20px;'>Could not load structure file: " +
                error.message +
                "</p>";
            }});
        </script>
      </body>
    </html>
    """

    return HTMLResponse(content=html)