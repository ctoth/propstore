"""Embedding generation and similarity search over a vector-store protocol.

This is the generic, store-agnostic heuristic layer: :func:`embed_entities`
embeds the entities an :class:`_EmbeddingStore` yields and persists their vectors;
the ``_find_similar_*`` functions read a :class:`_SimilarityStore` for k-nearest
neighbours and for multi-model agree/disagree signals. Both store protocols are
satisfied by the sidecar stores in :mod:`propstore.families.embeddings.declaration`
(which compose quire's vector adapter).

``litellm`` is the optional ``[embeddings]`` extra: it is imported lazily through
:func:`require_litellm` so the core package and the ``pks`` CLI import and run
without the extra installed; the import hint is raised only when an embedding call
is actually made. Similarity carries each hit's distance as a heuristic score — a
no-hit query returns ``[]``, never a fabricated distance.
"""

from __future__ import annotations

import importlib
import struct
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from types import ModuleType
from typing import Any, Protocol

from propstore.core.embeddings import EmbeddingEntity
from propstore.heuristic.embedding_identity import EmbeddingModelIdentity


class _EmbeddingStore(Protocol):
    def ensure_storage(self) -> None: ...

    def load_entities(
        self, entity_ids: Sequence[str] | None = None
    ) -> list[EmbeddingEntity]: ...

    def existing_content_hashes(
        self, model_identity: EmbeddingModelIdentity
    ) -> Mapping[str, str]: ...

    def prepare_model(
        self,
        model_identity: EmbeddingModelIdentity,
        dimensions: int,
        created_at: str,
    ) -> None: ...

    def save_embedding(
        self,
        model_identity: EmbeddingModelIdentity,
        entity: EmbeddingEntity,
        vector_blob: bytes,
        embedded_at: str,
    ) -> None: ...


class _SimilarityStore(Protocol):
    def resolve_entity(self, entity_id: str) -> tuple[str, int]: ...

    def vector_for(
        self, model_identity: EmbeddingModelIdentity, seq: int
    ) -> bytes | None: ...

    def similar_entities(
        self,
        model_identity: EmbeddingModelIdentity,
        query_vector: bytes,
        k: int,
    ) -> list[dict[str, Any]]: ...


def require_litellm() -> ModuleType:
    try:
        return importlib.import_module("litellm")
    except ImportError as exc:
        raise ImportError(
            "litellm is required for embedding commands. "
            "Install with: uv pip install 'propstore[embeddings]'"
        ) from exc


def serialize_float32(vector: Sequence[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def deserialize_float32(blob: bytes) -> list[float]:
    count = len(blob) // 4
    return list(struct.unpack(f"{count}f", blob))


def _embedding_vector(response: Any, index: int) -> list[float]:
    """Launder one embedding row out of the untyped litellm response."""

    return [float(value) for value in response.data[index]["embedding"]]


def embed_entities(
    store: _EmbeddingStore,
    model_name: str,
    entity_ids: Sequence[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, int]:
    """Embed the store's entities; return ``{embedded, skipped, errors}`` counts.

    Skips an entity whose stored content hash already matches (re-embed is a
    no-op on unchanged text). A transient embedding-API failure for a batch is
    counted in ``errors`` and the batch is skipped; an unexpected error (e.g. a
    provider ``RuntimeError`` or a storage ``OperationalError``) propagates — it
    is not silently swallowed.
    """

    litellm = require_litellm()
    store.ensure_storage()
    model_identity = EmbeddingModelIdentity.from_model_name(model_name)
    entities = store.load_entities(entity_ids)
    existing = store.existing_content_hashes(model_identity)

    to_embed: list[EmbeddingEntity] = []
    skipped = 0
    for entity in entities:
        if existing.get(entity.entity_id) == entity.content_hash:
            skipped += 1
            continue
        to_embed.append(entity)

    if not to_embed:
        return {"embedded": 0, "skipped": skipped, "errors": 0}

    embedded = 0
    errors = 0
    dimensions: int | None = None
    now = datetime.now(timezone.utc).isoformat()

    for offset in range(0, len(to_embed), batch_size):
        batch = to_embed[offset : offset + batch_size]
        texts = [entity.text for entity in batch]

        try:
            response = litellm.embedding(model=model_name, input=texts)
        except (ConnectionError, TimeoutError, OSError, ValueError):
            errors += len(batch)
            continue

        if dimensions is None:
            dimensions = len(_embedding_vector(response, 0))
            store.prepare_model(model_identity, dimensions, now)

        for index, entity in enumerate(batch):
            store.save_embedding(
                model_identity,
                entity,
                serialize_float32(_embedding_vector(response, index)),
                now,
            )
            embedded += 1

        if on_progress is not None:
            on_progress(embedded, len(to_embed))

    return {"embedded": embedded, "skipped": skipped, "errors": errors}


def find_similar_entities(
    store: _SimilarityStore,
    entity_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Find the top-k nearest entities under one model name."""

    return find_similar_entities_by_identity(
        store,
        entity_id,
        EmbeddingModelIdentity.from_model_name(model_name),
        top_k,
    )


def find_similar_entities_by_identity(
    store: _SimilarityStore,
    entity_id: str,
    model_identity: EmbeddingModelIdentity,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Find the top-k nearest entities for an already-registered model identity."""

    resolved_id, seq = store.resolve_entity(entity_id)
    vector = store.vector_for(model_identity, seq)
    if vector is None:
        raise ValueError(
            f"No embedding for {resolved_id} under model {model_identity.model_name}"
        )

    results = store.similar_entities(model_identity, vector, top_k + 1)
    return [result for result in results if result["id"] != resolved_id][:top_k]


def find_similar_agree_generic(
    store: _SimilarityStore,
    entity_id: str,
    models: Sequence[dict[str, Any]],
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Entities that are near ``entity_id`` under *every* stored model."""

    if not models:
        return []

    result_sets: list[set[str]] = []
    for model in models:
        try:
            results = find_similar_entities_by_identity(
                store,
                entity_id,
                EmbeddingModelIdentity.from_registry_row(model),
                top_k=top_k * 2,
            )
        except ValueError:
            continue
        result_sets.append({str(result["id"]) for result in results})

    if not result_sets:
        return []

    common_ids = set(result_sets[0])
    for result_set in result_sets[1:]:
        common_ids &= result_set

    all_results = find_similar_entities_by_identity(
        store,
        entity_id,
        EmbeddingModelIdentity.from_registry_row(models[0]),
        top_k=top_k * 2,
    )
    return [result for result in all_results if str(result["id"]) in common_ids][:top_k]


def find_similar_disagree_generic(
    store: _SimilarityStore,
    entity_id: str,
    models: Sequence[dict[str, Any]],
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Entities near ``entity_id`` under some stored models but not others."""

    if len(models) < 2:
        return []

    per_model: dict[str, set[str]] = {}
    for model in models:
        model_identity = EmbeddingModelIdentity.from_registry_row(model)
        try:
            results = find_similar_entities_by_identity(
                store,
                entity_id,
                model_identity,
                top_k=top_k * 2,
            )
        except ValueError:
            continue
        per_model[model_identity.model_name] = {str(result["id"]) for result in results}

    if len(per_model) < 2:
        return []

    all_ids: set[str] = set()
    for ids in per_model.values():
        all_ids |= ids

    disagree_ids = {
        candidate
        for candidate in all_ids
        if 0 < sum(1 for ids in per_model.values() if candidate in ids) < len(per_model)
    }

    results: list[dict[str, Any]] = []
    try:
        all_results = find_similar_entities_by_identity(
            store,
            entity_id,
            EmbeddingModelIdentity.from_registry_row(models[0]),
            top_k=top_k * 3,
        )
    except ValueError:
        return []

    for result in all_results:
        result_id = str(result["id"])
        if result_id not in disagree_ids:
            continue
        result["similar_in"] = [
            model_name for model_name, ids in per_model.items() if result_id in ids
        ]
        result["not_similar_in"] = [
            model_name for model_name, ids in per_model.items() if result_id not in ids
        ]
        results.append(result)

    return results[:top_k]


__all__ = [
    "deserialize_float32",
    "embed_entities",
    "find_similar_agree_generic",
    "find_similar_disagree_generic",
    "find_similar_entities",
    "find_similar_entities_by_identity",
    "require_litellm",
    "serialize_float32",
]
