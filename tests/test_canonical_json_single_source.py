from __future__ import annotations

import ast
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
import pytest

from quire.hashing import canonical_json_bytes


@pytest.mark.property
@given(st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=5))
def test_quire_canonical_json_bytes_is_the_payload_hashing_source(
    payload: dict[str, int],
) -> None:
    assert canonical_json_bytes(payload) == canonical_json_bytes(dict(reversed(payload.items())))


def test_propstore_defines_no_local_canonical_json_helpers() -> None:
    offenders: list[str] = []
    for path in Path("propstore").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_canonical_json":
                offenders.append(f"{path}:{node.lineno}")

    assert offenders == []
