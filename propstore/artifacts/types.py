from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

import msgspec

if TYPE_CHECKING:
    from propstore.cli.repository import Repository

TRef = TypeVar("TRef")
TDoc = TypeVar("TDoc")


@dataclass(frozen=True)
class ResolvedArtifact:
    branch: str
    relpath: str
    commit: str | None = None


@dataclass(frozen=True)
class ArtifactContext(Generic[TRef]):
    repo: Repository
    ref: TRef
    branch: str
    relpath: str


@dataclass(frozen=True)
class ArtifactFamily(Generic[TRef, TDoc]):
    name: str
    doc_type: type[TDoc]
    resolve_ref: Callable[[Repository, TRef], ResolvedArtifact]
    normalize_for_write: Callable[[ArtifactContext[TRef], TDoc, object], TDoc] | None = None
    validate_for_write: Callable[[ArtifactContext[TRef], TDoc, object], None] | None = None
    list_refs: Callable[[Repository, str | None, str | None], list[TRef]] | None = None
    scan_type: type[msgspec.Struct] | None = None
