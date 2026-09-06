import { HttpErrorResponse, HttpHandlerFn, HttpRequest } from '@angular/common/http';
import { Injector, inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthRefreshService } from './auth-refresh.service';
import { AuthStore } from './auth.store';
import { AuthTokenStore } from './auth-token.store';

const SKIP_REFRESH_PATHS = ['/api/v1/auth/login', '/api/v1/auth/refresh'];
const RETRIED_HEADER = 'X-VIVA-Retried';

export function authInterceptor(req: HttpRequest<unknown>, next: HttpHandlerFn) {
  const tokenStore = inject(AuthTokenStore);
  const injector = inject(Injector);
  const tokens = tokenStore.read();
  const authedReq = tokens?.access_token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${tokens.access_token}` } })
    : req;

  return next(authedReq).pipe(
    catchError((error: unknown) => {
      const canRefresh =
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        !SKIP_REFRESH_PATHS.some((path) => req.url.includes(path)) &&
        !req.headers.has(RETRIED_HEADER) &&
        !!tokenStore.read()?.refresh_token;

      if (!canRefresh) {
        return throwError(() => error);
      }

      const refreshService = injector.get(AuthRefreshService);
      return refreshService.refreshOnce().pipe(
        switchMap((newTokens) => {
          const retryReq = req.clone({
            setHeaders: {
              Authorization: `Bearer ${newTokens.access_token}`,
              [RETRIED_HEADER]: '1',
            },
          });
          return next(retryReq);
        }),
        catchError((refreshError: unknown) => {
          const authStore = injector.get(AuthStore);
          const router = injector.get(Router);
          authStore.setAnonymous();
          void router.navigate(['/login']);
          return throwError(() => refreshError);
        }),
      );
    }),
  );
}
