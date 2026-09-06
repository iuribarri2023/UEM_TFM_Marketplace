import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import type { AssetDto } from '@viva/contracts';
import { AssetApi } from '../../core/api/asset.api';
import { IFC_VIEWER_FACTORY, IfcViewerHostComponent } from './ifc-viewer-host';

const asset: AssetDto = {
  id: 'asset-1',
  code: null,
  original_filename: 'model.ifc',
  mime_type: 'application/octet-stream',
  size: 1,
  sha256: 'x',
  asset_type: 'bim_model',
  format: 'ifc',
  role: 'primary_commercial_model',
  uploaded_by: null,
  validation_data: { valid: true },
  extraction_data: null,
  created_at: '',
  updated_at: '',
};

describe('IfcViewerHostComponent', () => {
  let fixture: ComponentFixture<IfcViewerHostComponent>;
  let viewer: {
    initialize: ReturnType<typeof vi.fn>;
    load: ReturnType<typeof vi.fn>;
    fitToModel: ReturnType<typeof vi.fn>;
    dispose: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    viewer = {
      initialize: vi.fn().mockResolvedValue(undefined),
      load: vi.fn().mockResolvedValue(undefined),
      fitToModel: vi.fn().mockResolvedValue(undefined),
      dispose: vi.fn().mockResolvedValue(undefined),
    };
    TestBed.configureTestingModule({
      imports: [IfcViewerHostComponent],
      providers: [
        {
          provide: AssetApi,
          useValue: { downloadArrayBuffer: () => of(new Uint8Array([1, 2, 3]).buffer) },
        },
        { provide: IFC_VIEWER_FACTORY, useValue: async () => viewer },
      ],
    });
    fixture = TestBed.createComponent(IfcViewerHostComponent);
  });

  it('downloads bytes and calls viewer lifecycle', async () => {
    fixture.componentRef.setInput('asset', asset);
    fixture.detectChanges();
    await fixture.whenStable();
    await new Promise((resolve) => setTimeout(resolve));

    expect(viewer.initialize).toHaveBeenCalled();
    expect(viewer.load).toHaveBeenCalledWith({
      id: 'asset-1',
      name: 'model.ifc',
      bytes: new Uint8Array([1, 2, 3]),
    });

    fixture.destroy();
    expect(viewer.dispose).toHaveBeenCalled();
  });
});
