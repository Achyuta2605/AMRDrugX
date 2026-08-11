import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';

import { AmrApiService, AmrWorkflowResponse } from './amr-api.service';

@Component({
  selector: 'app-root',
  imports: [CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  readonly loading = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly workflow = signal<AmrWorkflowResponse | null>(null);
  readonly bindingSiteSummary = signal<string | null>(null);
  readonly dockingSummary = signal<string | null>(null);
  readonly interactionSummary = signal<string | null>(null);

  readonly form = {
    resistance_mechanism: 'carbapenem resistance',
    enzyme: 'KPC beta-lactamase',
    organism: 'Klebsiella pneumoniae',
  };

  constructor(private readonly amrApi: AmrApiService) {}

  getBindingSiteResultUrl(workflow: AmrWorkflowResponse): string {
    return `http://127.0.0.1:8000/api/binding-sites/${workflow.completed_demo_jobs.binding_site_job_id}/result`;
  }

  getDockingResultUrl(workflow: AmrWorkflowResponse): string {
    return `http://127.0.0.1:8000/api/docking/jobs/${workflow.completed_demo_jobs.docking_job_id}/result`;
  }

  getDockingViewerUrl(workflow: AmrWorkflowResponse): string {
    return `http://127.0.0.1:8000/api/docking/jobs/${workflow.completed_demo_jobs.docking_job_id}/view`;
  }

  getInteractionResultUrl(workflow: AmrWorkflowResponse): string {
    return `http://127.0.0.1:8000/api/interactions/${workflow.completed_demo_jobs.interaction_job_id}/result`;
  }

  prepareWorkflow(): void {
    this.loading.set(true);
    this.errorMessage.set(null);

    this.amrApi.prepareWorkflow(this.form).subscribe({
      next: (workflow) => {
        this.workflow.set(workflow);
        this.loadDemoSummaries(workflow);
        this.loading.set(false);
      },
      error: () => {
        this.errorMessage.set(
          'Unable to prepare AMR workflow. Check that the FastAPI backend is running.',
        );
        this.loading.set(false);
      },
    });
  }

  private loadDemoSummaries(workflow: AmrWorkflowResponse): void {
  this.bindingSiteSummary.set(null);
  this.dockingSummary.set(null);
  this.interactionSummary.set(null);

  const bindingSiteJobId = workflow.completed_demo_jobs.binding_site_job_id;
  const dockingJobId = workflow.completed_demo_jobs.docking_job_id;
  const interactionJobId = workflow.completed_demo_jobs.interaction_job_id;

  if (bindingSiteJobId) {
    this.amrApi.getBindingSiteResult(bindingSiteJobId).subscribe({
      next: (response: any) => {
        const pocket = response?.result?.top_pocket;
        if (pocket) {
          this.bindingSiteSummary.set(
            `Top pocket score ${pocket.score}, probability ${pocket.probability}`,
          );
        }
      },
    });
  }

  if (dockingJobId) {
    this.amrApi.getDockingResult(dockingJobId).subscribe({
      next: (response: any) => {
        const affinity = response?.result?.best_affinity_kcal_mol;
        if (affinity !== undefined && affinity !== null) {
          this.dockingSummary.set(`Best affinity ${affinity} kcal/mol`);
        }
      },
    });
  }

  if (interactionJobId) {
    this.amrApi.getInteractionResult(interactionJobId).subscribe({
      next: (response: any) => {
        const total = response?.result?.summary?.total_interactions;
        if (total !== undefined && total !== null) {
          this.interactionSummary.set(`${total} predicted interactions`);
        }
      },
    });
  }
}
}