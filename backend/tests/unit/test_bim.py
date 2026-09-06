import sys
from types import SimpleNamespace

import pytest

from app.core.exceptions import InvalidIfcFile
from app.infrastructure.bim.ifc import IfcOpenShellAdapter


class FakeIfcModel:
    schema = "IFC4"

    def __iter__(self):
        return iter([1, 2, 3])

    def by_type(self, name):
        if name == "IfcProject":
            return [SimpleNamespace(Name="Project", GlobalId="GID")]
        return []


def test_ifcopenshell_validation_accepts_ifc(valid_ifc_file, monkeypatch):
    monkeypatch.setitem(sys.modules, "ifcopenshell", SimpleNamespace(open=lambda _path: FakeIfcModel()))
    metadata = IfcOpenShellAdapter().inspect(valid_ifc_file)
    assert metadata["schema"] == "IFC4"
    assert metadata["entity_count"] == 3
    assert metadata["validated_by"] == "ifcopenshell"


def test_ifcopenshell_validation_rejects_invalid_file(tmp_path, monkeypatch):
    path = tmp_path / "bad.ifc"
    path.write_text("not ifc", encoding="utf-8")

    def fail(_path):
        raise RuntimeError("parse error")

    monkeypatch.setitem(sys.modules, "ifcopenshell", SimpleNamespace(open=fail))
    with pytest.raises(InvalidIfcFile):
        IfcOpenShellAdapter().inspect(path)
