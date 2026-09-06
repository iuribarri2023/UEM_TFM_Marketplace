import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


def test_import_json_schemas_are_valid_and_examples_conform():
    pairs = [
        ("generic_solutions.schema.json", "generic_solutions.example.json"),
        ("manufacturer_solutions.schema.json", "manufacturer_solutions.example.json"),
    ]
    for schema_name, example_name in pairs:
        schema = json.loads((ROOT / "schemas/import" / schema_name).read_text(encoding="utf-8"))
        example = json.loads((ROOT / "data/examples" / example_name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(example))
        assert errors == []
