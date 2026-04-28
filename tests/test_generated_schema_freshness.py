from __future__ import annotations

from pathlib import Path

from schema.generate import RESOURCE_SCHEMA_DIR, SCHEMAS


def test_generated_schema_resources_are_committed_and_fresh() -> None:
    assert RESOURCE_SCHEMA_DIR.is_dir(), (
        "schema/generate.py targets propstore/_resources/schemas, but that "
        "resource tree is not committed"
    )

    expected_names = {json_file for _, json_file in SCHEMAS} | {"form.schema.json"}
    actual_names = {path.name for path in RESOURCE_SCHEMA_DIR.glob("*.schema.json")}
    assert actual_names == expected_names

    generated_dir = Path("schema/generated")
    for name in sorted(expected_names):
        assert (RESOURCE_SCHEMA_DIR / name).read_bytes() == (generated_dir / name).read_bytes()
