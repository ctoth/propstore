from __future__ import annotations

import ast
import inspect

import propstore.provenance as provenance


def test_compose_provenance_uses_the_module_witness_key() -> None:
    source = inspect.getsource(provenance.compose_provenance)

    assert "_witness_key(witness)" in source


def test_provenance_module_has_one_witness_key_tuple_order() -> None:
    source = inspect.getsource(provenance)
    tree = ast.parse(source)
    witness_tuple_orders: list[tuple[str, ...]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Tuple):
            continue
        fields: list[str] = []
        for element in node.elts:
            text = ast.get_source_segment(source, element) or ""
            if text.startswith("witness."):
                fields.append(text.removeprefix("witness."))
        if len(fields) >= 2:
            witness_tuple_orders.append(tuple(fields))

    assert sorted(set(witness_tuple_orders)) == [
        ("asserter", "method", "source_artifact_code", "timestamp")
    ]
