from __future__ import annotations

import ast
from pathlib import Path


RELATION_KERNEL = Path("propstore/core/relations/kernel.py")
ASSERTION_REFS = Path("propstore/core/assertions/refs.py")
FORBIDDEN_RELATION_IDENTITY_NAMES = {
    "predicate",
    "predicate_id",
    "predicate_name",
    "predicate_string",
}
FORBIDDEN_ASSERTION_REF_FIELD_NAMES = {
    "cel",
    "conditions",
    "graph_payload",
    "provenance",
    "provenance_blob",
}


def _kernel_tree() -> ast.AST:
    return ast.parse(RELATION_KERNEL.read_text(encoding="utf-8"))


def _assertion_refs_tree() -> ast.AST:
    return ast.parse(ASSERTION_REFS.read_text(encoding="utf-8"))


def test_relation_kernel_does_not_name_relation_identity_as_predicate() -> None:
    tree = _kernel_tree()
    observed: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            observed.add(node.id)
        elif isinstance(node, ast.arg):
            observed.add(node.arg)
        elif isinstance(node, ast.Attribute):
            observed.add(node.attr)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            observed.add(node.name)

    assert observed.isdisjoint(FORBIDDEN_RELATION_IDENTITY_NAMES)


def test_relation_concept_ref_is_not_a_string_alias() -> None:
    tree = _kernel_tree()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "RelationConceptRef"
            for target in node.targets
        ):
            continue
        assert not (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "NewType"
        )
        assert not (
            isinstance(node.value, ast.Name)
            and node.value.id in {"str", "String"}
        )


def test_assertion_refs_do_not_store_raw_conditions_or_provenance_blobs() -> None:
    tree = _assertion_refs_tree()
    observed: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            observed.add(node.arg)
        elif isinstance(node, ast.Attribute):
            observed.add(node.attr)
        elif isinstance(node, ast.Name):
            observed.add(node.id)

    assert observed.isdisjoint(FORBIDDEN_ASSERTION_REF_FIELD_NAMES)
