import type {
  CommercialSolutionCreateDto,
  CommercialSolutionPatchDto,
  JsonObject,
} from './contracts';

export interface CommercialSolutionFormValue {
  generic_solution_id?: unknown;
  code?: unknown;
  name_es?: unknown;
  description?: unknown;
  technical_data?: unknown;
  manufacturer_id?: unknown;
  status?: unknown;
  assets?: unknown;
}

export function createCommercialSolutionPayload(
  value: CommercialSolutionFormValue,
): CommercialSolutionCreateDto {
  return {
    generic_solution_id: stringField(value.generic_solution_id),
    code: stringField(value.code),
    name_es: stringField(value.name_es),
    description: nullableString(value.description),
    technical_data: objectField(value.technical_data),
  };
}

export function patchCommercialSolutionPayload(
  value: CommercialSolutionFormValue,
): CommercialSolutionPatchDto {
  return {
    code: value.code === undefined ? undefined : stringField(value.code),
    name_es: value.name_es === undefined ? undefined : stringField(value.name_es),
    description: value.description === undefined ? undefined : nullableString(value.description),
    technical_data:
      value.technical_data === undefined ? undefined : objectField(value.technical_data),
  };
}

export interface AssetUploadValue {
  file: File;
  code?: string | null;
  role?: string | null;
  asset_type?: string | null;
}

export function buildAssetUploadFormData(value: AssetUploadValue): FormData {
  const formData = new FormData();
  formData.append('file', value.file);
  formData.append('role', value.role || 'primary_commercial_model');
  formData.append('asset_type', value.asset_type || 'bim_model');
  if (value.code) {
    formData.append('code', value.code);
  }
  return formData;
}

function stringField(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function nullableString(value: unknown): string | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  return typeof value === 'string' ? value : String(value);
}

function objectField(value: unknown): JsonObject {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as JsonObject)
    : {};
}
