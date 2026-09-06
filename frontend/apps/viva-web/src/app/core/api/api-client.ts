import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import type { ApiEnvelope } from '@viva/contracts';
import { Observable, map } from 'rxjs';

export const API_BASE = '/api/v1';

export function unwrapEnvelope<T>(envelope: ApiEnvelope<T>): T {
  return envelope.data;
}

@Injectable({ providedIn: 'root' })
export class ApiClient {
  private readonly http = inject(HttpClient);

  get<T>(path: string, params?: Record<string, string | null | undefined>): Observable<T> {
    return this.http
      .get<ApiEnvelope<T>>(`${API_BASE}${path}`, { params: toHttpParams(params) })
      .pipe(map(unwrapEnvelope));
  }

  post<T>(path: string, body: unknown): Observable<T> {
    return this.http.post<ApiEnvelope<T>>(`${API_BASE}${path}`, body).pipe(map(unwrapEnvelope));
  }

  patch<T>(path: string, body: unknown): Observable<T> {
    return this.http.patch<ApiEnvelope<T>>(`${API_BASE}${path}`, body).pipe(map(unwrapEnvelope));
  }

  delete(path: string): Observable<void> {
    return this.http.delete<void>(`${API_BASE}${path}`);
  }

  downloadArrayBuffer(path: string): Observable<ArrayBuffer> {
    return this.http.get(`${API_BASE}${path}`, { responseType: 'arraybuffer' });
  }
}

function toHttpParams(params?: Record<string, string | null | undefined>): HttpParams | undefined {
  if (!params) {
    return undefined;
  }
  let httpParams = new HttpParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) {
      httpParams = httpParams.set(key, value);
    }
  }
  return httpParams;
}
