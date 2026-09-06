import { Injectable, inject } from '@angular/core';
import type { CommercialSolutionDto, ManufacturerDto } from '@viva/contracts';
import { Observable } from 'rxjs';
import { ApiClient } from './api-client';

export interface MarketplaceFilters {
  system_id?: string | null;
  subsystem_id?: string | null;
  archetype_id?: string | null;
  generic_solution_id?: string | null;
  manufacturer_id?: string | null;
}

@Injectable({ providedIn: 'root' })
export class MarketplaceApi {
  private readonly api = inject(ApiClient);

  commercialSolutions(filters: MarketplaceFilters = {}): Observable<CommercialSolutionDto[]> {
    return this.api.get('/marketplace/commercial-solutions', { ...filters });
  }

  commercialSolution(id: string): Observable<CommercialSolutionDto> {
    return this.api.get(`/marketplace/commercial-solutions/${id}`);
  }

  manufacturers(): Observable<ManufacturerDto[]> {
    return this.api.get('/manufacturers');
  }

  manufacturer(id: string): Observable<ManufacturerDto> {
    return this.api.get(`/manufacturers/${id}`);
  }
}
