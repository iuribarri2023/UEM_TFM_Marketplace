import { describe, expect, it } from 'vitest';
import { actionsForCommercialSolution, hasBackendValidIfc } from './workflow';
import type { AssetDto, CommercialSolutionStatus } from './contracts';

const ifc: AssetDto = {
  id: 'a',
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

describe('workflow helpers', () => {
  it('detects backend-valid IFC assets', () => {
    expect(hasBackendValidIfc([ifc])).toBe(true);
    expect(hasBackendValidIfc([{ ...ifc, validation_data: { valid: false } }])).toBe(false);
  });

  it.each<[CommercialSolutionStatus, boolean, boolean, boolean, boolean]>([
    ['DRAFT', true, true, true, true],
    ['SUBMITTED', false, false, false, false],
    ['APPROVED', true, false, false, false],
    ['REJECTED', true, true, true, true],
    ['ARCHIVED', false, false, false, false],
  ])('matches matrix for %s', (status, canEdit, canAssets, canSubmit, canDelete) => {
    const actions = actionsForCommercialSolution({ status, assets: [ifc] });
    expect(actions.canEditMetadata).toBe(canEdit);
    expect(actions.canChangeAssets).toBe(canAssets);
    expect(actions.canSubmit).toBe(canSubmit);
    expect(actions.canDelete).toBe(canDelete);
  });
});
