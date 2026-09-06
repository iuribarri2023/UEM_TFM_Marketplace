import { Injectable, inject } from '@angular/core';
import type {
  AssetDto,
  CommercialSolutionCreateDto,
  CommercialSolutionDto,
  CommercialSolutionPatchDto,
} from '@viva/contracts';
import { Observable } from 'rxjs';
import { ApiClient } from './api-client';

@Injectable({ providedIn: 'root' })
export class ManufacturerSolutionsApi {
  private readonly api = inject(ApiClient);
  private readonly base = '/manufacturer/commercial-solutions';

  list(): Observable<CommercialSolutionDto[]> {
    return this.api.get(this.base);
  }

  create(payload: CommercialSolutionCreateDto): Observable<CommercialSolutionDto> {
    return this.api.post(this.base, payload);
  }

  get(id: string): Observable<CommercialSolutionDto> {
    return this.api.get(`${this.base}/${id}`);
  }

  patch(id: string, payload: CommercialSolutionPatchDto): Observable<CommercialSolutionDto> {
    return this.api.patch(`${this.base}/${id}`, payload);
  }

  delete(id: string): Observable<void> {
    return this.api.delete(`${this.base}/${id}`);
  }

  submit(id: string): Observable<CommercialSolutionDto> {
    return this.api.post(`${this.base}/${id}/submit`, {});
  }

  assets(id: string): Observable<AssetDto[]> {
    return this.api.get(`${this.base}/${id}/assets`);
  }

  uploadAsset(id: string, formData: FormData): Observable<AssetDto> {
    return this.api.post(`${this.base}/${id}/assets`, formData);
  }

  deleteAsset(solutionId: string, assetId: string): Observable<void> {
    return this.api.delete(`${this.base}/${solutionId}/assets/${assetId}`);
  }
}
