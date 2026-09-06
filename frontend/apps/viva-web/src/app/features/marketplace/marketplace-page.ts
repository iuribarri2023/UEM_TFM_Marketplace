import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import type {
  ArchetypeDto,
  CommercialSolutionDto,
  GenericSolutionSummaryDto,
  ManufacturerDto,
  SubsystemDto,
  SystemDto,
} from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { CatalogueApi } from '../../core/api/catalogue.api';
import { MarketplaceApi, MarketplaceFilters } from '../../core/api/marketplace.api';
import { normalizeApiError, userMessageForError } from '../../core/errors/api-error';
import { StatusBadgeComponent } from '../../shared/status-badge';

@Component({
  imports: [RouterLink, StatusBadgeComponent],
  template: `
    <section class="page-header">
      <div>
        <h1>Marketplace</h1>
        <p>Approved manufacturer commercial solutions returned by the public marketplace API.</p>
      </div>
    </section>

    <section class="panel filters">
      <label class="field">
        <span>System</span>
        <select [value]="filters().system_id || ''" (change)="setTaxonomyFilter('system_id', $any($event.target).value)">
          <option value="">All systems</option>
          @for (system of systems(); track system.id) {
            <option [value]="system.id">{{ system.code }} · {{ system.name_es }}</option>
          }
        </select>
      </label>
      <label class="field">
        <span>Subsystem</span>
        <select [value]="filters().subsystem_id || ''" (change)="setTaxonomyFilter('subsystem_id', $any($event.target).value)">
          <option value="">All subsystems</option>
          @for (subsystem of visibleSubsystems(); track subsystem.id) {
            <option [value]="subsystem.id">{{ subsystem.code }} · {{ subsystem.name_es }}</option>
          }
        </select>
      </label>
      <label class="field">
        <span>Archetype</span>
        <select [value]="filters().archetype_id || ''" (change)="setTaxonomyFilter('archetype_id', $any($event.target).value)">
          <option value="">All archetypes</option>
          @for (archetype of visibleArchetypes(); track archetype.id) {
            <option [value]="archetype.id">{{ archetype.code }} · {{ archetype.name_es }}</option>
          }
        </select>
      </label>
      <label class="field">
        <span>Generic solution</span>
        <select [value]="filters().generic_solution_id || ''" (change)="setFilter('generic_solution_id', $any($event.target).value)">
          <option value="">All generic solutions</option>
          @for (generic of visibleGenerics(); track generic.id) {
            <option [value]="generic.id">{{ generic.code }} · {{ generic.name_es }}</option>
          }
        </select>
      </label>
      <label class="field">
        <span>Manufacturer</span>
        <select [value]="filters().manufacturer_id || ''" (change)="setFilter('manufacturer_id', $any($event.target).value)">
          <option value="">All manufacturers</option>
          @for (manufacturer of manufacturers(); track manufacturer.id) {
            <option [value]="manufacturer.id">{{ manufacturer.name }}</option>
          }
        </select>
      </label>
    </section>

    @if (error()) {
      <p class="error">{{ error() }}</p>
    } @else if (loading()) {
      <div class="skeleton"></div>
    } @else if (solutions().length === 0) {
      <section class="panel">
        <h2>No approved solutions</h2>
        <p class="muted">The backend returned no approved commercial solutions for these filters.</p>
      </section>
    } @else {
      <section class="grid three">
        @for (solution of solutions(); track solution.id) {
          <article class="card market-card">
            <div>
              <p class="muted">{{ solution.code }}</p>
              <h2>{{ solution.name_es }}</h2>
              <p>{{ solution.description || 'No commercial description.' }}</p>
              <p><strong>Manufacturer:</strong> {{ manufacturerName(solution.manufacturer_id) }}</p>
              <p><strong>Generic:</strong> {{ genericName(solution.generic_solution_id) }}</p>
              <app-status-badge [status]="solution.status" />
            </div>
            <a class="button secondary" [routerLink]="['/marketplace', solution.id]">Inspect</a>
          </article>
        }
      </section>
    }
  `,
  styles: [
    `
      .filters {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
      }
      .market-card {
        display: grid;
        align-content: space-between;
        min-height: 19rem;
      }
      h2,
      p {
        margin: 0.25rem 0;
      }
      @media (max-width: 760px) {
        .filters {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MarketplacePage {
  private readonly api = inject(MarketplaceApi);
  private readonly catalogueApi = inject(CatalogueApi);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly solutions = signal<CommercialSolutionDto[]>([]);
  readonly manufacturers = signal<ManufacturerDto[]>([]);
  readonly systems = signal<SystemDto[]>([]);
  readonly subsystems = signal<SubsystemDto[]>([]);
  readonly archetypes = signal<ArchetypeDto[]>([]);
  readonly generics = signal<GenericSolutionSummaryDto[]>([]);
  readonly filters = signal<MarketplaceFilters>({});
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  constructor() {
    void this.loadLookups();
    this.route.queryParamMap.subscribe((params) => {
      this.filters.set({
        system_id: params.get('system_id'),
        subsystem_id: params.get('subsystem_id'),
        archetype_id: params.get('archetype_id'),
        generic_solution_id: params.get('generic_solution_id'),
        manufacturer_id: params.get('manufacturer_id'),
      });
      void this.loadSolutions();
    });
  }

  setFilter(key: keyof MarketplaceFilters, value: string): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { ...this.filters(), [key]: value || null },
      queryParamsHandling: 'merge',
    });
  }

  setTaxonomyFilter(key: keyof MarketplaceFilters, value: string): void {
    const resets: Partial<MarketplaceFilters> =
      key === 'system_id'
        ? { subsystem_id: null, archetype_id: null, generic_solution_id: null }
        : key === 'subsystem_id'
          ? { archetype_id: null, generic_solution_id: null }
          : key === 'archetype_id'
            ? { generic_solution_id: null }
            : {};
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { ...resets, [key]: value || null },
      queryParamsHandling: 'merge',
    });
  }

  visibleSubsystems(): SubsystemDto[] {
    const systemId = this.filters().system_id;
    return systemId
      ? this.subsystems().filter((subsystem) => subsystem.system_id === systemId)
      : this.subsystems();
  }

  visibleArchetypes(): ArchetypeDto[] {
    const subsystemId = this.filters().subsystem_id;
    return subsystemId
      ? this.archetypes().filter((archetype) => archetype.subsystem_id === subsystemId)
      : this.archetypes();
  }

  visibleGenerics(): GenericSolutionSummaryDto[] {
    const archetypeId = this.filters().archetype_id;
    return archetypeId
      ? this.generics().filter((generic) => generic.archetype_id === archetypeId)
      : this.generics();
  }

  manufacturerName(id: string): string {
    return this.manufacturers().find((manufacturer) => manufacturer.id === id)?.name ?? id;
  }

  genericName(id: string): string {
    const item = this.generics().find((generic) => generic.id === id);
    return item ? `${item.code} · ${item.name_es}` : id;
  }

  private async loadLookups(): Promise<void> {
    try {
      const [manufacturers, systems, subsystems, archetypes, generics] = await Promise.all([
        firstValueFrom(this.api.manufacturers()),
        firstValueFrom(this.catalogueApi.systems()),
        firstValueFrom(this.catalogueApi.subsystems()),
        firstValueFrom(this.catalogueApi.archetypes()),
        firstValueFrom(this.catalogueApi.genericSolutions()),
      ]);
      this.manufacturers.set(manufacturers);
      this.systems.set(systems);
      this.subsystems.set(subsystems);
      this.archetypes.set(archetypes);
      this.generics.set(generics);
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
    }
  }

  private async loadSolutions(): Promise<void> {
    this.loading.set(true);
    try {
      this.solutions.set(await firstValueFrom(this.api.commercialSolutions(this.filters())));
      this.error.set(null);
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
    } finally {
      this.loading.set(false);
    }
  }
}
