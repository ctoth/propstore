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

from sqlalchemy import select

from quire.sqlalchemy_schema import SqlAlchemySchema
from quire.sqlalchemy_store import readonly_session

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


def _row_to_concept(row: object) -> Concept:
    """Reconstruct the one ``Concept`` type from a sidecar row.

    The row carries the same fields as the charter, so this rebuilds the single
    canonical ``Concept`` — it is not a second spelling or a payload decode.
    """

    status = row.status  # type: ignore[attr-defined]
    if not isinstance(status, ConceptStatus):
        status = ConceptStatus(status)
    return Concept(
        concept_id=row.concept_id,  # type: ignore[attr-defined]
        canonical_name=row.canonical_name,  # type: ignore[attr-defined]
        status=status,
        definition=row.definition,  # type: ignore[attr-defined]
        ontology_reference=row.ontology_reference,  # type: ignore[attr-defined]
        lexical_entry=row.lexical_entry,  # type: ignore[attr-defined]
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
