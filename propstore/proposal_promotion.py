"""Shared transaction helper for already-planned proposal promotions."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Generic, TypeVar


RefT = TypeVar("RefT")
DocT = TypeVar("DocT")
TransactionT = TypeVar("TransactionT")


@dataclass(frozen=True)
class PlannedCanonicalArtifact(Generic[RefT, DocT]):
    ref: RefT
    document: DocT


def commit_planned_canonical_artifacts(
    transact: Callable[..., AbstractContextManager[TransactionT]],
    *,
    message: str,
    family: Callable[[TransactionT], Any],
    artifacts: Iterable[PlannedCanonicalArtifact[RefT, DocT]],
) -> int:
    planned = tuple(artifacts)
    if not planned:
        return 0
    with transact(message=message) as transaction:
        writer = family(transaction)
        for artifact in planned:
            writer.save(artifact.ref, artifact.document)
    return len(planned)
