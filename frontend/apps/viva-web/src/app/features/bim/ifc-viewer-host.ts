import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
  InjectionToken,
  inject,
  input,
  signal,
} from '@angular/core';
import type { AssetDto } from '@viva/contracts';
import { firstValueFrom } from 'rxjs';
import { AssetApi } from '../../core/api/asset.api';

type ViewerInstance = import('@viva/ifc-viewer').VivaIfcViewer;
type ViewerCtor = new () => ViewerInstance;
type ViewerFactory = () => Promise<ViewerInstance>;

export const IFC_VIEWER_FACTORY = new InjectionToken<ViewerFactory>('IFC_VIEWER_FACTORY', {
  providedIn: 'root',
  factory: () => async () => {
    const module = await import('@viva/ifc-viewer');
    const ViewerClass = module.VivaIfcViewer as ViewerCtor;
    return new ViewerClass();
  },
});

@Component({
  selector: 'app-ifc-viewer-host',
  template: `
    <section class="viewer-shell" aria-label="IFC viewer">
      <div class="viewer-toolbar">
        <div>
          <strong>{{ asset()?.original_filename || 'IFC model' }}</strong>
          <span aria-live="polite">{{ state() }}</span>
        </div>
        <div class="actions">
          <button type="button" class="secondary" (click)="fit()">Fit</button>
          <button type="button" class="secondary" (click)="reload()">Reload</button>
        </div>
      </div>
      <div #container class="viewer-canvas"></div>
      @if (error()) {
        <p class="error">{{ error() }}</p>
      }
    </section>
  `,
  styles: [
    `
      .viewer-shell {
        overflow: hidden;
        border: 1px solid #bdc8bf;
        border-radius: 8px;
        background: #fbfcf8;
      }
      .viewer-toolbar {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        align-items: center;
        padding: 0.75rem;
        border-bottom: 1px solid #d8ded6;
      }
      .viewer-toolbar span {
        margin-left: 0.75rem;
        color: #66726a;
      }
      .viewer-canvas {
        width: 100%;
        height: min(62vh, 620px);
        min-height: 360px;
        background: #e9ede6;
      }
      .error {
        margin: 0.75rem;
      }
      @media (max-width: 760px) {
        .viewer-toolbar {
          display: grid;
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IfcViewerHostComponent implements AfterViewInit, OnChanges, OnDestroy {
  readonly asset = input<AssetDto | null>(null);
  @ViewChild('container', { static: true }) private readonly container?: ElementRef<HTMLElement>;

  private readonly assetApi = inject(AssetApi);
  private readonly viewerFactory = inject(IFC_VIEWER_FACTORY);
  private viewer: ViewerInstance | null = null;
  private initialized = false;

  readonly state = signal('Idle');
  readonly error = signal<string | null>(null);

  async ngAfterViewInit(): Promise<void> {
    await this.ensureViewer();
    await this.loadAsset();
  }

  async ngOnChanges(changes: SimpleChanges): Promise<void> {
    if (changes['asset'] && this.initialized) {
      await this.loadAsset();
    }
  }

  async reload(): Promise<void> {
    await this.loadAsset();
  }

  async fit(): Promise<void> {
    await this.viewer?.fitToModel();
  }

  async ngOnDestroy(): Promise<void> {
    await this.viewer?.dispose();
    this.viewer = null;
    this.initialized = false;
  }

  private async ensureViewer(): Promise<void> {
    if (this.viewer || !this.container?.nativeElement) {
      return;
    }
    this.state.set('Initializing viewer');
    this.viewer = await this.viewerFactory();
    await this.viewer.initialize(this.container.nativeElement);
    this.initialized = true;
  }

  private async loadAsset(): Promise<void> {
    const asset = this.asset();
    if (!asset || !this.viewer) {
      return;
    }
    this.error.set(null);
    this.state.set('Downloading IFC bytes');
    try {
      const buffer = await firstValueFrom(this.assetApi.downloadArrayBuffer(asset.id));
      this.state.set('Loading model');
      await this.viewer.load({
        id: asset.id,
        name: asset.original_filename,
        bytes: new Uint8Array(buffer),
      });
      await this.viewer.fitToModel();
      this.state.set('Ready');
    } catch (error) {
      this.error.set(error instanceof Error ? error.message : 'The IFC model could not be loaded.');
      this.state.set('Failed');
    }
  }
}
