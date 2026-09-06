import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function parseJsonObject(text: string): Record<string, unknown> | null {
  try {
    const parsed: unknown = JSON.parse(text || '{}');
    return parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

export const jsonObjectValidator: ValidatorFn = (
  control: AbstractControl<string>,
): ValidationErrors | null => (parseJsonObject(control.value) ? null : { jsonObject: true });
