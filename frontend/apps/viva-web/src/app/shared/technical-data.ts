import { NgTemplateOutlet } from '@angular/common';
import { ChangeDetectionStrategy, Component, input } from '@angular/core';

type Entry = { key: string; value: unknown };

@Component({
  selector: 'app-technical-data',
  imports: [NgTemplateOutlet],
  template: `
    <ng-template #node let-value let-label="label">
      @if (label) {
        <dt>{{ label }}</dt>
      }
      <dd>
        @if (isNullish(value)) {
          <span class="empty">Unavailable</span>
        } @else if (isMetric(value)) {
          <span class="metric">{{ metricValue(value) }} <small>{{ metricUnit(value) }}</small></span>
        } @else if (isArray(value)) {
          @if (value.length === 0) {
            <span class="empty">No values</span>
          } @else {
            <ol class="json-list">
              @for (item of value; track $index) {
                <li>
                  <ng-container *ngTemplateOutlet="node; context: { $implicit: item }" />
                </li>
              }
            </ol>
          }
        } @else if (isObject(value)) {
          @if (entries(value).length === 0) {
            <span class="empty">No data</span>
          } @else {
            <dl class="json-object">
              @for (entry of entries(value); track entry.key) {
                <ng-container
                  *ngTemplateOutlet="node; context: { $implicit: entry.value, label: labelFor(entry.key) }"
                />
              }
            </dl>
          }
        } @else if (isBoolean(value)) {
          <span>{{ value ? 'Yes' : 'No' }}</span>
        } @else {
          <span>{{ value }}</span>
        }
      </dd>
    </ng-template>

    <section class="technical-section">
      @if (title()) {
        <h3>{{ title() }}</h3>
      }
      <ng-container *ngTemplateOutlet="node; context: { $implicit: data() }" />
    </section>
  `,
  styles: [
    `
      :host {
        display: block;
      }
      .technical-section {
        display: grid;
        gap: 0.6rem;
      }
      h3 {
        margin: 0;
        font-size: 1rem;
      }
      dd {
        margin: 0;
      }
      dt {
        color: #55615b;
        font-size: 0.78rem;
        font-weight: 750;
        text-transform: uppercase;
      }
      .json-object {
        display: grid;
        grid-template-columns: minmax(8rem, 0.35fr) minmax(0, 1fr);
        gap: 0.45rem 0.75rem;
        margin: 0;
      }
      .json-object .json-object {
        grid-template-columns: minmax(7rem, 0.32fr) minmax(0, 1fr);
      }
      .json-list {
        display: grid;
        gap: 0.4rem;
        margin: 0;
        padding-left: 1.25rem;
      }
      .empty {
        color: #78827b;
      }
      .metric {
        font-weight: 700;
      }
      small {
        color: #66726a;
        font-weight: 500;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TechnicalDataComponent {
  readonly data = input<unknown>(null);
  readonly title = input<string | null>(null);

  isNullish(value: unknown): value is null | undefined {
    return value === null || value === undefined;
  }

  isArray(value: unknown): value is unknown[] {
    return Array.isArray(value);
  }

  isObject(value: unknown): value is Record<string, unknown> {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }

  isBoolean(value: unknown): value is boolean {
    return typeof value === 'boolean';
  }

  entries(value: Record<string, unknown>): Entry[] {
    return Object.entries(value).map(([key, entryValue]) => ({ key, value: entryValue }));
  }

  labelFor(key: string): string {
    return key.replaceAll('_', ' ');
  }

  isMetric(value: unknown): value is { value: unknown; unit: unknown } {
    return this.isObject(value) && 'value' in value && 'unit' in value;
  }

  metricValue(value: { value: unknown }): string {
    return String(value.value);
  }

  metricUnit(value: { unit: unknown }): string {
    return String(value.unit);
  }
}
