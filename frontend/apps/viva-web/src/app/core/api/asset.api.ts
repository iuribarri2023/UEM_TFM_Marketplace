import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClient } from './api-client';

@Injectable({ providedIn: 'root' })
export class AssetApi {
  private readonly api = inject(ApiClient);

  downloadArrayBuffer(assetId: string): Observable<ArrayBuffer> {
    return this.api.downloadArrayBuffer(`/assets/${assetId}/download`);
  }
}
