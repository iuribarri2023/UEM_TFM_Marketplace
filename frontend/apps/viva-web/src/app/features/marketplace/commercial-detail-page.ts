import { ChangeDetectionStrategy, Component, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import type { AssetDto, CommercialSolutionDto, GenericSolutionDto, ManufacturerDto } from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { CatalogueApi } from '../../core/api/catalogue.api';
import { MarketplaceApi } from '../../core/api/marketplace.api';
import { normalizeApiError, userMessageForError } from '../../core/errors/api-error';
import { AssetListComponent } from '../../shared/asset-list';
import { StatusBadgeComponent } from '../../shared/status-badge';
import { TechnicalDataComponent } from '../../shared/technical-data';
import { IfcViewerHostComponent } from '../bim/ifc-viewer-host';

@Component({
  imports: [RouterLink, AssetListComponent, TechnicalDataComponent, StatusBadgeComponent, IfcViewerHostComponent],
  template: `
    @if (error()) {
      <p class="error">{{ error() }}</p>
    } @else if (!solution()) {
      <div class="skeleton"></div>
    } @else {
      @let current = solution()!;
      <section class="page-header">
        <div>
          <p class="muted">{{ current.code }}</p>
          <h1>{{ current.name_es }}</h1>
          <p>{{ current.description || 'No description available.' }}</p>
          <app-status-badge [status]="current.status" />
        </div>
        <a class="button secondary" routerLink="/marketplace">Back to marketplace</a>
      </section>

      <section class="grid two">
        <div class="panel">
          <h2>Commercial context</h2>
          <p><strong>Manufacturer:</strong> {{ manufacturer()?.name || current.manufacturer_id }}</p>
          <p><strong>Generic solution:</strong> {{ generic()?.code || current.generic_solution_id }} {{ generic()?.name_es }}</p>
        </div>
        <div class="panel">
          <app-technical-data title="Commercial technical data" [data]="current.technical_data" />
        </div>
      </section>

      <section class="panel">
        <h2>Assets</h2>
        <app-asset-list [assets]="current.assets" (preview)="selectedIfc.set($event)" />
      </section>

      @if (selectedIfc()) {
        <app-ifc-viewer-host [asset]="selectedIfc()" />
      }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CommercialDetailPage {
  readonly id = input.required<string>();
  private readonly marketplaceApi = inject(MarketplaceApi);
  private readonly catalogueApi = inject(CatalogueApi);
  readonly solution = signal<CommercialSolutionDto | null>(null);
  readonly manufacturer = signal<ManufacturerDto | null>(null);
  readonly generic = signal<GenericSolutionDto | null>(null);
  readonly selectedIfc = signal<AssetDto | null>(null);
  readonly error = signal<string | null>(null);

  constructor() {
    queueMicrotask(() => void this.load());
  }

  private async load(): Promise<void> {
    try {
      const solution = await firstValueFrom(this.marketplaceApi.commercialSolution(this.id()));
      this.solution.set(solution);
      this.selectedIfc.set(solution.assets.find((asset) => asset.format === 'ifc') ?? null);
      const [manufacturer, generic] = await Promise.all([
        firstValueFrom(this.marketplaceApi.manufacturer(solution.manufacturer_id)),
        firstValueFrom(this.catalogueApi.genericSolution(solution.generic_solution_id)),
      ]);
      this.manufacturer.set(manufacturer);
      this.generic.set(generic);
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
    }
  }
}
