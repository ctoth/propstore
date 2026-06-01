"""Stable embedding-model identity for heuristic embedding caches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quire import canonical_json_sha256


@dataclass(frozen=True)
class EmbeddingModelIdentity:
    """Lossless identity for a provider model plus its cache-relevant config."""

    provider: str
    model_name: str
    model_version: str = ""
    content_digest: str = ""

    @classmethod
    def from_registry_row(cls, row: dict[str, Any]) -> "EmbeddingModelIdentity":
        return cls(
            provider=str(row["provider"]),
            model_name=str(row["model_name"]),
            model_version=str(row["model_version"]),
            content_digest=str(row["content_digest"]),
        )

    @property
    def identity_hash(self) -> str:
        return canonical_json_sha256(
            {
                "provider": self.provider,
                "model_name": self.model_name,
                "model_version": self.model_version,
                "content_digest": self.content_digest,
            }
        )
