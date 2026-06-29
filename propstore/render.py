"""Render layer — Phase 1 walking skeleton.

The render layer reads the sidecar projection and applies a :class:`RenderPolicy`
to decide which concepts are *visible*. This is the other half of the
non-commitment proof: the build stores every concept (``propstore.storage``),
and filtering happens HERE, at render time, over the full row set. The same
underlying corpus yields different views under different policies.

A ``DRAFT`` or ``BLOCKED`` concept is present in the sidecar but hidden by the
default :class:`RenderPolicy`; opting a status into the policy makes those rows
visible without touching storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sqlalchemy import select

from quire.sqlalchemy_schema import SqlAlchemySchema
from quire.sqlalchemy_store import readonly_session

from propstore.core.lemon import LexicalEntry, OntologyReference
from propstore.families.concepts import Concept, ConceptStatus


@dataclass(frozen=True)
class RenderPolicy:
    """Which non-default concept statuses to surface at render time.

    Both flags default to ``False``: the default view shows only ``AUTHORED``
    concepts, keeping drafts and blocked items present-in-storage-but-hidden.
    Setting a flag reveals the corresponding status without any change to the
    stored corpus or the sidecar.
    """

    include_drafts: bool = False
    include_blocked: bool = False

    def _hidden_statuses(self) -> frozenset[ConceptStatus]:
        hidden: set[ConceptStatus] = set()
        if not self.include_drafts:
            hidden.add(ConceptStatus.DRAFT)
        if not self.include_blocked:
            hidden.add(ConceptStatus.BLOCKED)
        return frozenset(hidden)

    def admits(self, status: ConceptStatus) -> bool:
        """Whether a concept of ``status`` is visible under this policy."""

        return status not in self._hidden_statuses()


class _ConceptRow(Protocol):
    """Structural view of a sidecar concept row.

    The sidecar model is built dynamically from the charter, so it has no static
    class to import. This protocol names exactly the charter-derived columns the
    render reads, giving typed attribute access without a cast or an ``ignore``.
    """

    concept_id: str
    canonical_name: str
    status: ConceptStatus | str
    definition: str | None
    ontology_reference: OntologyReference | None
    lexical_entry: LexicalEntry | None


def _row_to_concept(row: _ConceptRow) -> Concept:
    """Reconstruct the one ``Concept`` type from a sidecar row.

    The row carries the same fields as the charter, so this rebuilds the single
    canonical ``Concept`` — it is not a second spelling or a payload decode.
    """

    status = row.status
    if not isinstance(status, ConceptStatus):
        status = ConceptStatus(status)
    return Concept(
        concept_id=row.concept_id,
        canonical_name=row.canonical_name,
        status=status,
        definition=row.definition,
        ontology_reference=row.ontology_reference,
        lexical_entry=row.lexical_entry,
    )


def render_concepts(
    sidecar_path: Path,
    schema: SqlAlchemySchema,
    policy: RenderPolicy | None = None,
) -> list[Concept]:
    """Return concepts visible under ``policy`` (default policy if ``None``).

    Reads the full sidecar row set, then filters by status at render time. The
    rows themselves are untouched — a hidden concept is omitted from the result,
    not removed from storage.
    """

    resolved = policy if policy is not None else RenderPolicy()
    model = schema.model("concept")
    with readonly_session(sidecar_path, schema) as session:
        rows = list(session.scalars(select(model)))
    concepts = [_row_to_concept(row) for row in rows]
    return [c for c in concepts if resolved.admits(c.status)]
