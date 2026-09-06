import { HttpErrorResponse, HttpHandlerFn, HttpRequest, HttpResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError, firstValueFrom, Subject } from 'rxjs';
import { AuthRefreshService } from './auth-refresh.service';
import { authInterceptor } from './auth.interceptor';
import { AuthStore } from './auth.store';
import { AuthTokenStore } from './auth-token.store';

describe('authInterceptor', () => {
  it('attaches bearer tokens', async () => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthTokenStore, useValue: { read: () => ({ access_token: 'access', refresh_token: 'refresh' }) } },
        { provide: AuthRefreshService, useValue: { refreshOnce: vi.fn() } },
        { provide: AuthStore, useValue: { setAnonymous: vi.fn() } },
      ],
    });

    const next: HttpHandlerFn = (request) => {
      expect(request.headers.get('Authorization')).toBe('Bearer access');
      return of(new HttpResponse({ status: 200 }));
    };

    await firstValueFrom(
      TestBed.runInInjectionContext(() => authInterceptor(new HttpRequest('GET', '/api/v1/systems'), next)),
    );
  });

  it('uses one refresh observable and retries waiting 401 requests once', async () => {
    const refresh$ = new Subject<{ access_token: string; refresh_token: string; token_type: string }>();
    const refreshOnce = vi.fn(() => refresh$.asObservable());
    let calls = 0;
    const next: HttpHandlerFn = (request) => {
      calls += 1;
      if (!request.headers.has('X-VIVA-Retried')) {
        return throwError(() => new HttpErrorResponse({ status: 401 }));
      }
      expect(request.headers.get('Authorization')).toBe('Bearer next');
      return of(new HttpResponse({ status: 200 }));
    };

    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthTokenStore, useValue: { read: () => ({ access_token: 'old', refresh_token: 'refresh' }) } },
        { provide: AuthRefreshService, useValue: { refreshOnce } },
        { provide: AuthStore, useValue: { setAnonymous: vi.fn() } },
      ],
    });

    const req = new HttpRequest('GET', '/api/v1/auth/me');
    const one = firstValueFrom(TestBed.runInInjectionContext(() => authInterceptor(req, next)));
    const two = firstValueFrom(TestBed.runInInjectionContext(() => authInterceptor(req, next)));
    refresh$.next({ access_token: 'next', refresh_token: 'new-refresh', token_type: 'Bearer' });
    refresh$.complete();

    await Promise.all([one, two]);
    expect(refreshOnce).toHaveBeenCalledTimes(2);
    expect(calls).toBe(4);
  });
});
