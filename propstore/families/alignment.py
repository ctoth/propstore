"""Durable typed proposals for concept alignment across imported snapshots.

An alignment artifact records rival concepts exactly as they exist on pinned
repository-import commits.  It is an open partial-argumentation proposal: no
concept is merged, promoted, or treated as truth by authoring this document.
The nested value objects are the document shape; there is no proposal payload,
record mirror, or conversion layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

import msgspec
from quire.artifacts import BranchPlacement, FlatYamlPlacement
from quire.charter_class import CharterDoc, charter, charter_field
from quire.refs import single_field_ref_type

from propstore.core.lemon import LexicalEntry, OntologyReference


CONCEPT_ALIGNMENT_BRANCH = BranchPlacement(
    policy="fixed", fixed_branch="proposal/concepts"
)
"""Place every concept-alignment proposal on ``proposal/concepts``."""


if TYPE_CHECKING:

    @dataclass(frozen=True)
    class ConceptAlignmentRef:
        slug: str

else:
    ConceptAlignmentRef = single_field_ref_type(
        "ConceptAlignmentRef", "slug", module=__name__
    )


CONCEPT_ALIGNMENT_PLACEMENT: FlatYamlPlacement[object, ConceptAlignmentRef] = (
    FlatYamlPlacement(
        "merge/concepts",
        ConceptAlignmentRef,
        ref_field="slug",
        branch=CONCEPT_ALIGNMENT_BRANCH,
    )
)


def _empty_operator_scores() -> dict[str, dict[str, int]]:
    return {}


class AlignmentArgument(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """One typed imported concept and the commits that make it reproducible."""

    id: str
    repository_origin: str
    source_commit: str
    import_branch: str
    import_commit: str
    concept_id: str
    canonical_name: str
    ontology_reference: OntologyReference | None = None
    lexical_entry: LexicalEntry | None = None
    definition: str | None = None
    form: str | None = None


class AlignmentFramework(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """The attack/ignorance/non-attack partition of ordered argument pairs."""

    attacks: tuple[tuple[str, str], ...] = ()
    ignorance: tuple[tuple[str, str], ...] = ()
    non_attacks: tuple[tuple[str, str], ...] = ()


class AlignmentQueries(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """Acceptance results computed directly by the argumentation substrate."""

    skeptical_acceptance: tuple[str, ...] = ()
    credulous_acceptance: tuple[str, ...] = ()
    operator_scores: dict[str, dict[str, int]] = msgspec.field(
        default_factory=_empty_operator_scores
    )


class AlignmentDecision(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A deferred human decision; imported-snapshot proposals begin open."""

    status: str = "open"
    accepted: tuple[str, ...] = ()
    rejected: tuple[str, ...] = ()
    promoted_concept: str | None = None


@charter(
    key="concept_alignment",
    name="concept_alignment_framework",
    contract_version="2026.07.12",
    placement=CONCEPT_ALIGNMENT_PLACEMENT,
    accessor="concept_alignments",
    identity_field="alignment_id",
)
class ConceptAlignmentArtifact(CharterDoc):
    """A durable open PAF proposal over independently addressable concepts."""

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
