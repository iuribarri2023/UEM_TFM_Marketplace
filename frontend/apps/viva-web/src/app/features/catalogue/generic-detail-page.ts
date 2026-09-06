import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import type { ArchetypeDto, AssetDto, GenericSolutionDto, SubsystemDto, SystemDto } from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { CatalogueApi } from '../../core/api/catalogue.api';
import { normalizeApiError, userMessageForError } from '../../core/errors/api-error';
import { AssetListComponent } from '../../shared/asset-list';
import { TechnicalDataComponent } from '../../shared/technical-data';
import { IfcViewerHostComponent } from '../bim/ifc-viewer-host';

@Component({
  imports: [RouterLink, AssetListComponent, TechnicalDataComponent, IfcViewerHostComponent],
  template: `
    @if (error()) {
      <p class="error">{{ error() }}</p>
    } @else if (!solution()) {
      <div class="skeleton"></div>
    } @else {
      @let current = solution()!;
      <section class="page-header">
        <div>
          <p class="muted">{{ current.code }} · {{ current.status || 'catalogue' }}</p>
          <h1>{{ current.name_es }}</h1>
          <p>{{ current.description || 'No description available.' }}</p>
        </div>
        <a
          class="button primary"
          [routerLink]="['/marketplace']"
          [queryParams]="{ generic_solution_id: current.id }"
        >
          Approved commercial solutions
        </a>
      </section>

      <section class="grid two">
        <div class="panel">
          <h2>Taxonomy</h2>
          <p><strong>System:</strong> {{ system()?.code || 'Unknown' }} {{ system()?.name_es }}</p>
          <p><strong>Subsystem:</strong> {{ subsystem()?.code || 'Unknown' }} {{ subsystem()?.name_es }}</p>
          <p><strong>Archetype:</strong> {{ archetype()?.code || 'Unknown' }} {{ archetype()?.name_es }}</p>
          <p><strong>Functional unit:</strong> {{ current.functional_unit || 'Unavailable' }}</p>
        </div>

        <div class="panel">
          <h2>Assets</h2>
          <app-asset-list [assets]="current.assets" (preview)="selectIfc($event)" />
        </div>
      </section>

      @if (selectedIfc()) {
        <app-ifc-viewer-host [asset]="selectedIfc()" />
      }

      <section class="panel">
        <h2>Slots</h2>
        <div class="list">
          @for (slot of orderedSlots(); track slot.id) {
            <article class="card">
              <p class="muted">{{ slot.key }} · {{ slot.role || 'role not specified' }}</p>
              <h3>{{ slot.sequence }}. {{ slot.name_es }} {{ slot.required ? '(required)' : '' }}</h3>
              <app-technical-data title="Properties" [data]="slot.properties" />
              <app-technical-data title="Metrics" [data]="slot.metrics" />
              <app-technical-data title="Source reference" [data]="slot.source_reference" />
            </article>
          }
        </div>
      </section>

      <section class="grid two">
        @for (section of sections(current); track section.label) {
          <div class="panel">
            <app-technical-data [title]="section.label" [data]="section.value" />
          </div>
        }
      </section>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GenericDetailPage {
  readonly code = input.required<string>();
  private readonly api = inject(CatalogueApi);
  readonly solution = signal<GenericSolutionDto | null>(null);
  readonly archetype = signal<ArchetypeDto | null>(null);
  readonly subsystem = signal<SubsystemDto | null>(null);
  readonly system = signal<SystemDto | null>(null);
  readonly selectedIfc = signal<AssetDto | null>(null);
  readonly error = signal<string | null>(null);
  readonly orderedSlots = computed(() =>
    [...(this.solution()?.slots ?? [])].sort((a, b) => a.sequence - b.sequence),
  );

  constructor() {
    queueMicrotask(() => void this.load());
  }

  selectIfc(asset: AssetDto): void {
    this.selectedIfc.set(asset);
  }

  sections(solution: GenericSolutionDto): { label: string; value: unknown }[] {
    return [
      { label: 'Classifications', value: solution.classifications },
      { label: 'Source references', value: solution.source_references },
      { label: 'Attributes', value: solution.attributes },
      { label: 'Metrics', value: solution.metrics },
      { label: 'CTE compliance', value: solution.cte_compliance },
      { label: 'Environmental data', value: solution.environmental_data },
      { label: 'Economic data', value: solution.economic_data },
      { label: 'Industrialization data', value: solution.industrialization_data },
      { label: 'VIVA metrics', value: solution.viva_metrics },
      { label: 'Data quality notes', value: solution.data_quality_notes },
    ];
  }

  private async load(): Promise<void> {
    try {
      const solution = await firstValueFrom(this.api.genericSolutionByCode(this.code()));
      this.solution.set(solution);
      this.selectedIfc.set(solution.assets.find((asset) => asset.format === 'ifc') ?? null);
      const archetype = await firstValueFrom(this.api.archetype(solution.archetype_id));
      this.archetype.set(archetype);
      const subsystem = await firstValueFrom(this.api.subsystem(archetype.subsystem_id));
      this.subsystem.set(subsystem);
      this.system.set(await firstValueFrom(this.api.system(subsystem.system_id)));
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
    }
  }
}
