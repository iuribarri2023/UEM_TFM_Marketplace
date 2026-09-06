import json

import pytest

from app.infrastructure.storage.local import LocalFileStorage
from app.repositories.catalogue import GenericSolutionRepository, GenericSolutionSlotRepository
from app.repositories.commercial import AssetRepository, CommercialSolutionRepository, ManufacturerRepository
from app.services.importer import CatalogImportService, ManufacturerSolutionImportService
from tests.conftest import FakeBimAdapter

pytestmark = pytest.mark.postgres


def _write_ifc(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("IFC fixture", encoding="utf-8")


def test_generic_importer_is_idempotent_and_preserves_real_json_shapes(db_session, tmp_path):
    import_dir = tmp_path / "generic"
    ifc = import_dir / "assets/ifc/generic/FAC-VEN-IMP.ifc"
    _write_ifc(ifc)
    payload = {
        "schema_version": "1.2",
        "generation_provenance": {"ignored_as_document_metadata": True},
        "system": {"code": "ENV", "name_es": "Envolvente"},
        "subsystem": {"code": "FAC", "name_es": "Fachadas"},
        "archetype": {"code": "FAC-VEN", "name_es": "Fachada ventilada"},
        "generic_solutions": [
            {
                "code": "FAC-VEN-IMP",
                "name_es": "Importada",
                "functional_unit": "m2",
                "classifications": [{"scheme": "CTE-CEC", "code": "F 8.1"}],
                "source_references": [{"dataset": "fixture", "code": "F 8.1"}],
                "attributes": {"family": "facade"},
                "metrics": {"u": {"value": None, "status": "unknown"}},
                "cte_compliance": {},
                "environmental_data": {},
                "economic_data": {},
                "industrialization_data": {},
                "viva_metrics": {},
                "data_quality_notes": ["test"],
                "assets": [
                    {
                        "id": "FAC-VEN-IMP-IFC",
                        "type": "bim_model",
                        "format": "IFC",
                        "role": "primary_generic_model",
                        "uri": "assets/ifc/generic/FAC-VEN-IMP.ifc",
                    }
                ],
                "slots": [
                    {
                        "key": "AT",
                        "name_es": "Aislamiento",
                        "sequence": 20,
                        "properties": {"thickness": 80},
                    },
                    {
                        "key": "AT",
                        "name_es": "Aislamiento 2",
                        "sequence": 30,
                        "properties": {"thickness": 40},
                    },
                ],
            }
        ],
    }
    json_path = import_dir / "fac-ven.json"
    import_dir.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    storage = LocalFileStorage(tmp_path / "storage", 1024 * 1024)
    service = CatalogImportService(db_session, storage, FakeBimAdapter())
    assert service.import_file(json_path) == {"generic_solutions": 1, "slots": 2, "assets": 1}
    assert service.import_file(json_path) == {"generic_solutions": 1, "slots": 2, "assets": 1}

    solution = GenericSolutionRepository(db_session).get_by_code("FAC-VEN-IMP")
    slots = GenericSolutionSlotRepository(db_session).list_for_solution(solution.id)
    assets = AssetRepository(db_session).list_for_generic_solution(solution.id)
    assert solution.classifications[0]["scheme"] == "CTE-CEC"
    assert solution.source_references[0]["dataset"] == "fixture"
    assert solution.attributes["family"] == "facade"
    assert solution.metrics["u"]["value"] is None
    assert [slot.key for slot in slots] == ["AT", "AT"]
    assert len(assets) == 1
    assert assets[0].code == "FAC-VEN-IMP-IFC"
    assert assets[0].validation_data["valid"] is True


def test_manufacturer_importer_creates_draft_and_links_ifc(db_session, catalogue, tmp_path):
    import_dir = tmp_path / "manufacturer"
    ifc = import_dir / "assets/ifc/manufacturer/ACME-001.ifc"
    _write_ifc(ifc)
    payload = {
        "schema_version": "1.0",
        "manufacturer": {
            "code": "ACME",
            "name": "ACME",
            "tax_id": "B12345678",
            "status": "ACTIVE",
        },
        "manufacturer_solutions": [
            {
                "generic_solution_code": catalogue["facade"].code,
                "code": "ACME-001",
                "name_es": "Producto ACME",
                "technical_data": {"declared_u_value": 0.4},
                "status": "DRAFT",
                "assets": [
                    {
                        "id": "ACME-001-IFC",
                        "type": "bim_model",
                        "format": "IFC",
                        "role": "primary_commercial_model",
                        "uri": "assets/ifc/manufacturer/ACME-001.ifc",
                    }
                ],
            }
        ],
    }
    json_path = import_dir / "acme.json"
    import_dir.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    storage = LocalFileStorage(tmp_path / "storage", 1024 * 1024)
    service = ManufacturerSolutionImportService(db_session, storage, FakeBimAdapter())
    assert service.import_file(json_path) == {
        "manufacturers": 1,
        "manufacturer_solutions": 1,
        "assets": 1,
    }
    assert service.import_file(json_path) == {
        "manufacturers": 1,
        "manufacturer_solutions": 1,
        "assets": 1,
    }

    manufacturer = ManufacturerRepository(db_session).get_by_code("ACME")
    solution = CommercialSolutionRepository(db_session).get_by_code("ACME-001", include_assets=True)
    assert manufacturer.tax_id == "B12345678"
    assert solution.status == "DRAFT"
    assert solution.technical_data["declared_u_value"] == 0.4
    assert solution.generic_solution_id == catalogue["facade"].id
    assert [asset.code for asset in solution.assets] == ["ACME-001-IFC"]
