import { Injectable, inject } from '@angular/core';
import type {
  ArchetypeDto,
  GenericSolutionDto,
  GenericSolutionSummaryDto,
  SubsystemDto,
  SystemDto,
} from '@viva/contracts';
import { Observable } from 'rxjs';
import { ApiClient } from './api-client';

@Injectable({ providedIn: 'root' })
export class CatalogueApi {
  private readonly api = inject(ApiClient);

  systems(): Observable<SystemDto[]> {
    return this.api.get('/systems');
  }

  system(id: string): Observable<SystemDto> {
    return this.api.get(`/systems/${id}`);
  }

  subsystems(systemId?: string): Observable<SubsystemDto[]> {
    return this.api.get('/subsystems', { system_id: systemId });
  }

  subsystem(id: string): Observable<SubsystemDto> {
    return this.api.get(`/subsystems/${id}`);
  }

  archetypes(subsystemId?: string): Observable<ArchetypeDto[]> {
    return this.api.get('/archetypes', { subsystem_id: subsystemId });
  }

  archetype(id: string): Observable<ArchetypeDto> {
    return this.api.get(`/archetypes/${id}`);
  }

  genericSolutions(archetypeId?: string): Observable<GenericSolutionSummaryDto[]> {
    return this.api.get('/generic-solutions', { archetype_id: archetypeId });
  }

  genericSolution(id: string): Observable<GenericSolutionDto> {
    return this.api.get(`/generic-solutions/${id}`);
  }

  genericSolutionByCode(code: string): Observable<GenericSolutionDto> {
    return this.api.get(`/generic-solutions/by-code/${encodeURIComponent(code)}`);
  }
}
