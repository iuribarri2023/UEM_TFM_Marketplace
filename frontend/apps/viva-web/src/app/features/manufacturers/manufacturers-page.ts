import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import type { ManufacturerDto } from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { MarketplaceApi } from '../../core/api/marketplace.api';
import { normalizeApiError, userMessageForError } from '../../core/errors/api-error';

@Component({
  imports: [RouterLink],
  template: `
    <section class="page-header">
      <div>
        <h1>Manufacturers</h1>
        <p>Active public manufacturers from the marketplace API.</p>
      </div>
    </section>

    @if (error()) {
      <p class="error">{{ error() }}</p>
    } @else if (manufacturers().length === 0) {
      <div class="skeleton"></div>
    } @else {
      <section class="grid three">
        @for (manufacturer of manufacturers(); track manufacturer.id) {
          <article class="card">
            <p class="muted">{{ manufacturer.code }} · {{ manufacturer.status }}</p>
            <h2>{{ manufacturer.name }}</h2>
            <p>{{ manufacturer.description || 'No profile description.' }}</p>
            <a class="button secondary" [routerLink]="['/manufacturers', manufacturer.id]">Open</a>
          </article>
        }
      </section>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ManufacturersPage {
  private readonly api = inject(MarketplaceApi);
  readonly manufacturers = signal<ManufacturerDto[]>([]);
  readonly error = signal<string | null>(null);

  constructor() {
    void this.load();
  }

  private async load(): Promise<void> {
    try {
      this.manufacturers.set(await firstValueFrom(this.api.manufacturers()));
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
    }
  }
}
