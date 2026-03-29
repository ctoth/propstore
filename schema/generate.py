#!/usr/bin/env python3
"""Regenerate JSON Schema files from LinkML sources.

Usage:
    uv run python schema/generate.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent
GENERATED_DIR = SCHEMA_DIR / "generated"
RESOURCE_SCHEMA_DIR = SCHEMA_DIR.parent / "propstore" / "_resources" / "schemas"

SCHEMAS = [
    ("claim.linkml.yaml", "claim.schema.json"),
    ("concept_registry.linkml.yaml", "concept_registry.schema.json"),
]


def main() -> int:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESOURCE_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    ok = True

    for linkml_file, json_file in SCHEMAS:
        src = SCHEMA_DIR / linkml_file
        dst = GENERATED_DIR / json_file

        if not src.exists():
            print(f"ERROR: {src} not found", file=sys.stderr)
            ok = False
            continue

        print(f"  {linkml_file} -> generated/{json_file}")
        result = subprocess.run(
            ["gen-json-schema", "--closed", str(src)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"ERROR generating {json_file}:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            ok = False
            continue

        dst.write_text(result.stdout)
        (RESOURCE_SCHEMA_DIR / json_file).write_text(result.stdout)

    for filename in ("form.schema.json",):
        src = GENERATED_DIR / filename
        dst = RESOURCE_SCHEMA_DIR / filename
        if not src.exists():
            print(f"ERROR: {src} not found", file=sys.stderr)
            ok = False
            continue
        dst.write_text(src.read_text())

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
