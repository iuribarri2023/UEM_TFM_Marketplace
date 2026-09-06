import { TestBed } from '@angular/core/testing';
import { Subject } from 'rxjs';
import { AuthApi } from './auth.api';
import { AuthRefreshService } from './auth-refresh.service';
import { AuthTokenStore } from './auth-token.store';

describe('AuthRefreshService', () => {
  it('deduplicates concurrent refresh calls', () => {
    const subject = new Subject<{ access_token: string; refresh_token: string; token_type: string }>();
    const refresh = vi.fn(() => subject.asObservable());
    TestBed.configureTestingModule({
      providers: [
        AuthRefreshService,
        { provide: AuthApi, useValue: { refresh } },
        {
          provide: AuthTokenStore,
          useValue: {
            read: () => ({ access_token: 'a1', refresh_token: 'r1' }),
            write: vi.fn(),
          },
        },
      ],
    });

    const service = TestBed.inject(AuthRefreshService);
    service.refreshOnce().subscribe();
    service.refreshOnce().subscribe();

    expect(refresh).toHaveBeenCalledTimes(1);
    subject.next({ access_token: 'a2', refresh_token: 'r2', token_type: 'Bearer' });
    subject.complete();
  });
});
