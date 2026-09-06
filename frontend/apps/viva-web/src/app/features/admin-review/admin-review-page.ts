import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import type { AssetDto, CommercialSolutionDto, GenericSolutionDto, ManufacturerDto } from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { AdminReviewApi } from '../../core/api/admin-review.api';
import { CatalogueApi } from '../../core/api/catalogue.api';
import { MarketplaceApi } from '../../core/api/marketplace.api';
import { normalizeApiError, userMessageForError } from '../../core/errors/api-error';
import { AssetListComponent } from '../../shared/asset-list';
import { StatusBadgeComponent } from '../../shared/status-badge';
import { TechnicalDataComponent } from '../../shared/technical-data';
import { IfcViewerHostComponent } from '../bim/ifc-viewer-host';

@Component({
  imports: [ReactiveFormsModule, AssetListComponent, StatusBadgeComponent, TechnicalDataComponent, IfcViewerHostComponent],
  template: `
    <section class="page-header">
      <div>
        <h1>Admin review</h1>
        <p>Submitted queue using the existing list endpoint as the detail source.</p>
      </div>
      <button type="button" class="secondary" (click)="load()">Refresh queue</button>
    </section>

    @if (error()) {
      <p class="error" aria-live="assertive">{{ error() }}</p>
    }

    <section class="review-layout">
      <aside class="panel queue">
        <h2>Submitted</h2>
        @for (item of queue(); track item.id) {
          <button type="button" [class.active]="item.id === selectedId()" (click)="select(item)">
            <strong>{{ item.code }}</strong>
            <span>{{ item.name_es }}</span>
          </button>
        } @empty {
          <p class="muted">No submitted commercial solutions.</p>
        }
      </aside>

      <section class="panel">
        @if (!selected()) {
          <p class="muted">Select a submitted item.</p>
        } @else {
          @let item = selected()!;
          <div class="page-header">
            <div>
              <p class="muted">{{ item.code }} · {{ item.submitted_at || 'Submitted' }}</p>
              <h2>{{ item.name_es }}</h2>
              <app-status-badge [status]="item.status" />
              <p>{{ item.description || 'No description.' }}</p>
              <p><strong>Manufacturer:</strong> {{ manufacturerName(item.manufacturer_id) }}</p>
              <p><strong>Generic:</strong> {{ generic()?.code || item.generic_solution_id }} {{ generic()?.name_es }}</p>
            </div>
            <div class="actions">
              <button type="button" class="primary" (click)="approve(item)">Approve</button>
            </div>
          </div>

          <label class="field">
            <span>Reject reason</span>
            <textarea [formControl]="reason" maxlength="2000"></textarea>
          </label>
          <button type="button" class="danger" [disabled]="reason.invalid" (click)="reject(item)">
            Reject
          </button>

          <section class="grid two">
            <div>
              <h3>Technical data</h3>
              <app-technical-data [data]="item.technical_data" />
            </div>
            <div>
              <h3>Assets</h3>
              <app-asset-list [assets]="item.assets" (preview)="selectedIfc.set($event)" />
            </div>
          </section>

          @if (selectedIfc()) {
            <app-ifc-viewer-host [asset]="selectedIfc()" />
          }
        }
      </section>
    </section>
  `,
  styles: [
    `
      .review-layout {
        display: grid;
        grid-template-columns: 22rem minmax(0, 1fr);
        gap: 1rem;
      }
      .queue {
        align-self: start;
      }
      .queue button {
        display: grid;
        width: 100%;
        gap: 0.25rem;
        margin-bottom: 0.45rem;
        border: 1px solid #d6ddd2;
        border-radius: 6px;
        padding: 0.65rem;
        background: #fff;
        text-align: left;
      }
      .queue button.active,
      .queue button:hover {
        background: #edf3ec;
      }
      @media (max-width: 960px) {
        .review-layout {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminReviewPage {
  private readonly api = inject(AdminReviewApi);
  private readonly marketplaceApi = inject(MarketplaceApi);
  private readonly catalogueApi = inject(CatalogueApi);
  readonly queue = signal<CommercialSolutionDto[]>([]);
  readonly selectedId = signal<string | null>(null);
  readonly manufacturers = signal<ManufacturerDto[]>([]);
  readonly generic = signal<GenericSolutionDto | null>(null);
  readonly selectedIfc = signal<AssetDto | null>(null);
  readonly error = signal<string | null>(null);
  readonly reason = new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.maxLength(2000)] });
  readonly selected = computed(() => this.queue().find((item) => item.id === this.selectedId()) ?? null);

  constructor() {
    void this.load();
  }

  async load(): Promise<void> {
    try {
      const [queue, manufacturers] = await Promise.all([
        firstValueFrom(this.api.submitted()),
        firstValueFrom(this.marketplaceApi.manufacturers()).catch(() => []),
      ]);
      this.queue.set(queue);
      this.manufacturers.set(manufacturers);
      this.selectedId.set(queue[0]?.id ?? null);
      if (queue[0]) {
        await this.select(queue[0]);
      }
      this.error.set(null);
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
    }
  }

  async select(item: CommercialSolutionDto): Promise<void> {
    this.selectedId.set(item.id);
    this.reason.setValue('');
    this.selectedIfc.set(item.assets.find((asset) => asset.format === 'ifc') ?? null);
    try {
      this.generic.set(await firstValueFrom(this.catalogueApi.genericSolution(item.generic_solution_id)));
    } catch {
      this.generic.set(null);
    }
  }

  manufacturerName(id: string): string {
    return this.manufacturers().find((item) => item.id === id)?.name ?? id;
  }

  async approve(item: CommercialSolutionDto): Promise<void> {
    await this.review(async () => {
      await firstValueFrom(this.api.approve(item.id));
    });
  }

  async reject(item: CommercialSolutionDto): Promise<void> {
    if (this.reason.invalid) {
      return;
    }
    await this.review(async () => {
      await firstValueFrom(this.api.reject(item.id, this.reason.value));
    });
  }

  private async review(work: () => Promise<void>): Promise<void> {
    try {
      await work();
      await this.load();
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
      await this.load();
    }
  }
}
