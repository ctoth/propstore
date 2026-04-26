from __future__ import annotations

import ast
from pathlib import Path

from argumentation.aspic import GroundAtom

from tests.test_grounding_grounder import (
    _bird_registry,
    _build_atom,
    _build_rule_document,
    _build_rule_file,
    _build_term_var,
)


_PRODUCTION_GROUNDING_FILES = (
    Path("propstore/grounding/grounder.py"),
    Path("propstore/grounding/translator.py"),
    Path("propstore/grounding/explanations.py"),
    Path("propstore/grounding/gunray_complement.py"),
)
_FORBIDDEN_GUNRAY_MODULES = {
    "gunray.adapter",
    "gunray.disagreement",
    "gunray.parser",
    "gunray.schema",
    "gunray.trace",
    "gunray.types",
}


def test_ws6_grounding_uses_public_gunray_boundary_imports() -> None:
    for path in _PRODUCTION_GROUNDING_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module)

        forbidden = imported_modules & _FORBIDDEN_GUNRAY_MODULES
        assert forbidden == set(), f"{path} imports private Gunray modules: {forbidden}"


def test_ws6_explanations_use_typed_trace_lookup_helper() -> None:
    source = Path("propstore/grounding/explanations.py").read_text(encoding="utf-8")

    assert "tree_for_parts(" in source
    assert "trace.trees.items()" not in source


def test_ws6_grounder_bundle_carries_typed_grounding_substitutions() -> None:
    from propstore.grounding.grounder import ground

    rule = _build_rule_document(
        rule_id="birds_fly",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])
    facts = (GroundAtom("bird", ("tweety",)),)

    bundle = ground([rule_file], facts, _bird_registry())

    assert bundle.grounding_inspection is not None
    instances = bundle.grounding_inspection.defeasible_rules
    assert [
        (instance.rule_id, instance.head.predicate, instance.head.arguments, instance.substitution)
        for instance in instances
    ] == [("birds_fly", "flies", ("tweety",), (("X", "tweety"),))]
