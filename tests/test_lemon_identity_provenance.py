"""Provenance laws (PLAN.md §12.4): qualia REQUIRES provenance, yet provenance is
EXCLUDED from lexical identity.

These two laws coexist: a qualia/sense link cannot be authored without saying
where it came from, but two entries differing ONLY in provenance are the same
entry. Provenance is carried alongside the value object (the physical out-of-band
git-note carrier is a later phase) and never enters an identity key.
"""

from __future__ import annotations

import pytest

from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
    QualiaReference,
    lexical_entry_identity_key,
    lexical_form_identity_key,
)
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness


def _provenance(method: str) -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(
            ProvenanceWitness(
                asserter="tests",
                timestamp="2026-04-17T00:00:00Z",
                source_artifact_code="tests:identity",
                method=method,
            ),
        ),
    )


def test_qualia_reference_requires_provenance() -> None:
    """A qualia link without provenance cannot be constructed (honest ignorance)."""

    with pytest.raises(TypeError):
        QualiaReference(reference=OntologyReference(uri="u:measure"))  # type: ignore[call-arg]


def test_entry_identity_excludes_provenance() -> None:
    """Two entries differing only in sense provenance share both identity keys."""

    reference = OntologyReference(uri="u:temperature")
    form = LexicalForm(written_rep="temperature", language="en")

    stated = LexicalEntry(
        identifier="entry:temperature",
        canonical_form=form,
        senses=(LexicalSense(reference=reference, provenance=_provenance("stated")),),
    )
    measured = LexicalEntry(
        identifier="entry:temperature",
        canonical_form=form,
        senses=(LexicalSense(reference=reference, provenance=_provenance("measured")),),
    )

    # The senses carry different provenance ...
    assert stated.senses[0].provenance != measured.senses[0].provenance
    # ... yet identity is unchanged: provenance is not part of what the entry IS.
    assert lexical_entry_identity_key(stated) == lexical_entry_identity_key(measured)
    assert lexical_form_identity_key(stated) == lexical_form_identity_key(measured)
