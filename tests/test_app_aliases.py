"""Owner-layer concept alias export (Phase 10-0b).

``export_concept_aliases`` flattens each concept's lemon *other forms* into an
``alias -> {logical_id, name}`` map for the ``pks export-aliases`` adapter. The
canonical form is the name (not an alias); a concept with no lexical entry
contributes nothing; a shared alias is last-writer-wins.
"""

from __future__ import annotations

from pathlib import Path

from propstore.app.aliases import AliasExportEntry, export_concept_aliases
from propstore.core.lemon import LexicalEntry, LexicalForm, LexicalSense, OntologyReference
from propstore.families.concepts import Concept
from propstore.repository import Repository
from propstore.world import WorldQuery


def _entry(canonical: str, *aliases: str) -> LexicalEntry:
    return LexicalEntry(
        identifier=f"entry:{canonical}",
        canonical_form=LexicalForm(written_rep=canonical, language="en"),
        senses=(LexicalSense(reference=OntologyReference(uri=f"urn:{canonical}")),),
        other_forms=tuple(LexicalForm(written_rep=alias, language="en") for alias in aliases),
    )


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "speech:fundamental_frequency",
        Concept(
            concept_id="speech:fundamental_frequency",
            canonical_name="fundamental_frequency",
            lexical_entry=_entry("fundamental_frequency", "F0", "f0"),
        ),
        message="m",
    )
    repo.families.concept.save(
        "speech:amplitude",
        Concept(
            concept_id="speech:amplitude",
            canonical_name="amplitude",
            lexical_entry=_entry("amplitude"),
        ),
        message="m",
    )
    # A flat (pre-lemon) concept with no entry contributes no alias.
    repo.families.concept.save(
        "speech:loudness",
        Concept(concept_id="speech:loudness", canonical_name="loudness"),
        message="m",
    )
    return repo


def test_export_concept_aliases_maps_other_forms(tmp_path: Path) -> None:
    with WorldQuery(_repo(tmp_path)) as world:
        aliases = export_concept_aliases(world)

    assert set(aliases) == {"F0", "f0"}
    assert aliases["F0"] == AliasExportEntry(
        logical_id="speech:fundamental_frequency", name="fundamental_frequency"
    )
    assert aliases["F0"].to_dict() == {
        "logical_id": "speech:fundamental_frequency",
        "name": "fundamental_frequency",
    }


def test_export_concept_aliases_empty_without_other_forms(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1",
        Concept(concept_id="c1", canonical_name="Solo", lexical_entry=_entry("Solo")),
        message="m",
    )
    with WorldQuery(repo) as world:
        assert export_concept_aliases(world) == {}
