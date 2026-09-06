import { Injectable, inject } from '@angular/core';
import type { TokenResponseDto } from '@viva/contracts';
import { Observable, finalize, shareReplay, tap, throwError } from 'rxjs';
import { AuthApi } from './auth.api';
import { AuthTokenStore } from './auth-token.store';

@Injectable({ providedIn: 'root' })
export class AuthRefreshService {
  private readonly authApi = inject(AuthApi);
  private readonly tokenStore = inject(AuthTokenStore);
  private refreshRequest$: Observable<TokenResponseDto> | null = null;

  refreshOnce(): Observable<TokenResponseDto> {
    const tokens = this.tokenStore.read();
    if (!tokens) {
      return throwError(() => new Error('No refresh token is available.'));
    }
    if (!this.refreshRequest$) {
      this.refreshRequest$ = this.authApi.refresh({ refresh_token: tokens.refresh_token }).pipe(
        tap((nextTokens) => this.tokenStore.write(nextTokens)),
        finalize(() => {
          this.refreshRequest$ = null;
        }),
        shareReplay({ bufferSize: 1, refCount: false }),
      );
    }
    return this.refreshRequest$;
  }
}
