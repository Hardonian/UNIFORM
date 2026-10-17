import json
from pathlib import Path

from jsonschema.validators import validator_for
from referencing import Registry, Resource

from uniform_lab.resources import load_example, load_schema, schema_names


def test_all_json_schemas_are_valid_draft_2020_12() -> None:
    root = Path(__file__).parents[1] / "schemas"
    schemas = list(root.glob("*.schema.json"))
    assert schemas
    for path in schemas:
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        validator_for(document).check_schema(document)


def test_every_versioned_source_schema_has_a_bundled_schema() -> None:
    root = Path(__file__).parents[1]
    emitted: set[str] = set()
    for directory in (root / "src", root / "examples"):
        for path in directory.rglob("*"):
            if path.suffix not in {".py", ".json"}:
                continue
            text = path.read_text(encoding="utf-8")
            marker = "uniform."
            for fragment in text.split('"'):
                if fragment.startswith(marker) and "/v" in fragment:
                    emitted.add(fragment)
    bundled = set(schema_names())
    missing = {
        schema
        for schema in emitted
        if f"{schema.removeprefix('uniform.').replace('/', '-')}.schema.json" not in bundled
    }
    assert missing == set()


def _schema_registry() -> Registry:
    reg: Registry = Registry()
    for name in schema_names():
        sch = load_schema(name)
        res = Resource.from_contents(sch)
        reg = reg.with_resource(name, res)
        if "$id" in sch:
            reg = reg.with_resource(sch["$id"], res)
    return reg


def test_bundled_resources_are_readable_and_examples_validate() -> None:
    assert len(schema_names()) >= 20
    for name in schema_names():
        assert load_schema(name)["$schema"].endswith("2020-12/schema")

    registry = _schema_registry()
    root = Path(__file__).parents[1]
    for path in (root / "examples").rglob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        schema_id = document.get("schema")
        if not isinstance(schema_id, str):
            continue
        filename = f"{schema_id.removeprefix('uniform.').replace('/', '-')}.schema.json"
        schema = load_schema(filename)
        validator_for(schema)(schema, registry=registry).validate(document)

    assert load_example("one_player_zero.json")["players"] == 1


def test_resource_names_reject_traversal() -> None:
    try:
        load_schema("../pyproject.toml")
    except KeyError:
        pass
    else:
        raise AssertionError("schema resource traversal was accepted")
