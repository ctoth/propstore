"""The ``MergeManifest`` entity — the record of a two-parent storage merge.

A merge manifest is the durable record of one repository merge (Phase 9-2): it
names the two branches that were merged and carries the formal merge object's
surviving claim alternatives as *arguments*. The merge boundary never collapses
disagreement (CLAUDE.md), so the manifest holds **every rival** that survived the
three-way merge — divergent versions of the same artifact each appear as their own
argument with their own ``assertion_id``. The manifest is the queryable witness
that the rivals were preserved, not resolved.

Like :class:`~propstore.families.conflicts.ConflictProjection` and
:class:`~propstore.families.diagnostics.BuildDiagnostic`, this is a *record* family
with no ``semantic`` tag and no foreign keys: a merge argument may reference a
quarantined or blocked claim and must still record. The class IS the document; the
charter's fields are exactly the stored fields and the sidecar ``merge_manifest``
columns. There is no ``MergeManifestDocument`` second spelling.
"""

from __future__ import annotations

from typing import Annotated

import msgspec

from quire.charter_class import CharterDoc, charter, charter_field


class MergeManifestWitness(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """The provenance witness tying one merge argument back to its source claim."""

    source_artifact_id: str
    source_paper: str | None = None
    source_page: int | None = None
    branch_origin: str | None = None


class MergeManifestArgument(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """One claim alternative the merge boundary materialized.

    ``assertion_id`` is the argument's propositional identity; ``artifact_id`` is
    the storage identity of the claim version it materialized. Two rival versions of
    the same ``artifact_id`` carry distinct ``assertion_id`` values — that is the
    non-commitment surface made durable.
    """

    assertion_id: str
    canonical_claim_id: str
    artifact_id: str
    branch_origins: tuple[str, ...]
    materialized: bool
    logical_id: str | None = None
    witness_basis: tuple[MergeManifestWitness, ...] = ()


class MergeManifestCandidate(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A cluster of arguments the merge flagged as cross-claim semantic candidates."""

    assertion_ids: tuple[str, ...]


@charter(
    key="merge_manifest",
    name="merge_manifest",
    contract_version="2026.06.29",
    placement="merge_manifest",
    identity_field="manifest_id",
)
class MergeManifest(CharterDoc):
    """The record of one two-parent storage merge.

    ``manifest_id`` is the identity (derived from the merged branches and the
    surviving arguments, so a re-merge of the same branches records the same
    manifest). ``arguments`` holds the surviving rival claim alternatives;
    ``semantic_candidates`` flags cross-claim clusters the merge could not collapse.
    """

    manifest_id: Annotated[str, charter_field(primary_key=True)]
    branch_a: str
    branch_b: str
    arguments: Annotated[
        tuple[MergeManifestArgument, ...], charter_field(json=True)
    ] = ()
    semantic_candidates: Annotated[
        tuple[MergeManifestCandidate, ...], charter_field(json=True)
    ] = ()
