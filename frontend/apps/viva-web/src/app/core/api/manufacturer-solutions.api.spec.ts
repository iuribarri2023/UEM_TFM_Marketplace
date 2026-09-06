import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { ManufacturerSolutionsApi } from './manufacturer-solutions.api';

describe('ManufacturerSolutionsApi', () => {
  let api: ManufacturerSolutionsApi;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(ManufacturerSolutionsApi);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('uploads multipart form data without changing field names', () => {
    const formData = new FormData();
    formData.append('file', new File(['x'], 'model.ifc'));
    formData.append('role', 'primary_commercial_model');
    formData.append('asset_type', 'bim_model');

    api.uploadAsset('solution-1', formData).subscribe();
    const request = http.expectOne('/api/v1/manufacturer/commercial-solutions/solution-1/assets');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBe(formData);
    expect(request.request.headers.has('Content-Type')).toBe(false);
    request.flush({ data: {} });
  });
});
