import pytest

from app.repositories.catalogue import GenericSolutionRepository, GenericSolutionSlotRepository


pytestmark = pytest.mark.postgres


def test_hierarchy_and_jsonb_round_trip(db_session, catalogue):
    facade = GenericSolutionRepository(db_session).get(catalogue["facade"].id, include_slots=True)
    assert facade.archetype.subsystem.system.code == "ENV"
    assert facade.attributes["total_thickness"]["unit"] == "mm"
    assert facade.metrics["u_value"]["value"] is None
    assert facade.environmental_data["gwp"]["unit"] == "kgCO2e"


def test_duplicate_slot_keys_and_slot_ordering(db_session, catalogue):
    slots = GenericSolutionSlotRepository(db_session).list_for_solution(catalogue["facade"].id)
    assert [slot.sequence for slot in slots] == [10, 20, 30]
    assert [slot.key for slot in slots].count("AT") == 2
    assert slots[1].properties["thickness"] == 100


def test_generalized_schema_handles_facade_roof_window(db_session, catalogue):
    repo = GenericSolutionRepository(db_session)
    facade = repo.get(catalogue["facade"].id, include_slots=True)
    roof = repo.get(catalogue["roof"].id, include_slots=True)
    window = repo.get(catalogue["window"].id, include_slots=True)
    assert facade.slots[0].properties["material"] == "ceramic"
    assert roof.slots[0].properties["system"] == "monocapa"
    assert window.slots[0].metrics["uf"]["value"] == 1.8
    assert window.slots[1].source_reference["epd"] == "fixture"

