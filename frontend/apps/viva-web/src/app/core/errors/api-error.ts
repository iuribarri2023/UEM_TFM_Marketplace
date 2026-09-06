import { HttpErrorResponse } from '@angular/common/http';
import type { ApiErrorEnvelope, BackendErrorCode } from '@viva/contracts';

export interface AppApiError {
  status: number;
  code: BackendErrorCode | string;
  message: string;
}

export function normalizeApiError(error: unknown): AppApiError {
  if (error instanceof HttpErrorResponse) {
    const body = error.error as Partial<ApiErrorEnvelope> | null;
    if (body?.error?.code && body.error.message) {
      return {
        status: error.status,
        code: body.error.code,
        message: body.error.message,
      };
    }
    return {
      status: error.status,
      code: error.status === 0 ? 'NETWORK_ERROR' : 'INTERNAL_SERVER_ERROR',
      message: error.message || 'Request failed.',
    };
  }
  return {
    status: 0,
    code: 'UNKNOWN_ERROR',
    message: error instanceof Error ? error.message : 'Unexpected error.',
  };
}

export function userMessageForError(error: AppApiError): string {
  switch (error.code) {
    case 'AUTHENTICATION_FAILED':
      return 'The email or password is not valid.';
    case 'PERMISSION_DENIED':
      return 'You do not have permission to perform this action.';
    case 'ENTITY_NOT_FOUND':
    case 'NOT_FOUND':
      return 'The requested item was not found.';
    case 'VALIDATION_FAILED':
      return 'Review the fields and try again.';
    case 'INTEGRITY_ERROR':
      return 'A conflicting value already exists, commonly a duplicate code.';
    case 'INVALID_WORKFLOW_TRANSITION':
      return 'The item changed state. The latest server state has been reloaded.';
    case 'MISSING_IFC_FILE':
      return 'A backend-valid IFC asset is required before submission.';
    case 'INVALID_IFC_FILE':
      return 'The uploaded IFC could not be validated by the backend.';
    case 'FILE_TOO_LARGE':
      return 'The uploaded file exceeds the backend upload limit.';
    case 'STORAGE_ERROR':
      return 'The file storage operation failed.';
    case 'INTERNAL_SERVER_ERROR':
      return 'The server failed to complete the request.';
    default:
      return error.message || 'Request failed.';
  }
}
