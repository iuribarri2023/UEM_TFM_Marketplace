import { AuthTokenStore } from './auth-token.store';

describe('AuthTokenStore', () => {
  beforeEach(() => sessionStorage.clear());

  it('restores tokens from sessionStorage', () => {
    const store = new AuthTokenStore();
    store.write({ access_token: 'access', refresh_token: 'refresh' });

    expect(store.read()).toEqual({ access_token: 'access', refresh_token: 'refresh' });
  });
});
