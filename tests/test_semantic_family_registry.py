"""The propstore family registry is charter-derived (PLAN.md §12.6).

These tests are the binding gate for the registry's central discipline: the
family set and the foreign-key graph are *derived* from the ``@charter``
document classes and their ``charter_field(foreign_key=...)`` annotations, not
hand-authored as a literal table. The headline assertions:

* every registry foreign key equals the lift of some charter field's annotation
  (``test_foreign_key_graph_is_derived_from_charter_fields``);
* ``families/registry.py`` contains **no** ``ForeignKeySpec`` literal — the only
  place a foreign-key spec may be written is a charter field annotation
  (``test_no_foreign_key_literal_outside_charter_annotation``).
"""

from __future__ import annotations

from pathlib import Path

from quire.charters import charter_field_foreign_keys
from quire.references import ForeignKeySpec

import propstore.families.registry as registry_module
from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    registered_charters,
    semantic_families,
    semantic_foreign_keys,
    semantic_import_families,
    semantic_init_roots,
)


def _charter_field_foreign_keys(family_name: str) -> tuple[ForeignKeySpec, ...]:
    for charter_obj in registered_charters():
        if charter_obj.family.name == family_name:
            return tuple(
                spec
                for field in charter_obj.fields
                for spec in charter_field_foreign_keys(field)
            )
    raise AssertionError(f"no charter for family {family_name!r}")


def test_registry_contains_every_authored_family() -> None:
    names = set(PROPSTORE_FAMILY_REGISTRY.names())
    # A representative spread across the entity families must all be present.
    assert {"concept", "claim", "context", "form", "stance", "defeasible_rule"} <= names


def test_foreign_key_graph_is_derived_from_charter_fields() -> None:
    # For every family, the registry's foreign keys are exactly the lift of its
    # charter fields' annotations — proving the graph is derived, not authored
    # as a separate literal table alongside the charters.
    for family in PROPSTORE_FAMILY_REGISTRY.families:
        derived = _charter_field_foreign_keys(family.name)
        assert family.foreign_keys == derived, family.name


def test_claim_foreign_keys_point_at_concept_and_context() -> None:
    claim_fks = {
        spec.name: spec for spec in PROPSTORE_FAMILY_REGISTRY.by_name("claim").foreign_keys
    }
    assert claim_fks["claim_context"].target_family == "context"
    assert claim_fks["claim_output_concept"].target_family == "concept"
    assert claim_fks["claim_concepts"].source_field == "concepts[]"
    assert claim_fks["claim_concepts"].many is True


def test_micropublication_foreign_keys_are_derived() -> None:
    # PLAN.md §12.6 names micropublications as one of the two hardest families the
    # charter->FK derivation must cover (lemon/concept being the other).
    fks = {
        spec.name: spec
        for spec in PROPSTORE_FAMILY_REGISTRY.by_name("micropublication").foreign_keys
    }
    assert fks["micropublication_context"].target_family == "context"
    assert fks["micropublication_claims"].target_family == "claim"
    assert fks["micropublication_claims"].source_field == "claims[]"
    assert fks["micropublication_claims"].many is True
    # Derivation, not a literal table: the lift equals the charter field FKs.
    assert PROPSTORE_FAMILY_REGISTRY.by_name(
        "micropublication"
    ).foreign_keys == _charter_field_foreign_keys("micropublication")


def test_every_foreign_key_target_is_a_registered_family() -> None:
    names = set(PROPSTORE_FAMILY_REGISTRY.names())
    for family in PROPSTORE_FAMILY_REGISTRY.families:
        for spec in family.foreign_keys:
            assert spec.source_family == family.name
            assert spec.target_family in names


def test_no_foreign_key_literal_outside_charter_annotation() -> None:
    # The registry module must not author any ForeignKeySpec; the only legal home
    # for a foreign-key literal is a charter field annotation. (PLAN.md §12.6.)
    source = Path(registry_module.__file__).read_text(encoding="utf-8")
    assert "ForeignKeySpec(" not in source


def test_semantic_init_roots_cover_the_core_families() -> None:
    roots = set(semantic_init_roots())
    assert {"concept", "claim", "context", "form"} <= roots


def test_semantic_import_order_places_targets_before_sources() -> None:
    order = [family.name for family in semantic_import_families()]
    position = {name: index for index, name in enumerate(order)}
    semantic_names = set(position)
    for family in semantic_families():
        if family.name not in position:
            continue
        for spec in family.foreign_keys:
            if (
                spec.target_family in semantic_names
                and spec.target_family != family.name
            ):
                assert position[spec.target_family] < position[family.name], spec.name


def test_semantic_foreign_keys_are_sorted_and_complete() -> None:
    specs = semantic_foreign_keys()
    assert [spec.name for spec in specs] == sorted(spec.name for spec in specs)
    # claim's four references all surface (claim is a semantic family).
    assert {
        "claim_context",
        "claim_output_concept",
        "claim_target_concept",
        "claim_concepts",
    } <= {spec.name for spec in specs}
