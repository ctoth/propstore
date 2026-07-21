"""Application-layer owner for render-time description-claim coreference.

``pks event`` asks a plain question — "which description claims does the corpus
currently treat as the same event/thing?" — and the answer is NOT stored. Rival
merge-argument hypotheses live on the ``proposal/coreference`` branch
(:mod:`propstore.families.coreference`); this owner resolves them into coreference
*clusters* at render time by running Dung argumentation under a
:class:`~propstore.core.render_policy.RenderPolicy`'s semantics
(:mod:`propstore.core.lemon.coreference`). The SAME stored arguments yield
DIFFERENT clusters under grounded (sceptical) vs preferred (credulous) — the
policy-dependence is the whole point (CLAUDE.md non-commitment), so this owner
takes a policy and never bakes one in.

This module owns the query and authoring *semantics*; the CLI
(:mod:`propstore.cli.event`) is a thin adapter over the typed request/report/
failure objects here. It imports Click nothing, writes to no stream, and calls no
``sys.exit`` (CLAUDE.md CLI-adapter discipline). The world-query read surface it
uses is :func:`propstore.world.queries.select_coreference_merge_arguments`, over a
sidecar the family repository projects.

Semantics coverage is honest: :meth:`CoreferenceQuery.clusters` supports only
``grounded`` and ``preferred``. Any other :class:`ArgumentationSemantics` returns a
typed :class:`UnsupportedCoreferenceSemantics` — never a silent fallback to
grounded, and never an exception used for control flow across this boundary.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from quire.sqlalchemy_store import readonly_session

from propstore.core.lemon.coreference import coreference_query
from propstore.core.lemon.description_kinds import CoreferenceMergeArgument
from propstore.core.reasoning import ArgumentationSemantics
from propstore.core.render_policy import RenderPolicy
from propstore.families.coreference import (
    CoreferenceMergeArgumentDoc,
    CoreferenceMergeArgumentRepository,
    derive_coreference_argument_id,
    stated_provenance,
)
from propstore.provenance import Provenance
from propstore.world.queries import select_coreference_merge_arguments

if TYPE_CHECKING:
    from propstore.repository import Repository


# ── semantics mapping ────────────────────────────────────────────────────────
#
# CoreferenceQuery.clusters accepts only these two; the wider ArgumentationSemantics
# vocabulary is mapped here and anything else is a typed failure, per the task's
# honest-gap requirement.
_SEMANTICS_TO_CLUSTERS_NAME: dict[ArgumentationSemantics, str] = {
    ArgumentationSemantics.GROUNDED: "grounded",
    ArgumentationSemantics.PREFERRED: "preferred",
}


@dataclass(frozen=True)
class UnsupportedCoreferenceSemantics:
    """Typed failure: the requested semantics is not one coreference can resolve.

    Coreference clusters are only defined for the sceptical ``grounded`` and the
    credulous ``preferred`` semantics. A request for any other semantics returns
    this (never a silent fallback), carrying both the requested value and the
    supported set so the adapter can render an actionable message.
    """

    requested: ArgumentationSemantics
    supported: tuple[ArgumentationSemantics, ...]

    def message(self) -> str:
        supported = ", ".join(item.value for item in self.supported)
        return (
            f"coreference does not support semantics '{self.requested.value}'; "
            f"supported semantics: {supported}"
        )


@dataclass(frozen=True)
class CoreferenceClusterView:
    """One resolved coreference cluster and the merge arguments that support it.

    ``claim_ids`` are the description claims the render treats as coreferent under
    the report's semantics. ``supporting_arguments`` are the accepted merge
    arguments whose supports fall in this cluster — carried in full so the
    drill-down can show each argument's provenance (the ``pks event`` inspection).
    """

    claim_ids: tuple[str, ...]
    supporting_arguments: tuple[CoreferenceMergeArgumentDoc, ...]


@dataclass(frozen=True)
class CoreferenceClustersReport:
    """Every coreference cluster admitted under ``semantics``.

    Under ``preferred`` a claim may appear in more than one cluster (rival
    credulous extensions); the report never picks one — it returns them all.
    """

    semantics: ArgumentationSemantics
    clusters: tuple[CoreferenceClusterView, ...]


@dataclass(frozen=True)
class CoreferenceProposalResult:
    """The identity of an authored merge-argument proposal."""

    argument_id: str


# ── authoring (writes proposal docs, nothing more) ───────────────────────────


def propose_coreference_merge_argument(
    repo: Repository,
    *,
    supports: tuple[str, ...],
    description_claim_ids: tuple[str, ...] = (),
    provenance: Provenance | None = None,
    note: str | None = None,
) -> CoreferenceProposalResult:
    """Author one merge-argument proposal on ``proposal/coreference``; return its id.

    Writes a proposal doc and nothing else — no canonical edge, no promotion (there
    is none, by design). The ``argument_id`` is content-derived from ``supports``,
    so re-proposing the same merge is idempotent. A merge argument may reference
    claims that are not (yet) canonical: it is a heuristic-layer candidate.
    """

    resolved_description = description_claim_ids or supports
    document = CoreferenceMergeArgumentDoc(
        argument_id=derive_coreference_argument_id(supports),
        provenance=provenance if provenance is not None else stated_provenance(),
        supports=tuple(supports),
        description_claim_ids=tuple(resolved_description),
        note=note,
    )
    _repository(repo).author(
        document, message=f"Propose coreference merge argument {document.argument_id}"
    )
    return CoreferenceProposalResult(argument_id=document.argument_id)


class UnknownCoreferenceArgument(Exception):
    """Raised when an attack names a merge argument that is not stored."""

    def __init__(self, argument_id: str) -> None:
        super().__init__(f"unknown coreference merge argument: {argument_id}")
        self.argument_id = argument_id


def record_coreference_attack(
    repo: Repository, *, attacker_id: str, target_id: str
) -> None:
    """Record that ``attacker_id`` attacks ``target_id`` between stored arguments.

    The attack is stored on the attacker's own doc (its ``attacks`` set), so the
    two rival hypotheses remain independent rows — recording the conflict never
    merges or resolves them. Both arguments must already be stored.
    """

    repository = _repository(repo)
    attacker = repository.get(attacker_id)
    if attacker is None:
        raise UnknownCoreferenceArgument(attacker_id)
    if repository.get(target_id) is None:
        raise UnknownCoreferenceArgument(target_id)
    if target_id in attacker.attacks:
        return
    updated = CoreferenceMergeArgumentDoc(
        argument_id=attacker.argument_id,
        provenance=attacker.provenance,
        supports=attacker.supports,
        description_claim_ids=attacker.description_claim_ids,
        attacks=(*attacker.attacks, target_id),
        note=attacker.note,
    )
    repository.author(
        updated, message=f"Record coreference attack {attacker_id} -> {target_id}"
    )


# ── query (resolves clusters at render time under a policy) ───────────────────


def coreference_clusters(
    repo: Repository, policy: RenderPolicy
) -> CoreferenceClustersReport | UnsupportedCoreferenceSemantics:
    """Resolve every coreference cluster admitted under ``policy``'s semantics.

    Returns a typed :class:`UnsupportedCoreferenceSemantics` when the policy asks
    for a semantics coreference cannot resolve (never a silent grounded fallback).
    """

    semantics_name = _SEMANTICS_TO_CLUSTERS_NAME.get(policy.semantics)
    if semantics_name is None:
        return UnsupportedCoreferenceSemantics(
            requested=policy.semantics,
            supported=tuple(_SEMANTICS_TO_CLUSTERS_NAME),
        )

    documents = _load_merge_arguments(repo)
    by_id = {document.argument_id: document for document in documents}
    query = coreference_query(
        tuple(_to_merge_argument(document) for document in documents),
        attacks=_attack_pairs(documents),
    )
    clusters = query.clusters(semantics=semantics_name)
    return CoreferenceClustersReport(
        semantics=policy.semantics,
        clusters=tuple(_cluster_view(cluster, by_id) for cluster in clusters),
    )


def coreference_clusters_for_claim(
    repo: Repository, claim_id: str, policy: RenderPolicy
) -> CoreferenceClustersReport | UnsupportedCoreferenceSemantics:
    """The cluster(s) containing ``claim_id`` under ``policy``'s semantics.

    A claim may sit in rival clusters under ``preferred`` semantics; this returns
    ALL of them and never picks one. A claim in no accepted cluster yields an empty
    report (honest absence), not an error.
    """

    resolved = coreference_clusters(repo, policy)
    if isinstance(resolved, UnsupportedCoreferenceSemantics):
        return resolved
    return CoreferenceClustersReport(
        semantics=resolved.semantics,
        clusters=tuple(
            cluster for cluster in resolved.clusters if claim_id in cluster.claim_ids
        ),
    )


# ── internals ────────────────────────────────────────────────────────────────


def _repository(repo: Repository) -> CoreferenceMergeArgumentRepository:
    return CoreferenceMergeArgumentRepository(backend=repo.require_git())


def _load_merge_arguments(repo: Repository) -> list[CoreferenceMergeArgumentDoc]:
    """Read every stored merge-argument proposal through the world-query surface.

    The family repository projects the ``proposal/coreference`` docs into a fresh
    sidecar and :func:`select_coreference_merge_arguments` reads every row back —
    the same git-to-sidecar-to-select path the rest of the world uses, scoped to
    this one family.
    """

    repository = _repository(repo)
    with tempfile.TemporaryDirectory() as directory:
        sidecar = Path(directory) / "coreference.sqlite"
        schema = repository.build_sidecar(sidecar)
        with readonly_session(sidecar, schema) as session:
            return select_coreference_merge_arguments(session)


def _to_merge_argument(document: CoreferenceMergeArgumentDoc) -> CoreferenceMergeArgument:
    """Lower a stored proposal doc to the lemon compute struct (a construction)."""

    return CoreferenceMergeArgument(
        argument_id=document.argument_id,
        description_claim_ids=document.description_claim_ids,
        supports=document.supports,
        provenance=document.provenance,
        attacks=document.attacks,
    )


def _attack_pairs(
    documents: list[CoreferenceMergeArgumentDoc],
) -> tuple[tuple[str, str], ...]:
    """The (attacker, target) pairs across all stored arguments.

    Only pairs whose target is itself a stored argument are kept: the Dung
    framework is built over stored arguments, and a dangling attack target would
    fail the merge-protocol's known-argument check.
    """

    known = {document.argument_id for document in documents}
    return tuple(
        (document.argument_id, target)
        for document in documents
        for target in document.attacks
        if target in known
    )


def _cluster_view(
    cluster: frozenset[str],
    by_id: dict[str, CoreferenceMergeArgumentDoc],
) -> CoreferenceClusterView:
    """Attach to a cluster the stored arguments whose supports fall inside it."""

    claim_ids = tuple(sorted(cluster))
    supporting = tuple(
        document
        for argument_id in sorted(by_id)
        for document in (by_id[argument_id],)
        if set(document.supports) <= cluster and document.supports
    )
    return CoreferenceClusterView(claim_ids=claim_ids, supporting_arguments=supporting)
