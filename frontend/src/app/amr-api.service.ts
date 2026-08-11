import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface AmrWorkflowRequest {
  resistance_mechanism: string;
  enzyme?: string;
  organism?: string;
}

export interface AmrWorkflowResponse {
  workflow_id: string;
  status: string;
  input: {
    resistance_mechanism: string;
    enzyme?: string;
    organism?: string;
  };
  target: {
    target_name: string;
    gene?: string;
    organism?: string;
    uniprot_accession?: string;
    confidence: string;
    source: string;
  };
  available_modules: {
    protein_enrichment: boolean;
    structure_lookup: boolean;
    candidate_retrieval: boolean;
    deeppurpose_screening: boolean;
    binding_site_prediction: boolean;
    docking: boolean;
    interaction_analysis: boolean;
  };
  known_inputs: {
    receptor_pdb_s3_key?: string;
    ligand_name?: string;
    bindingdb_monomer_id?: string;
    ligand_sdf_s3_key?: string;
  };
  completed_demo_jobs: {
    binding_site_job_id?: string;
    docking_job_id?: string;
    interaction_job_id?: string;
  };
  recommended_next_steps: string[];
  action_endpoints: Record<string, string>;
  safety_note: string;
}

@Injectable({
  providedIn: 'root',
})
export class AmrApiService {
  private readonly apiBaseUrl = 'http://127.0.0.1:8000';

  constructor(private readonly http: HttpClient) {}

  prepareWorkflow(
    request: AmrWorkflowRequest,
  ): Observable<AmrWorkflowResponse> {
    return this.http.post<AmrWorkflowResponse>(
      `${this.apiBaseUrl}/api/workflows/amr`,
      request,
    );
  }

  getBindingSiteResult(jobId: string) {
  return this.http.get<unknown>(
    `${this.apiBaseUrl}/api/binding-sites/${jobId}/result`,
  );
}

getDockingResult(jobId: string) {
  return this.http.get<unknown>(
    `${this.apiBaseUrl}/api/docking/jobs/${jobId}/result`,
  );
}

getInteractionResult(jobId: string) {
  return this.http.get<unknown>(
    `${this.apiBaseUrl}/api/interactions/${jobId}/result`,
  );
}
}