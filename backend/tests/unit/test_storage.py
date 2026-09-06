import io

import pytest
from werkzeug.datastructures import FileStorage

from app.core.exceptions import StorageError
from app.infrastructure.storage.local import LocalFileStorage


def test_storage_blocks_path_traversal(tmp_path):
    storage = LocalFileStorage(tmp_path, 1000)
    with pytest.raises(StorageError):
        storage.absolute_path("../outside.ifc")


def test_storage_stages_promotes_and_checksums(tmp_path):
    storage = LocalFileStorage(tmp_path, 1000)
    upload = FileStorage(stream=io.BytesIO(b"abc"), filename="model.ifc", content_type="text/plain")
    staged = storage.stage_upload(upload)
    stored = storage.promote(staged, folder="models")
    assert stored.sha256 == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert storage.absolute_path(stored.relative_path).read_bytes() == b"abc"
    assert not storage.absolute_path(staged.staging_relative_path).exists()
