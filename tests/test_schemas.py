import json
from pathlib import Path


def test_all_json_schemas_are_valid_json() -> None:
    root = Path(__file__).parents[1] / "schemas"
    schemas = list(root.glob("*.schema.json"))
    assert schemas
    for path in schemas:
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"
