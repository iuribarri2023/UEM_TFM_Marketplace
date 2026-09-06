import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import type { AssetDto, CommercialSolutionDto, GenericSolutionDto } from '@viva/contracts';
import { actionsForCommercialSolution, buildAssetUploadFormData, patchCommercialSolutionPayload } from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { CatalogueApi } from '../../core/api/catalogue.api';
import { ManufacturerSolutionsApi } from '../../core/api/manufacturer-solutions.api';
import { normalizeApiError, userMessageForError } from '../../core/errors/api-error';
import { AssetListComponent } from '../../shared/asset-list';
import { StatusBadgeComponent } from '../../shared/status-badge';
import { TechnicalDataComponent } from '../../shared/technical-data';
import { IfcViewerHostComponent } from '../bim/ifc-viewer-host';
import { jsonObjectValidator, parseJsonObject } from './solution-form';

@Component({
  imports: [
    ReactiveFormsModule,
    RouterLink,
    AssetListComponent,
    StatusBadgeComponent,
    TechnicalDataComponent,
    IfcViewerHostComponent,
  ],
  template: `
    @if (error()) {
      <p class="error" aria-live="assertive">{{ error() }}</p>
    }
    @if (!solution()) {
      <div class="skeleton"></div>
    } @else {
      @let current = solution()!;
      @let actions = actionState();
      <section class="page-header">
        <div>
          <p class="muted">{{ current.code }}</p>
          <h1>{{ current.name_es }}</h1>
          <app-status-badge [status]="current.status" />
        </div>
        <a class="button secondary" routerLink="/manufacturer/solutions">Back</a>
      </section>

      @if (actions.editResetsToDraft) {
        <p class="success">Saving metadata for this status creates a new DRAFT state before assets can be changed or resubmitted.</p>
      }
      @if (current.status === 'SUBMITTED' || current.status === 'ARCHIVED') {
        <p class="error">Metadata and assets cannot be edited while this solution is {{ current.status }}.</p>
      }
      @if (current.rejection_reason) {
        <p class="error">Review feedback: {{ current.rejection_reason }}</p>
      }

      <section class="grid two">
        <form class="panel form-grid" [formGroup]="form" (ngSubmit)="save()">
          <label class="field">
            <span>Generic solution (read-only)</span>
            <input [value]="genericLabel()" readonly />
          </label>
          <label class="field">
            <span>Code</span>
            <input formControlName="code" maxlength="64" />
          </label>
          <label class="field">
            <span>Name ES</span>
            <input formControlName="name_es" maxlength="255" />
          </label>
          <label class="field wide">
            <span>Description</span>
            <textarea formControlName="description"></textarea>
          </label>
          <label class="field wide">
            <span>technical_data JSON object</span>
            <textarea formControlName="technical_data"></textarea>
          </label>
          @if (form.controls.technical_data.hasError('jsonObject')) {
            <p class="error wide">technical_data must be a JSON object.</p>
          }
          <button type="submit" class="primary" [disabled]="form.invalid || !actions.canEditMetadata || saving()">
            Save metadata
          </button>
        </form>

        <section class="panel">
          <h2>Asset upload</h2>
          @if (!actions.canChangeAssets) {
            <p class="muted">Assets may be changed only for DRAFT or REJECTED solutions.</p>
          } @else {
            <form class="upload-form" (ngSubmit)="upload()">
              <label class="field">
                <span>File</span>
                <input type="file" accept=".ifc,.pdf,.png,.jpg,.jpeg,.webp" (change)="selectFile($event)" />
              </label>
              <label class="field">
                <span>Code</span>
                <input [formControl]="assetCode" />
              </label>
              <button type="submit" class="primary" [disabled]="!selectedFile() || uploading()">Upload asset</button>
            </form>
          }
          <app-technical-data title="Current technical data" [data]="current.technical_data" />
        </section>
      </section>

      <section class="panel">
        <div class="page-header">
          <div>
            <h2>Assets</h2>
            <p class="muted">
              Backend-valid IFC:
              {{ actions.hasBackendValidIfc ? 'Yes' : 'No' }}
            </p>
          </div>
          <div class="actions">
            <button type="button" class="primary" [disabled]="!actions.canSubmit || submitting()" (click)="submit()">
              Submit for review
            </button>
            @if (actions.canDelete) {
              <button type="button" class="danger" (click)="deleteSolution()">Delete solution</button>
            }
          </div>
        </div>
        @if (!actions.hasBackendValidIfc && (current.status === 'DRAFT' || current.status === 'REJECTED')) {
          <p class="error">A backend-valid IFC asset is required before submission.</p>
        }
        <app-asset-list
          [assets]="assets()"
          [deletable]="actions.canChangeAssets"
          (preview)="selectedIfc.set($event)"
          (remove)="deleteAsset($event)"
        />
      </section>

      @if (selectedIfc()) {
        <app-ifc-viewer-host [asset]="selectedIfc()" />
      }
    }
  `,
  styles: [
    `
      .form-grid,
      .upload-form {
        display: grid;
        gap: 1rem;
      }
      .wide {
        grid-column: 1 / -1;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ManufacturerSolutionEditPage {
  readonly id = input.required<string>();
  private readonly api = inject(ManufacturerSolutionsApi);
  private readonly catalogueApi = inject(CatalogueApi);
  private readonly router = inject(Router);

  readonly solution = signal<CommercialSolutionDto | null>(null);
  readonly assets = signal<AssetDto[]>([]);
  readonly generic = signal<GenericSolutionDto | null>(null);
  readonly selectedIfc = signal<AssetDto | null>(null);
  readonly selectedFile = signal<File | null>(null);
  readonly error = signal<string | null>(null);
  readonly saving = signal(false);
  readonly uploading = signal(false);
  readonly submitting = signal(false);
  readonly assetCode = new FormControl('', { nonNullable: true });

  readonly actionState = computed(() =>
    actionsForCommercialSolution({ status: this.solution()?.status ?? 'ARCHIVED', assets: this.assets() }),
  );

  readonly form = new FormGroup({
    code: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.maxLength(64)] }),
    name_es: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.maxLength(255)] }),
    description: new FormControl('', { nonNullable: true }),
    technical_data: new FormControl('{}', { nonNullable: true, validators: [jsonObjectValidator] }),
  });

  constructor() {
    queueMicrotask(() => void this.reload());
  }

  genericLabel(): string {
    const generic = this.generic();
    return generic ? `${generic.code} · ${generic.name_es}` : this.solution()?.generic_solution_id ?? '';
  }

  selectFile(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile.set(input.files?.item(0) ?? null);
  }

  async save(): Promise<void> {
    if (this.form.invalid || !this.solution()) {
      return;
    }
    const technicalData = parseJsonObject(this.form.controls.technical_data.value) ?? {};
    const payload = patchCommercialSolutionPayload({
      ...this.form.getRawValue(),
      technical_data: technicalData,
    });
    this.saving.set(true);
    await this.mutate(async () => {
      await firstValueFrom(this.api.patch(this.id(), payload));
      await this.reload();
    });
    this.saving.set(false);
  }

  async upload(): Promise<void> {
    const file = this.selectedFile();
    if (!file) {
      return;
    }
    this.uploading.set(true);
    await this.mutate(async () => {
      await firstValueFrom(
        this.api.uploadAsset(
          this.id(),
          buildAssetUploadFormData({ file, code: this.assetCode.value || null }),
        ),
      );
      this.selectedFile.set(null);
      this.assetCode.setValue('');
      await this.reload();
    });
    this.uploading.set(false);
  }

  async submit(): Promise<void> {
    this.submitting.set(true);
    await this.mutate(async () => {
      await firstValueFrom(this.api.submit(this.id()));
      await this.reload();
    });
    this.submitting.set(false);
  }

  async deleteAsset(asset: AssetDto): Promise<void> {
    if (!confirm(`Delete asset ${asset.original_filename}?`)) {
      return;
    }
    await this.mutate(async () => {
      await firstValueFrom(this.api.deleteAsset(this.id(), asset.id));
      await this.reload();
    });
  }

  async deleteSolution(): Promise<void> {
    const solution = this.solution();
    if (!solution || !confirm(`Delete solution ${solution.code}?`)) {
      return;
    }
    await this.mutate(async () => {
      await firstValueFrom(this.api.delete(this.id()));
      await this.router.navigate(['/manufacturer/solutions']);
    });
  }

  private async reload(): Promise<void> {
    const [solution, assets] = await Promise.all([
      firstValueFrom(this.api.get(this.id())),
      firstValueFrom(this.api.assets(this.id())),
    ]);
    this.solution.set({ ...solution, assets });
    this.assets.set(assets);
    this.selectedIfc.set(assets.find((asset) => asset.format === 'ifc') ?? null);
    this.form.setValue({
      code: solution.code,
      name_es: solution.name_es,
      description: solution.description ?? '',
      technical_data: JSON.stringify(solution.technical_data ?? {}, null, 2),
    });
    this.generic.set(await firstValueFrom(this.catalogueApi.genericSolution(solution.generic_solution_id)));
  }

  private async mutate(work: () => Promise<void>): Promise<void> {
    this.error.set(null);
    try {
      await work();
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
      try {
        await this.reload();
      } catch {
        // Keep the original action error visible.
      }
    }
  }
}
