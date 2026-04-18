from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeAlias

from quire.artifacts import (
    ArtifactContext as _QuireArtifactContext,
    ArtifactFamily as _QuireArtifactFamily,
    ArtifactHandle as _QuireArtifactHandle,
    PreparedArtifact as _QuirePreparedArtifact,
    ResolvedArtifact,
    TDoc,
    TRef,
)

if TYPE_CHECKING:
    from propstore.repository import Repository

    ArtifactContext: TypeAlias = _QuireArtifactContext["Repository", TRef]
    ArtifactFamily: TypeAlias = _QuireArtifactFamily["Repository", TRef, TDoc]
    ArtifactHandle: TypeAlias = _QuireArtifactHandle["Repository", TRef, TDoc]
    PreparedArtifact: TypeAlias = _QuirePreparedArtifact["Repository", TRef, TDoc]
else:
    class ArtifactFamily(_QuireArtifactFamily[object, TRef, TDoc], Generic[TRef, TDoc]):
        pass

    ArtifactContext = _QuireArtifactContext
    ArtifactHandle = _QuireArtifactHandle
    PreparedArtifact = _QuirePreparedArtifact

__all__ = [
    "ArtifactContext",
    "ArtifactFamily",
    "ArtifactHandle",
    "PreparedArtifact",
    "ResolvedArtifact",
    "TDoc",
    "TRef",
]
