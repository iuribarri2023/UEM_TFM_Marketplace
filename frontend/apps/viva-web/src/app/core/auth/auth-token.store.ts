import { Injectable } from '@angular/core';
import type { TokenResponseDto } from '@viva/contracts';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

const ACCESS_TOKEN_KEY = 'viva.access_token';
const REFRESH_TOKEN_KEY = 'viva.refresh_token';

@Injectable({ providedIn: 'root' })
export class AuthTokenStore {
  read(): AuthTokens | null {
    const access = sessionStorage.getItem(ACCESS_TOKEN_KEY);
    const refresh = sessionStorage.getItem(REFRESH_TOKEN_KEY);
    return access && refresh ? { access_token: access, refresh_token: refresh } : null;
  }

  write(tokens: TokenResponseDto | AuthTokens): void {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }

  clear(): void {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}
