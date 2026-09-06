export type JsonValue =
  | null
  | string
  | number
  | boolean
  | JsonValue[]
  | { [key: string]: JsonValue };

export type JsonObject = Record<string, unknown>;

export interface ApiEnvelope<T> {
  data: T;
}

export interface ApiErrorBody {
  code: BackendErrorCode | string;
  message: string;
}

export interface ApiErrorEnvelope {
  error: ApiErrorBody;
}

export type BackendErrorCode =
  | 'AUTHENTICATION_FAILED'
  | 'PERMISSION_DENIED'
  | 'ENTITY_NOT_FOUND'
  | 'NOT_FOUND'
  | 'VALIDATION_FAILED'
  | 'INTEGRITY_ERROR'
  | 'INVALID_WORKFLOW_TRANSITION'
  | 'MISSING_IFC_FILE'
  | 'INVALID_IFC_FILE'
  | 'FILE_TOO_LARGE'
  | 'STORAGE_ERROR'
  | 'INTERNAL_SERVER_ERROR';

export type UserRole = 'ADMIN' | 'MANUFACTURER';

export type CommercialSolutionStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'APPROVED'
  | 'REJECTED'
  | 'ARCHIVED';

export interface SystemDto {
  id: string;
  code: string;
  name_es: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubsystemDto {
  id: string;
  system_id: string;
  code: string;
  name_es: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ArchetypeDto {
  id: string;
  subsystem_id: string;
  code: string;
  name_es: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface GenericSolutionSlotDto {
  id: string;
  key: string;
  name_es: string;
  role: string | null;
  sequence: number;
  required: boolean;
  properties: JsonObject;
  metrics: JsonObject | null;
  source_reference: JsonObject | null;
  created_at: string;
  updated_at: string;
}

export interface GenericSolutionSummaryDto {
  id: string;
  archetype_id: string;
  code: string;
  name_es: string;
  description: string | null;
  functional_unit: string | null;
  status: string | null;
  classifications: JsonObject[];
  source_references: JsonObject[];
  attributes: JsonObject;
  metrics: JsonObject;
  cte_compliance: JsonObject;
  environmental_data: JsonObject;
  economic_data: JsonObject;
  industrialization_data: JsonObject;
  viva_metrics: JsonObject;
  data_quality_notes: unknown[] | JsonObject | null;
  created_at: string;
  updated_at: string;
}

export interface GenericSolutionDto extends GenericSolutionSummaryDto {
  slots: GenericSolutionSlotDto[];
  assets: AssetDto[];
}

export interface AssetDto {
  id: string;
  code: string | null;
  original_filename: string;
  mime_type: string;
  size: number;
  sha256: string;
  asset_type: string;
  format: string;
  role: string;
  uploaded_by: string | null;
  validation_data: JsonObject | null;
  extraction_data: JsonObject | null;
  created_at: string;
  updated_at: string;
}

export interface ManufacturerDto {
  id: string;
  code: string;
  name: string;
  tax_id: string | null;
  website: string | null;
  description: string | null;
  status: string;
}

export interface CommercialSolutionDto {
  id: string;
  manufacturer_id: string;
  generic_solution_id: string;
  code: string;
  name_es: string;
  description: string | null;
  technical_data: JsonObject;
  status: CommercialSolutionStatus;
  rejection_reason: string | null;
  created_by: string | null;
  updated_by: string | null;
  submitted_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
  created_at: string;
  updated_at: string;
  assets: AssetDto[];
}

export interface CommercialSolutionCreateDto {
  generic_solution_id: string;
  code: string;
  name_es: string;
  description?: string | null;
  technical_data: JsonObject;
}

export interface CommercialSolutionPatchDto {
  code?: string;
  name_es?: string;
  description?: string | null;
  technical_data?: JsonObject;
}

export interface LoginRequestDto {
  email: string;
  password: string;
}

export interface RefreshRequestDto {
  refresh_token: string;
}

export interface TokenResponseDto {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CurrentUserDto {
  id: string;
  email: string;
  role: UserRole;
  manufacturer_id: string | null;
}
