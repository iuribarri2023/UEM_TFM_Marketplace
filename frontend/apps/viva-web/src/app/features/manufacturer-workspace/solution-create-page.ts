import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import type { GenericSolutionSummaryDto } from '@viva/contracts';
import { createCommercialSolutionPayload } from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { CatalogueApi } from '../../core/api/catalogue.api';
import { ManufacturerSolutionsApi } from '../../core/api/manufacturer-solutions.api';
import { normalizeApiError, userMessageForError } from '../../core/errors/api-error';
import { jsonObjectValidator, parseJsonObject } from './solution-form';

@Component({
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <section class="page-header">
      <div>
        <h1>Create commercial draft</h1>
        <p>The create request sends only the backend-supported fields; ownership comes from the authenticated user.</p>
      </div>
      <a class="button secondary" routerLink="/manufacturer/solutions">Back</a>
    </section>

    @if (error()) {
      <p class="error" aria-live="assertive">{{ error() }}</p>
    }

    <form class="panel form-grid" [formGroup]="form" (ngSubmit)="submit()">
      <label class="field">
        <span>Generic solution</span>
        <select formControlName="generic_solution_id">
          <option value="">Select generic solution</option>
          @for (generic of generics(); track generic.id) {
            <option [value]="generic.id">{{ generic.code }} · {{ generic.name_es }}</option>
          }
        </select>
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
        <p class="error wide">technical_data must be a JSON object, not an array or scalar.</p>
      }
      <button type="submit" class="primary" [disabled]="form.invalid || saving()">Create draft</button>
    </form>
  `,
  styles: [
    `
      .form-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
      }
      .wide {
        grid-column: 1 / -1;
      }
      @media (max-width: 760px) {
        .form-grid {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ManufacturerSolutionCreatePage {
  private readonly catalogueApi = inject(CatalogueApi);
  private readonly api = inject(ManufacturerSolutionsApi);
  private readonly router = inject(Router);
  readonly generics = signal<GenericSolutionSummaryDto[]>([]);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = new FormGroup({
    generic_solution_id: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    code: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.maxLength(64)] }),
    name_es: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.maxLength(255)] }),
    description: new FormControl('', { nonNullable: true }),
    technical_data: new FormControl('{}', { nonNullable: true, validators: [jsonObjectValidator] }),
  });

  constructor() {
    void this.loadGenerics();
  }

  async submit(): Promise<void> {
    if (this.form.invalid) {
      return;
    }
    const technicalData = parseJsonObject(this.form.controls.technical_data.value) ?? {};
    const payload = createCommercialSolutionPayload({
      ...this.form.getRawValue(),
      technical_data: technicalData,
    });
    this.saving.set(true);
    try {
      const created = await firstValueFrom(this.api.create(payload));
      await this.router.navigate(['/manufacturer/solutions', created.id, 'edit']);
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
    } finally {
      this.saving.set(false);
    }
  }

  private async loadGenerics(): Promise<void> {
    try {
      this.generics.set(await firstValueFrom(this.catalogueApi.genericSolutions()));
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
    }
  }
}
