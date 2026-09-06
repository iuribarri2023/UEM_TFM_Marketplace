import { Injectable, inject } from '@angular/core';
import type {
  CurrentUserDto,
  LoginRequestDto,
  RefreshRequestDto,
  TokenResponseDto,
} from '@viva/contracts';
import { Observable } from 'rxjs';
import { ApiClient } from '../api/api-client';

@Injectable({ providedIn: 'root' })
export class AuthApi {
  private readonly api = inject(ApiClient);

  login(payload: LoginRequestDto): Observable<TokenResponseDto> {
    return this.api.post('/auth/login', payload);
  }

  refresh(payload: RefreshRequestDto): Observable<TokenResponseDto> {
    return this.api.post('/auth/refresh', payload);
  }

  me(): Observable<CurrentUserDto> {
    return this.api.get('/auth/me');
  }
}
