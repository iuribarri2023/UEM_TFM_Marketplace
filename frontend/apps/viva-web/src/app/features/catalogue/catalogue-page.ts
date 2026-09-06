import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import type {
  ArchetypeDto,
  GenericSolutionSummaryDto,
  SubsystemDto,
  SystemDto,
} from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { CatalogueApi } from '../../core/api/catalogue.api';
import { normalizeApiError, userMessageForError } from '../../core/errors/api-error';

@Component({
  imports: [RouterLink],
  template: `
    <section class="page-header">
      <div>
        <h1>Catalogue</h1>
        <p>Browse AVRA taxonomy from systems down to generic construction solutions.</p>
      </div>
      <a class="button secondary" routerLink="/marketplace">Open marketplace</a>
    </section>

    @if (error()) {
      <p class="error" aria-live="assertive">{{ error() }}</p>
    }

    <section class="grid">
      <div class="panel selector-grid">
        <label class="field">
          <span>System</span>
          <select [value]="selectedSystemId()" (change)="selectSystem($any($event.target).value)">
            <option value="">Select system</option>
            @for (system of systems(); track system.id) {
              <option [value]="system.id">{{ system.code }} · {{ system.name_es }}</option>
            }
          </select>
        </label>

        <label class="field">
          <span>Subsystem</span>
          <select
            [value]="selectedSubsystemId()"
            [disabled]="subsystems().length === 0"
            (change)="selectSubsystem($any($event.target).value)"
          >
            <option value="">Select subsystem</option>
            @for (subsystem of subsystems(); track subsystem.id) {
              <option [value]="subsystem.id">{{ subsystem.code }} · {{ subsystem.name_es }}</option>
            }
          </select>
        </label>

        <label class="field">
          <span>Archetype</span>
          <select
            [value]="selectedArchetypeId()"
            [disabled]="archetypes().length === 0"
            (change)="selectArchetype($any($event.target).value)"
          >
            <option value="">Select archetype</option>
            @for (archetype of archetypes(); track archetype.id) {
              <option [value]="archetype.id">{{ archetype.code }} · {{ archetype.name_es }}</option>
            }
          </select>
        </label>
      </div>

      <div class="list">
        @if (loading()) {
          <div class="skeleton"></div>
        } @else if (genericSolutions().length === 0) {
          <div class="panel">
            <h2>No generic solutions</h2>
            <p class="muted">Select a taxonomy branch to load backend-filtered generic solutions.</p>
          </div>
        } @else {
          @for (solution of genericSolutions(); track solution.id) {
            <article class="card solution-card">
              <div>
                <p class="muted">{{ solution.code }} · {{ solution.functional_unit || 'No unit' }}</p>
                <h2>{{ solution.name_es }}</h2>
                <p>{{ solution.description || 'No description available.' }}</p>
              </div>
              <a class="button secondary" [routerLink]="['/generic-solutions', solution.code]">
                Inspect generic
              </a>
            </article>
          }
        }
      </div>
    </section>
  `,
  styles: [
    `
      .selector-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
      }
      .solution-card {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 1rem;
        align-items: center;
      }
      h2,
      p {
        margin: 0.2rem 0;
      }
      @media (max-width: 900px) {
        .selector-grid,
        .solution-card {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CataloguePage {
  private readonly api = inject(CatalogueApi);
  readonly systems = signal<SystemDto[]>([]);
  readonly subsystems = signal<SubsystemDto[]>([]);
  readonly archetypes = signal<ArchetypeDto[]>([]);
  readonly genericSolutions = signal<GenericSolutionSummaryDto[]>([]);
  readonly selectedSystemId = signal('');
  readonly selectedSubsystemId = signal('');
  readonly selectedArchetypeId = signal('');
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly selectedSystem = computed(() =>
    this.systems().find((system) => system.id === this.selectedSystemId()),
  );

  constructor() {
    void this.loadSystems();
  }

  async selectSystem(systemId: string): Promise<void> {
    this.selectedSystemId.set(systemId);
    this.selectedSubsystemId.set('');
    this.selectedArchetypeId.set('');
    this.archetypes.set([]);
    this.genericSolutions.set([]);
    this.subsystems.set(systemId ? await this.request(() => this.api.subsystems(systemId)) : []);
  }

  async selectSubsystem(subsystemId: string): Promise<void> {
    this.selectedSubsystemId.set(subsystemId);
    this.selectedArchetypeId.set('');
    this.genericSolutions.set([]);
    this.archetypes.set(subsystemId ? await this.request(() => this.api.archetypes(subsystemId)) : []);
  }

  async selectArchetype(archetypeId: string): Promise<void> {
    this.selectedArchetypeId.set(archetypeId);
    this.genericSolutions.set(
      archetypeId ? await this.request(() => this.api.genericSolutions(archetypeId)) : [],
    );
  }

  private async loadSystems(): Promise<void> {
    this.systems.set(await this.request(() => this.api.systems()));
  }

  private async request<T>(factory: () => import('rxjs').Observable<T>): Promise<T> {
    this.loading.set(true);
    this.error.set(null);
    try {
      return await firstValueFrom(factory());
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
      return [] as T;
    } finally {
      this.loading.set(false);
    }
  }
}
