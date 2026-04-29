"""Stable embedding-model identity for heuristic embedding caches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quire.hashing import canonical_json_sha256


@dataclass(frozen=True)
class EmbeddingModelIdentity:
    """Lossless identity for a provider model plus its cache-relevant config."""

    provider: str
    model_name: str
    model_version: str = ""
    content_digest: str = ""

    @classmethod
    def from_model_name(
        cls,
        model_name: str,
        *,
        provider: str = "litellm",
        model_version: str = "",
        normalize: bool | None = None,
        provider_kwargs: dict[str, Any] | None = None,
    ) -> "EmbeddingModelIdentity":
        digest_payload = {
            "provider": provider,
            "model_name": model_name,
            "model_version": model_version,
            "normalize": normalize,
            "provider_kwargs": provider_kwargs or {},
        }
        return cls(
            provider=provider,
            model_name=model_name,
            model_version=model_version,
            content_digest=canonical_json_sha256(digest_payload),
        )

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
