from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
    lexical_entry_identity_key,
)


_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1,
    max_size=40,
).filter(lambda value: bool(value.strip()))


def test_lexical_form_does_not_accept_dimensional_metadata() -> None:
    with pytest.raises(TypeError):
        LexicalForm(written_rep="temperature", language="en", unit_symbol="K")  # type: ignore[call-arg]


def test_lexical_entry_requires_at_least_one_sense() -> None:
    with pytest.raises(ValueError, match="at least one lexical sense"):
        LexicalEntry(
            identifier="entry:temperature",
            canonical_form=LexicalForm(written_rep="temperature", language="en"),
            senses=(),
        )


@given(entry_id=_text, written_rep=_text, language=_text, reference_uri=_text)
@settings(deadline=None)
def test_lexical_entry_identity_is_reference_stable(
    entry_id: str,
    written_rep: str,
    language: str,
    reference_uri: str,
) -> None:
    reference = OntologyReference(uri=reference_uri)
    entry = LexicalEntry(
        identifier=entry_id,
        canonical_form=LexicalForm(written_rep=written_rep, language=language),
        senses=(LexicalSense(reference=reference),),
    )
    same_reference = LexicalEntry(
        identifier=f"{entry_id}-variant",
        canonical_form=LexicalForm(written_rep=f"{written_rep} variant", language=language),
        senses=(LexicalSense(reference=OntologyReference(uri=reference_uri)),),
    )

    assert entry.references == same_reference.references
    assert lexical_entry_identity_key(entry) != lexical_entry_identity_key(same_reference)


@given(written_rep=_text, language=_text, reference_uri=_text)
@settings(deadline=None)
def test_homographs_are_distinct_senses_on_one_entry(
    written_rep: str,
    language: str,
    reference_uri: str,
) -> None:
    first = LexicalSense(reference=OntologyReference(uri=reference_uri))
    second = LexicalSense(reference=OntologyReference(uri=f"{reference_uri}#other"))
    entry = LexicalEntry(
        identifier="entry:homograph",
        canonical_form=LexicalForm(written_rep=written_rep, language=language),
        senses=(first, second),
    )

    assert len(entry.senses) == 2
    assert entry.references == (first.reference, second.reference)
