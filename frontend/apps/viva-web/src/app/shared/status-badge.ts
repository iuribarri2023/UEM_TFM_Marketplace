import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import type { CommercialSolutionStatus } from '@viva/contracts';

@Component({
  selector: 'app-status-badge',
  template: `<span class="badge" [class]="status().toLowerCase()">{{ status() }}</span>`,
  styles: [
    `
      .badge {
        display: inline-flex;
        min-width: 5.5rem;
        justify-content: center;
        border: 1px solid #aab5ad;
        border-radius: 999px;
        padding: 0.2rem 0.55rem;
        background: #fff;
        font-size: 0.78rem;
        font-weight: 750;
      }
      .draft {
        background: #f3f5f1;
      }
      .submitted {
        border-color: #8fa8c2;
        background: #eef5fb;
      }
      .approved {
        border-color: #85b597;
        background: #edf8f0;
      }
      .rejected {
        border-color: #d29b95;
        background: #fff2f0;
      }
      .archived {
        border-color: #b5b0a6;
        background: #f3efe7;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StatusBadgeComponent {
  readonly status = input.required<CommercialSolutionStatus>();
}
