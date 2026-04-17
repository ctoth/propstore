"""Domain objects for embedding inputs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from propstore.core.row_types import ClaimRow, ConceptRow


@dataclass(frozen=True)
class EmbeddingEntity:
    """A sidecar entity prepared for embedding."""

    entity_id: str
    seq: int
    content_hash: str
    text: str


def claim_embedding_text(claim: ClaimRow) -> str:
    """Return the text representation used for claim embeddings."""

    for value in (
        claim.auto_summary,
        claim.statement,
        claim.expression,
        claim.name,
    ):
        if value:
            return str(value)
    return str(claim.claim_id)


def concept_embedding_text(
    concept: ConceptRow,
    aliases: Sequence[str] = (),
) -> str:
    """Return the text representation used for concept embeddings."""

    parts = [concept.canonical_name]
    alias_names = [alias for alias in aliases if alias]
    if alias_names:
        parts.append(f"(also known as: {', '.join(alias_names)})")
    if concept.definition:
        parts.append(f"- {concept.definition}")
    return " ".join(parts)
