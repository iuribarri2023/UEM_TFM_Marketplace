import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthStore } from '../../core/auth/auth.store';

@Component({
  imports: [ReactiveFormsModule],
  template: `
    <section class="page-header">
      <div>
        <h1>Login</h1>
        <p>Use a backend manufacturer or administrator account.</p>
      </div>
    </section>

    <form class="panel login-form" [formGroup]="form" (ngSubmit)="submit()">
      <label class="field">
        <span>Email</span>
        <input type="email" formControlName="email" autocomplete="username" />
      </label>
      <label class="field">
        <span>Password</span>
        <input type="password" formControlName="password" autocomplete="current-password" />
      </label>
      @if (auth.error()) {
        <p class="error" aria-live="assertive">{{ auth.error() }}</p>
      }
      <button type="submit" class="primary" [disabled]="form.invalid || auth.loading()">
        {{ auth.loading() ? 'Signing in' : 'Login' }}
      </button>
    </form>
  `,
  styles: [
    `
      .login-form {
        display: grid;
        gap: 1rem;
        max-width: 30rem;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginPage {
  readonly auth = inject(AuthStore);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly form = new FormGroup({
    email: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.email] }),
    password: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
  });

  async submit(): Promise<void> {
    if (this.form.invalid) {
      return;
    }
    const ok = await this.auth.login(this.form.getRawValue());
    if (ok) {
      const user = this.auth.user();
      const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
      await this.router.navigateByUrl(
        returnUrl || (user?.role === 'ADMIN' ? '/admin/review' : '/manufacturer/solutions'),
      );
    }
  }
}
