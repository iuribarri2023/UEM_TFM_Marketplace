import { ChangeDetectionStrategy, Component, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import type { CommercialSolutionDto, ManufacturerDto } from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { MarketplaceApi } from '../../core/api/marketplace.api';
import { normalizeApiError, userMessageForError } from '../../core/errors/api-error';
import { StatusBadgeComponent } from '../../shared/status-badge';

@Component({
  imports: [RouterLink, StatusBadgeComponent],
  template: `
    @if (error()) {
      <p class="error">{{ error() }}</p>
    } @else if (!manufacturer()) {
      <div class="skeleton"></div>
    } @else {
      @let current = manufacturer()!;
      <section class="page-header">
        <div>
          <p class="muted">{{ current.code }} · {{ current.status }}</p>
          <h1>{{ current.name }}</h1>
          <p>{{ current.description || 'No public description.' }}</p>
          @if (current.website) {
            <a [href]="current.website" rel="noopener noreferrer" target="_blank">{{ current.website }}</a>
          }
        </div>
        <a class="button secondary" routerLink="/manufacturers">Back</a>
      </section>

      <section class="list">
        @for (solution of solutions(); track solution.id) {
          <article class="card">
            <p class="muted">{{ solution.code }}</p>
            <h2>{{ solution.name_es }}</h2>
            <app-status-badge [status]="solution.status" />
            <a class="button secondary" [routerLink]="['/marketplace', solution.id]">Inspect commercial solution</a>
          </article>
        } @empty {
          <section class="panel">
            <h2>No approved public solutions</h2>
          </section>
        }
      </section>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ManufacturerDetailPage {
  readonly id = input.required<string>();
  private readonly api = inject(MarketplaceApi);
  readonly manufacturer = signal<ManufacturerDto | null>(null);
  readonly solutions = signal<CommercialSolutionDto[]>([]);
  readonly error = signal<string | null>(null);

  constructor() {
    queueMicrotask(() => void this.load());
  }

  private async load(): Promise<void> {
    try {
      const id = this.id();
      const [manufacturer, solutions] = await Promise.all([
        firstValueFrom(this.api.manufacturer(id)),
        firstValueFrom(this.api.commercialSolutions({ manufacturer_id: id })),
      ]);
      this.manufacturer.set(manufacturer);
      this.solutions.set(solutions);
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
    }
  }
}
