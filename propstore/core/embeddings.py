"""Domain objects and text projection for embedding inputs.

An :class:`EmbeddingEntity` is one sidecar entity prepared for embedding: its id,
its source-row ``seq`` (the integer the vector store keys on), the content hash of
the embedded text (so an unchanged text is skipped on re-embed), and the text
itself. The two ``*_embedding_text`` functions are the embed-text projection — the
single place that decides what string represents a claim or concept for the
embedding model. They read the ONE canonical ``Claim`` / ``Concept`` charters, not
a ``*Row`` mirror (CLAUDE.md substrate boundary).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from propstore.families.claims import Claim
from propstore.families.concepts import Concept


@dataclass(frozen=True)
class EmbeddingEntity:
    """A sidecar entity prepared for embedding."""

    entity_id: str
    seq: int
    content_hash: str
    text: str


def claim_embedding_text(claim: Claim) -> str:
    """The text a claim is embedded as: its statement, else name/expression/body."""

    for value in (claim.statement, claim.name, claim.expression, claim.body):
        if value:
            return str(value)
    return str(claim.claim_id)


def concept_aliases(concept: Concept) -> tuple[str, ...]:
    """The concept's non-canonical written forms (lemon ``other_forms``)."""

    entry = concept.lexical_entry
    if entry is None:
        return ()
    return tuple(form.written_rep for form in entry.other_forms)


def concept_embedding_text(concept: Concept, aliases: Sequence[str] = ()) -> str:
    """The text a concept is embedded as: canonical name + aliases + definition."""

    parts = [concept.canonical_name]
    alias_names = [alias for alias in aliases if alias]
    if alias_names:
        parts.append(f"(also known as: {', '.join(alias_names)})")
    if concept.definition:
        parts.append(f"- {concept.definition}")
    return " ".join(parts)


__all__ = [
    "EmbeddingEntity",
    "claim_embedding_text",
    "concept_aliases",
    "concept_embedding_text",
]
