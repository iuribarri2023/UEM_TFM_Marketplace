import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  imports: [RouterLink],
  template: `
    <section class="panel">
      <h1>Page not found</h1>
      <p class="muted">The requested frontend route is not available.</p>
      <a class="button primary" routerLink="/catalogue">Go to catalogue</a>
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotFoundPage {}
