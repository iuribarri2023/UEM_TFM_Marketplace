class AppError(Exception):
    code = "APP_ERROR"
    status_code = 400

    def __init__(self, message: str | None = None):
        self.message = message or "Application error."
        super().__init__(self.message)


class EntityNotFound(AppError):
    code = "ENTITY_NOT_FOUND"
    status_code = 404


class ValidationFailed(AppError):
    code = "VALIDATION_FAILED"
    status_code = 400


class AuthenticationFailed(AppError):
    code = "AUTHENTICATION_FAILED"
    status_code = 401


class PermissionDenied(AppError):
    code = "PERMISSION_DENIED"
    status_code = 403


class InvalidWorkflowTransition(AppError):
    code = "INVALID_WORKFLOW_TRANSITION"
    status_code = 409


class MissingIfcFile(AppError):
    code = "MISSING_IFC_FILE"
    status_code = 409


class InvalidIfcFile(AppError):
    code = "INVALID_IFC_FILE"
    status_code = 400


class StorageError(AppError):
    code = "STORAGE_ERROR"
    status_code = 400

