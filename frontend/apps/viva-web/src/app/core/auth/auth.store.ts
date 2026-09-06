import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import type { CurrentUserDto, LoginRequestDto } from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { normalizeApiError, userMessageForError } from '../errors/api-error';
import { AuthApi } from './auth.api';
import { AuthTokenStore } from './auth-token.store';

type AuthStatus = 'unknown' | 'anonymous' | 'authenticated';

@Injectable({ providedIn: 'root' })
export class AuthStore {
  private readonly authApi = inject(AuthApi);
  private readonly tokenStore = inject(AuthTokenStore);
  private readonly router = inject(Router);

  readonly user = signal<CurrentUserDto | null>(null);
  readonly status = signal<AuthStatus>('unknown');
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly isAuthenticated = computed(() => this.status() === 'authenticated');

  async restoreSession(): Promise<void> {
    if (!this.tokenStore.read()) {
      this.user.set(null);
      this.status.set('anonymous');
      return;
    }
    this.loading.set(true);
    try {
      const user = await firstValueFrom(this.authApi.me());
      this.user.set(user);
      this.status.set('authenticated');
    } catch {
      this.tokenStore.clear();
      this.user.set(null);
      this.status.set('anonymous');
    } finally {
      this.loading.set(false);
    }
  }

  async login(payload: LoginRequestDto): Promise<boolean> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const tokens = await firstValueFrom(this.authApi.login(payload));
      this.tokenStore.write(tokens);
      const user = await firstValueFrom(this.authApi.me());
      this.user.set(user);
      this.status.set('authenticated');
      return true;
    } catch (error) {
      this.error.set(userMessageForError(normalizeApiError(error)));
      this.tokenStore.clear();
      this.user.set(null);
      this.status.set('anonymous');
      return false;
    } finally {
      this.loading.set(false);
    }
  }

  setAnonymous(): void {
    this.tokenStore.clear();
    this.user.set(null);
    this.status.set('anonymous');
  }

  logout(): void {
    this.setAnonymous();
    void this.router.navigate(['/login']);
  }
}
