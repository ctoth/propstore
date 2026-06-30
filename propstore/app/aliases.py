"""Owner-layer concept alias export.

``export_concept_aliases`` projects every concept's lemon *other forms* (the
surface realizations beyond the canonical written form) into a flat
``alias name -> entry`` map for the ``pks export-aliases`` adapter. The alias's
target is the concept's canonical identity (``logical_id`` = concept id,
``name`` = canonical name). Collisions are last-writer-wins at export time — this
lenient export is distinct from the strict build-time reference index, which
rejects an ambiguous alias outright.
"""

from __future__ import annotations

from dataclasses import dataclass

from propstore.world import WorldQuery


@dataclass(frozen=True)
class AliasExportEntry:
    """The concept an alias resolves to: its logical id and canonical name."""

    logical_id: str
    name: str

    def to_dict(self) -> dict[str, str]:
        return {"logical_id": self.logical_id, "name": self.name}


def export_concept_aliases(world: WorldQuery) -> dict[str, AliasExportEntry]:
    """Map every concept's lemon other-form written reps to their concept.

    Only the ``other_forms`` of a concept's lexical entry are aliases; the
    canonical form is the concept's name, not an alias. A concept with no lexical
    entry contributes nothing. Last-writer-wins on a shared alias name.
    """

    aliases: dict[str, AliasExportEntry] = {}
    for concept in world.all_concepts():
        entry = concept.lexical_entry
        if entry is None:
            continue
        target = AliasExportEntry(
            logical_id=str(concept.concept_id),
            name=concept.canonical_name,
        )
        for form in entry.other_forms:
            if form.written_rep:
                aliases[form.written_rep] = target
    return aliases
