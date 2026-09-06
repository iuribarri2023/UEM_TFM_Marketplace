import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import type { UserRole } from '@viva/contracts';
import { AuthStore } from './auth.store';

export const manufacturerGuard: CanActivateFn = () => guardRole('MANUFACTURER');
export const adminGuard: CanActivateFn = () => guardRole('ADMIN');

async function guardRole(role: UserRole): Promise<boolean | UrlTree> {
  const auth = inject(AuthStore);
  const router = inject(Router);
  if (auth.status() === 'unknown') {
    await auth.restoreSession();
  }
  const user = auth.user();
  if (user?.role === role) {
    return true;
  }
  return router.createUrlTree(['/login']);
}
