import { Injectable, inject } from '@angular/core';
import type { CommercialSolutionDto } from '@viva/contracts';
import { Observable } from 'rxjs';
import { ApiClient } from './api-client';

@Injectable({ providedIn: 'root' })
export class AdminReviewApi {
  private readonly api = inject(ApiClient);
  private readonly base = '/admin/commercial-solutions';

  submitted(): Observable<CommercialSolutionDto[]> {
    return this.api.get(`${this.base}/submitted`);
  }

  approve(id: string): Observable<CommercialSolutionDto> {
    return this.api.post(`${this.base}/${id}/approve`, {});
  }

  reject(id: string, reason: string): Observable<CommercialSolutionDto> {
    return this.api.post(`${this.base}/${id}/reject`, { reason });
  }
}
