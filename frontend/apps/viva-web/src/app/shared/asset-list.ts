import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import type { AssetDto } from '@viva/contracts';
import { TechnicalDataComponent } from './technical-data';

@Component({
  selector: 'app-asset-list',
  imports: [TechnicalDataComponent],
  template: `
    @if (assets().length === 0) {
      <p class="muted">No assets are linked.</p>
    } @else {
      <div class="asset-list">
        @for (asset of assets(); track asset.id) {
          <article class="asset">
            <div>
              <h4>{{ asset.original_filename }}</h4>
              <p class="muted">
                {{ asset.format }} · {{ asset.asset_type }} · {{ asset.role }} · {{ asset.size }} bytes
              </p>
              @if (asset.format === 'ifc') {
                <p>
                  IFC validation:
                  <strong>{{ asset.validation_data?.['valid'] === true ? 'valid' : 'not accepted' }}</strong>
                </p>
                <app-technical-data title="IFC extraction" [data]="asset.extraction_data" />
              }
            </div>
            <div class="actions">
              @if (asset.format === 'ifc') {
                <button type="button" class="secondary" (click)="preview.emit(asset)">Preview IFC</button>
              }
              @if (deletable()) {
                <button type="button" class="danger" (click)="remove.emit(asset)">Delete</button>
              }
            </div>
          </article>
        }
      </div>
    }
  `,
  styles: [
    `
      .asset-list {
        display: grid;
        gap: 0.75rem;
      }
      .asset {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 1rem;
        align-items: start;
        border: 1px solid #d6ddd2;
        border-radius: 8px;
        padding: 0.85rem;
        background: #fff;
      }
      h4 {
        margin: 0 0 0.25rem;
      }
      p {
        margin: 0.15rem 0;
      }
      @media (max-width: 760px) {
        .asset {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AssetListComponent {
  readonly assets = input.required<AssetDto[]>();
  readonly deletable = input(false);
  readonly preview = output<AssetDto>();
  readonly remove = output<AssetDto>();
}
