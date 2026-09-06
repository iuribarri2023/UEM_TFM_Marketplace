import type { AssetDto, CommercialSolutionDto, CommercialSolutionStatus } from './contracts';

export interface CommercialWorkflowActions {
  canEditMetadata: boolean;
  canChangeAssets: boolean;
  canSubmit: boolean;
  canDelete: boolean;
  editResetsToDraft: boolean;
  hasBackendValidIfc: boolean;
}

export function hasBackendValidIfc(assets: readonly AssetDto[] | null | undefined): boolean {
  return (assets ?? []).some(
    (asset) => asset.format === 'ifc' && asset.validation_data?.['valid'] === true,
  );
}

export function actionsForCommercialSolution(
  solution: Pick<CommercialSolutionDto, 'status' | 'assets'>,
): CommercialWorkflowActions {
  const hasValidIfc = hasBackendValidIfc(solution.assets);
  return {
    canEditMetadata: canEditMetadata(solution.status),
    canChangeAssets: solution.status === 'DRAFT' || solution.status === 'REJECTED',
    canSubmit: solution.status === 'DRAFT' || solution.status === 'REJECTED',
    canDelete: solution.status === 'DRAFT' || solution.status === 'REJECTED',
    editResetsToDraft: solution.status === 'APPROVED' || solution.status === 'REJECTED',
    hasBackendValidIfc: hasValidIfc,
  };
}

export function canEditMetadata(status: CommercialSolutionStatus): boolean {
  return status === 'DRAFT' || status === 'APPROVED' || status === 'REJECTED';
}
