import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { AuthApi } from './auth.api';
import { AuthStore } from './auth.store';
import { AuthTokenStore } from './auth-token.store';

describe('AuthStore', () => {
  it('restores a session by verifying identity with auth/me', async () => {
    const tokenStore = {
      read: () => ({ access_token: 'a', refresh_token: 'r' }),
      clear: vi.fn(),
      write: vi.fn(),
    };
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        AuthStore,
        { provide: AuthTokenStore, useValue: tokenStore },
        {
          provide: AuthApi,
          useValue: {
            me: () => of({ id: 'u', email: 'm@test', role: 'MANUFACTURER', manufacturer_id: 'm' }),
          },
        },
      ],
    });

    const store = TestBed.inject(AuthStore);
    await store.restoreSession();

    expect(store.user()?.role).toBe('MANUFACTURER');
    expect(store.status()).toBe('authenticated');
  });

  it('clears invalid restored tokens', async () => {
    const tokenStore = {
      read: () => ({ access_token: 'a', refresh_token: 'r' }),
      clear: vi.fn(),
      write: vi.fn(),
    };
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        AuthStore,
        { provide: AuthTokenStore, useValue: tokenStore },
        { provide: AuthApi, useValue: { me: () => throwError(() => new Error('401')) } },
      ],
    });

    const store = TestBed.inject(AuthStore);
    await store.restoreSession();

    expect(tokenStore.clear).toHaveBeenCalled();
    expect(store.status()).toBe('anonymous');
  });
});
