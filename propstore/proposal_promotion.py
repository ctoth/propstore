"""Shared transaction helper for already-planned proposal promotions.

A *promotion* is the one place a heuristic-layer proposal becomes (proposed)
canonical content (CLAUDE.md layer 3 → layer 1). The planning that decides *which*
proposals are eligible lives with each proposal family; this module owns only the
final, shared write: take a batch of :class:`PlannedCanonicalArtifact` and commit
them through a single transaction so a multi-artifact promotion is atomic.

The helper is deliberately generic over the transaction surface: callers pass the
``transact`` they already hold (``repo.families.transact`` or a
``head_bound_transaction``-derived one) and a ``family`` selector that picks the
target writer off the opened transaction. Nothing here knows about a specific
family — that knowledge stays at the call site, per the substrate-boundary rule.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

RefT = TypeVar("RefT")
DocT = TypeVar("DocT")
TransactionT = TypeVar("TransactionT")

RefT_contra = TypeVar("RefT_contra", contravariant=True)
DocT_contra = TypeVar("DocT_contra", contravariant=True)


class _ArtifactWriter(Protocol[RefT_contra, DocT_contra]):
    """Minimal writer surface a transaction family exposes for a save."""

    def save(self, ref: RefT_contra, document: DocT_contra) -> object: ...


@dataclass(frozen=True)
class PlannedCanonicalArtifact(Generic[RefT, DocT]):
    """One canonical write a promotion has already resolved: where and what."""

    ref: RefT
    document: DocT


def commit_planned_canonical_artifacts(
    transact: Callable[..., AbstractContextManager[TransactionT]],
    *,
    message: str,
    family: Callable[[TransactionT], _ArtifactWriter[RefT, DocT]],
    artifacts: Iterable[PlannedCanonicalArtifact[RefT, DocT]],
) -> int:
    """Save every planned artifact through one ``transact``; return the count.

    Opens the transaction exactly once (and only when there is something to
    write), selects the target family off it, and saves each artifact in order.
    An empty batch is a no-op that opens no transaction.
    """

    planned = tuple(artifacts)
    if not planned:
        return 0
    with transact(message=message) as transaction:
        writer = family(transaction)
        for artifact in planned:
            writer.save(artifact.ref, artifact.document)
    return len(planned)
