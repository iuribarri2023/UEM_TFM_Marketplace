import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import type { CurrentUserDto } from '@viva/contracts';
import { adminGuard, manufacturerGuard } from './role.guards';
import { AuthStore } from './auth.store';

function authStoreWith(user: CurrentUserDto | null, status = 'authenticated'): Partial<AuthStore> {
  return {
    user: () => user,
    status: () => status,
    restoreSession: vi.fn().mockResolvedValue(undefined),
  } as unknown as Partial<AuthStore>;
}

describe('role guards', () => {
  it('allows manufacturers into manufacturer routes', async () => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        {
          provide: AuthStore,
          useValue: authStoreWith({
            id: 'u',
            email: 'm@test',
            role: 'MANUFACTURER',
            manufacturer_id: 'm',
          }),
        },
      ],
    });

    const result = await TestBed.runInInjectionContext(() =>
      manufacturerGuard({} as never, {} as never),
    );
    expect(result).toBe(true);
  });

  it('redirects non-admins away from admin routes', async () => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        {
          provide: AuthStore,
          useValue: authStoreWith({
            id: 'u',
            email: 'm@test',
            role: 'MANUFACTURER',
            manufacturer_id: 'm',
          }),
        },
      ],
    });

    const result = await TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));
    expect(result).toEqual(TestBed.inject(Router).createUrlTree(['/login']));
  });

  it('restores an unknown session before deciding', async () => {
    const auth = authStoreWith(null, 'unknown');
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: AuthStore, useValue: auth }],
    });

    await TestBed.runInInjectionContext(() => manufacturerGuard({} as never, {} as never));
    expect(auth.restoreSession).toHaveBeenCalled();
  });
});
