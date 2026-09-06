from __future__ import annotations

import hashlib
import mimetypes
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage as WerkzeugFileStorage
from werkzeug.utils import secure_filename

from app.core.exceptions import StorageError, ValidationFailed

ALLOWED_EXTENSIONS = {".ifc", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/octet-stream",
    "application/p21",
    "application/step",
    "application/step-file",
    "application/x-step",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/plain",
    "text/step",
}


@dataclass(frozen=True)
class StagedFile:
    original_filename: str
    staging_relative_path: str
    mime_type: str
    size: int
    sha256: str
    format: str


@dataclass(frozen=True)
class StoredFile:
    original_filename: str
    stored_filename: str
    relative_path: str
    mime_type: str
    size: int
    sha256: str
    format: str


class LocalFileStorage:
    def __init__(self, root: Path, max_upload_size: int):
        self.root = root.resolve()
        self.max_upload_size = max_upload_size
        self.root.mkdir(parents=True, exist_ok=True)
        self._staging_root = self._resolve_relative(".staging")
        self._staging_root.mkdir(parents=True, exist_ok=True)

    def stage_upload(self, upload: WerkzeugFileStorage) -> StagedFile:
        original = secure_filename(upload.filename or "")
        if not original:
            raise ValidationFailed("A filename is required.")
        extension, mime_type = self._validate_file_metadata(original, upload.mimetype)
        staging_name = f"{uuid4()}{extension}"
        staging_relative = str(Path(".staging") / staging_name).replace("\\", "/")
        staging_path = self._resolve_relative(staging_relative)

        digest = hashlib.sha256()
        size = 0
        try:
            with staging_path.open("wb") as output:
                while chunk := upload.stream.read(1024 * 1024):
                    size += len(chunk)
                    if size > self.max_upload_size:
                        raise ValidationFailed("Upload exceeds maximum size.")
                    digest.update(chunk)
                    output.write(chunk)
        except Exception:
            staging_path.unlink(missing_ok=True)
            raise

        return StagedFile(
            original_filename=original,
            staging_relative_path=staging_relative,
            mime_type=mime_type,
            size=size,
            sha256=digest.hexdigest(),
            format=extension.lstrip("."),
        )

    def stage_local_file(self, source: Path) -> StagedFile:
        source = source.resolve()
        if not source.is_file():
            raise ValidationFailed(f"Referenced asset does not exist: {source}")
        original = secure_filename(source.name)
        extension, mime_type = self._validate_file_metadata(original, mimetypes.guess_type(original)[0])
        if source.stat().st_size > self.max_upload_size:
            raise ValidationFailed(f"Referenced asset exceeds MAX_UPLOAD_SIZE: {source.name}")

        staging_name = f"{uuid4()}{extension}"
        staging_relative = str(Path(".staging") / staging_name).replace("\\", "/")
        staging_path = self._resolve_relative(staging_relative)
        digest = hashlib.sha256()
        size = 0
        try:
            with source.open("rb") as input_file, staging_path.open("wb") as output:
                while chunk := input_file.read(1024 * 1024):
                    size += len(chunk)
                    digest.update(chunk)
                    output.write(chunk)
        except Exception:
            staging_path.unlink(missing_ok=True)
            raise

        return StagedFile(
            original_filename=original,
            staging_relative_path=staging_relative,
            mime_type=mime_type,
            size=size,
            sha256=digest.hexdigest(),
            format=extension.lstrip("."),
        )

    def promote(self, staged: StagedFile, *, folder: str) -> StoredFile:
        source = self._resolve_relative(staged.staging_relative_path)
        if not source.is_file():
            raise StorageError("Staged file does not exist.")
        target_dir = self._resolve_relative(folder)
        target_dir.mkdir(parents=True, exist_ok=True)
        extension = f".{staged.format.lower()}"
        stored_filename = f"{uuid4()}{extension}"
        relative_path = str(Path(folder) / stored_filename).replace("\\", "/")
        target = self._resolve_relative(relative_path)
        try:
            source.replace(target)
        except OSError:
            try:
                shutil.copy2(source, target)
                source.unlink(missing_ok=True)
            except Exception as exc:
                target.unlink(missing_ok=True)
                raise StorageError("Could not promote staged file.") from exc

        return StoredFile(
            original_filename=staged.original_filename,
            stored_filename=stored_filename,
            relative_path=relative_path,
            mime_type=staged.mime_type,
            size=staged.size,
            sha256=staged.sha256,
            format=staged.format.lower(),
        )

    def discard_staged(self, staged: StagedFile) -> None:
        self._resolve_relative(staged.staging_relative_path).unlink(missing_ok=True)

    def delete(self, relative_path: str) -> None:
        self._resolve_relative(relative_path).unlink(missing_ok=True)

    def open_for_read(self, relative_path: str):
        path = self._resolve_relative(relative_path)
        if not path.is_file():
            raise StorageError("Stored file does not exist.")
        return path.open("rb")

    def absolute_path(self, relative_path: str) -> Path:
        return self._resolve_relative(relative_path)

    def staged_absolute_path(self, staged: StagedFile) -> Path:
        return self._resolve_relative(staged.staging_relative_path)

    def _validate_file_metadata(self, filename: str, mime_type: str | None) -> tuple[str, str]:
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationFailed(f"File extension is not allowed: {extension or '<none>'}")
        resolved_mime = mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        if resolved_mime not in ALLOWED_MIME_TYPES:
            raise ValidationFailed(f"MIME type is not allowed: {resolved_mime}")
        return extension, resolved_mime

    def _resolve_relative(self, relative_path: str) -> Path:
        path = (self.root / relative_path).resolve()
        if self.root != path and self.root not in path.parents:
            raise StorageError("Invalid storage path.")
        return path
