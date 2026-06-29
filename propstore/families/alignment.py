"""The ``ConceptAlignmentArtifact`` entity — a vocabulary-reconciliation proposal.

When several sources each propose their own name for what may be the same concept,
the heuristic layer reconciles them. The reconciliation is *not* a source mutation:
it is a **proposal artifact** (CLAUDE.md layer 3) that records every candidate, the
partial argumentation framework relating them, and the skeptical/credulous
acceptance verdicts — leaving the final accept/reject/promote decision to an
explicit later step (Phase 8 source subsystem). Nothing here collapses the rival
proposals; the artifact holds them all.

Charter discipline (PLAN.md §12, CLAUDE.md): there is ONE canonical
``ConceptAlignmentArtifact`` charter. Its nested pieces — :class:`AlignmentArgument`,
:class:`AlignmentFramework`, :class:`AlignmentQueries`, :class:`AlignmentDecision`
— are single-spelling ``msgspec.Struct`` value types carried as JSON document
fields, exactly as the lemon entities are carried on :class:`~propstore.families.concepts.Concept`.
There is no ``*Document`` / ``*Record`` / ``*Row`` mirror and no ``to_payload`` /
``from_payload`` conversion: the git document, the sidecar columns, and the
serialized contract all fall out of these annotations.

The argumentation math (building the framework, classifying relations by lemon
identity, computing acceptance) lives in :mod:`propstore.source.alignment`; this
module owns only the artifact's shape.
"""

from __future__ import annotations

from typing import Annotated

import msgspec
from quire.charter_class import CharterDoc, charter, charter_field


def _empty_operator_scores() -> dict[str, dict[str, int]]:
    return {}


class AlignmentArgument(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """One source's proposed concept, as an argument in the alignment framework."""

    id: str
    source: str
    local_handle: str
    proposed_name: str
    proposed_uri: str
    definition: str
    form: str


class AlignmentFramework(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """The three-way partition of ordered argument pairs (a partial AF).

    Mirrors :class:`argumentation.frameworks.partial_af.PartialArgumentationFramework`:
    ``attacks`` are conflicting proposals, ``ignorance`` are pairs the heuristic
    cannot decide (honest non-commitment), and ``non_attacks`` are compatible or
    self pairs. The three sets partition ``arguments x arguments``.
    """

    attacks: tuple[tuple[str, str], ...] = ()
    ignorance: tuple[tuple[str, str], ...] = ()
    non_attacks: tuple[tuple[str, str], ...] = ()


class AlignmentQueries(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """Render-time acceptance verdicts over the alignment framework."""

    skeptical_acceptance: tuple[str, ...] = ()
    credulous_acceptance: tuple[str, ...] = ()
    operator_scores: dict[str, dict[str, int]] = msgspec.field(
        default_factory=_empty_operator_scores
    )


class AlignmentDecision(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """The (deferred) human decision over an alignment cluster.

    An artifact is born ``open``: the heuristic proposes, it never commits. A later
    explicit step records ``decided`` (accept/reject) and finally ``promoted`` with
    the canonical concept URI. No accept/reject value is fabricated by the build.
    """

    status: str = "open"
    accepted: tuple[str, ...] = ()
    rejected: tuple[str, ...] = ()
    promoted_concept: str | None = None


@charter(
    key="concept_alignment",
    name="concept_alignment_framework",
    contract_version="2026.06.29",
    placement="concept_alignment",
    identity_field="alignment_id",
    semantic="propstore.concept_alignment",
)
class ConceptAlignmentArtifact(CharterDoc):
    """A PAF-backed vocabulary-reconciliation proposal over rival concept names.

    The class *is* the document: ``alignment_id`` is the cluster identity; the
    nested arguments/framework/queries/decision project to JSON sidecar columns.
    The artifact is a proposal — authoring it never mutates any source concept.
    """

    alignment_id: Annotated[str, charter_field(primary_key=True)]
    kind: str = "concept_alignment_framework"
    sources: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    arguments: Annotated[tuple[AlignmentArgument, ...], charter_field(json=True)] = ()
    framework: Annotated[AlignmentFramework, charter_field(json=True)] = msgspec.field(
        default_factory=AlignmentFramework
    )
    queries: Annotated[AlignmentQueries, charter_field(json=True)] = msgspec.field(
        default_factory=AlignmentQueries
    )
    decision: Annotated[AlignmentDecision, charter_field(json=True)] = msgspec.field(
        default_factory=AlignmentDecision
    )
