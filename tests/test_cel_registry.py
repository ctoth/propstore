"""The canonical CEL concept registry built from concepts + forms.

A CEL expression refers to a concept by its ``concept_id``; the registry is keyed
by exactly that id, and each concept's measurement kind is resolved from its
linked physical-dimension form (defaulting to CATEGORY when none is linked).
"""

from __future__ import annotations

from condition_ir import KindType

from propstore.cel_registry import (
    build_canonical_cel_registry,
    concept_info_from_concept,
    concept_kind,
)
from propstore.core.lemon import LexicalEntry, LexicalForm, LexicalSense, OntologyReference
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition


def _linked_concept(concept_id: str, form_name: str) -> Concept:
    return Concept(
        concept_id=concept_id,
        canonical_name=concept_id,
        lexical_entry=LexicalEntry(
            identifier=f"entry:{concept_id}",
            canonical_form=LexicalForm(written_rep=concept_id, language="en"),
            senses=(LexicalSense(reference=OntologyReference(uri=f"u:{concept_id}")),),
            physical_dimension_form=form_name,
        ),
    )


def _quantity_form(name: str) -> FormDefinition:
    return FormDefinition(name=name, kind=KindType.QUANTITY, dimensions={"length": 1})


def test_concept_kind_resolves_from_linked_form() -> None:
    forms = {"len_form": _quantity_form("len_form")}
    concept = _linked_concept("width", "len_form")
    assert concept_kind(concept, forms) is KindType.QUANTITY


def test_concept_kind_defaults_to_category_without_form() -> None:
    concept = Concept(concept_id="color", canonical_name="color")
    assert concept_kind(concept, {}) is KindType.CATEGORY


def test_concept_kind_defaults_to_category_for_dangling_form() -> None:
    concept = _linked_concept("width", "missing_form")
    assert concept_kind(concept, {}) is KindType.CATEGORY


def test_concept_info_uses_concept_id() -> None:
    concept = Concept(concept_id="freq", canonical_name="frequency")
    info = concept_info_from_concept(concept, {})
    assert info.id == "freq"
    assert info.canonical_name == "frequency"


def test_registry_is_keyed_by_concept_id() -> None:
    forms = {"len_form": _quantity_form("len_form")}
    concepts = [_linked_concept("width", "len_form"), Concept(concept_id="hue", canonical_name="hue")]
    registry = build_canonical_cel_registry(concepts, forms)
    assert "width" in registry
    assert "hue" in registry
    assert registry["width"].kind is KindType.QUANTITY
    assert registry["hue"].kind is KindType.CATEGORY


def test_registry_accepts_synthetic_binding_names() -> None:
    # propstore supplies synthetic bindings by passing names as an argument to
    # condition-ir's generic builder (parameterised, not wrapped). With none
    # requested the registry is exactly the authored concepts.
    base = build_canonical_cel_registry(
        [Concept(concept_id="hue", canonical_name="hue")], {}
    )
    assert set(base) == {"hue"}
    with_binding = build_canonical_cel_registry(
        [Concept(concept_id="hue", canonical_name="hue")],
        {},
        synthetic_binding_names=("speaker",),
    )
    assert set(with_binding) >= {"hue", "speaker"}
