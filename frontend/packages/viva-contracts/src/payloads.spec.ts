import { describe, expect, it } from 'vitest';
import { buildAssetUploadFormData, createCommercialSolutionPayload, patchCommercialSolutionPayload } from './payloads';

describe('commercial payload helpers', () => {
  it('excludes manufacturer and server fields from create payloads', () => {
    const payload = createCommercialSolutionPayload({
      generic_solution_id: 'g',
      code: 'c',
      name_es: 'n',
      description: '',
      technical_data: { u: 1 },
      manufacturer_id: 'm',
      status: 'APPROVED',
      assets: [],
    });

    expect(payload).toEqual({
      generic_solution_id: 'g',
      code: 'c',
      name_es: 'n',
      description: null,
      technical_data: { u: 1 },
    });
    expect('manufacturer_id' in payload).toBe(false);
  });

  it('never includes generic_solution_id in patch payloads', () => {
    const payload = patchCommercialSolutionPayload({
      generic_solution_id: 'new',
      code: 'c',
      name_es: 'n',
      technical_data: { u: 1 },
    });

    expect(payload).toEqual({ code: 'c', name_es: 'n', technical_data: { u: 1 } });
    expect('generic_solution_id' in payload).toBe(false);
  });
});

describe('asset upload form data', () => {
  it('uses backend field names and defaults', () => {
    const file = new File(['x'], 'model.ifc');
    const formData = buildAssetUploadFormData({ file, code: 'A-1' });

    expect(formData.get('file')).toBe(file);
    expect(formData.get('role')).toBe('primary_commercial_model');
    expect(formData.get('asset_type')).toBe('bim_model');
    expect(formData.get('code')).toBe('A-1');
  });
});
