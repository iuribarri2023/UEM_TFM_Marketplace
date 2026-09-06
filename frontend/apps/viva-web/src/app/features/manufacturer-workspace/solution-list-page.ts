import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import type { CommercialSolutionDto } from '@viva/contracts';
import { actionsForCommercialSolution } from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { ManufacturerSolutionsApi } from '../../core/api/manufacturer-solutions.api';
import { normalizeApiError, userMessageForError } from '../../core/errors/api-error';
import { StatusBadgeComponent } from '../../shared/status-badge';

@Component({
  imports: [RouterLink, StatusBadgeComponent],
  template: `
    <section class="page-header">
      <div>
        <h1>Manufacturer solutions</h1>
        <p>Your commercial solutions, review status, rejection feedback, and backend IFC readiness.</p>
      </div>
      <a class="button primary" routerLink="/manufacturer/solutions/new">Create draft</a>
    </section>

    @if (error()) {
      <p class="error">{{ error() }}</p>
    }

    <section class="panel">
      @if (loading()) {
        <div class="skeleton"></div>
      } @else if (solutions().length === 0) {
        <p class="muted">No own commercial solutions exist yet.</p>
      } @else {
        <table class="table">
          <thead>
            <tr>
              <th>Solution</th>
              <th>Status</th>
              <th>Valid IFC</th>
              <th>Updated</th>
              <th>Review feedback</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            @for (solution of solutions(); track solution.id) {
              <tr>
                <td>
                  <strong>{{ solution.code }}</strong><br />
                  {{ solution.name_es }}
                </td>
                <td><app-status-badge [status]="solution.status" /></td>
                <td>{{ actionState(solution).hasBackendValidIfc ? 'Yes' : 'No' }}</td>
                <td>{{ solution.updated_at }}</td>
                <td>{{ solution.rejection_reason || 'None' }}</td>
                <td>
                  <a class="button secondary" [routerLink]="['/manufacturer/solutions', solution.id, 'edit']">
                    Open
                  </a>
                </td>
              </tr>
            }
          </tbody>
        </table>
      }
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ManufacturerSolutionListPage {
  private readonly api = inject(ManufacturerSolutionsApi);
  readonly solutions = signal<CommercialSolutionDto[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  constructor() {
    void this.load();
  }

  actionState(solution: CommercialSolutionDto) {
    return actionsForCommercialSolution(solution);
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    try {
      this.solutions.set(await firstValueFrom(this.api.list()));
      this.error.set(null);
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
    } finally {
      this.loading.set(false);
    }
  }
}
