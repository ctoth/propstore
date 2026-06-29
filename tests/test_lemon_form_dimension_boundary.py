"""The lemon form ↔ physical-dimension boundary (Phase 2a + 2b seam).

Physical dimensions live on the lemon *entry* (``physical_dimension_form``, a
form name), never on :class:`LexicalForm`; that name resolves to a
:class:`FormDefinition` which owns the dimensions. The dimensional *signature* is
bridgman's and is NOT re-exported by ``propstore.dimensions`` (PLAN §12.3).
"""

from __future__ import annotations

import bridgman
import pytest

import propstore.dimensions as dimensions
from condition_ir import KindType
from propstore.core.lemon import LexicalEntry, LexicalForm, LexicalSense, OntologyReference
from propstore.families.forms import FormDefinition, FormRepository


def _frequency_entry() -> LexicalEntry:
    return LexicalEntry(
        identifier="freq-en",
        canonical_form=LexicalForm(written_rep="frequency", language="en"),
        senses=(LexicalSense(reference=OntologyReference(uri="ex:frequency")),),
        physical_dimension_form="frequency",
    )


def test_lexical_form_lives_in_lemon_forms_module() -> None:
    assert LexicalForm.__module__ == "propstore.core.lemon.forms"


def test_lexical_form_rejects_a_dimensions_keyword() -> None:
    # forbid_unknown_fields keeps dimensions off the surface-form side.
    with pytest.raises(TypeError):
        LexicalForm(written_rep="frequency", language="en", dimensions={"T": -1})  # type: ignore[call-arg]


def test_physical_dimension_form_lives_on_the_entry() -> None:
    entry = _frequency_entry()
    assert entry.physical_dimension_form == "frequency"
    assert not hasattr(entry.canonical_form, "dimensions")


def test_entry_dimension_form_resolves_to_a_form_definition() -> None:
    repo = FormRepository()
    repo.author(
        FormDefinition(
            name="frequency", kind=KindType.QUANTITY, unit_symbol="Hz", dimensions={"T": -1}
        ),
        message="add frequency",
    )
    entry = _frequency_entry()
    assert entry.physical_dimension_form is not None
    resolved = repo.get(entry.physical_dimension_form)
    assert resolved is not None
    # Dimensions are owned by the form, reached via the entry's reference.
    assert resolved.dimensions == {"T": -1}


def test_dimensions_module_does_not_reexport_bridgman_signature() -> None:
    # §12.3: the canonical signature is bridgman's; propstore calls it, never wraps it.
    assert not hasattr(dimensions, "dims_signature")
    assert bridgman.dims_signature({"M": 1, "L": 1, "T": -2}) == "M:1,L:1,T:-2"
