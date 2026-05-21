"""Embedding generation and similarity search."""

from __future__ import annotations

import importlib
import logging
import struct
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from propstore.core.embeddings import EmbeddingEntity
from propstore.heuristic.embedding_identity import EmbeddingModelIdentity


ExistingContentHashes = Callable[[EmbeddingModelIdentity], Mapping[str, str]]
PrepareEmbeddingModel = Callable[[EmbeddingModelIdentity, int, str], None]
SaveEmbedding = Callable[[EmbeddingModelIdentity, EmbeddingEntity, bytes, str], None]
ResolveEmbeddingEntity = Callable[[str], tuple[str, int]]
LoadEmbeddingVector = Callable[[EmbeddingModelIdentity, int], bytes | None]
FindSimilarVectors = Callable[[EmbeddingModelIdentity, bytes, int], list[dict]]


def _require_litellm():
    try:
        return importlib.import_module("litellm")
    except ImportError:
        raise ImportError(
            "litellm is required for embedding commands. "
            "Install with: uv pip install 'propstore[embeddings]'"
        )


def _serialize_float32(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def _deserialize_float32(blob: bytes) -> list[float]:
    count = len(blob) // 4
    return list(struct.unpack(f"{count}f", blob))


def _embed_entities(
    entities: Sequence[EmbeddingEntity],
    model_name: str,
    *,
    existing_content_hashes: ExistingContentHashes,
    prepare_model: PrepareEmbeddingModel,
    save_embedding: SaveEmbedding,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Embed typed entities through explicit vector-cache operations.

    Returns:
        {"embedded": int, "skipped": int, "errors": int}
    """

    litellm = _require_litellm()
    model_identity = EmbeddingModelIdentity.from_model_name(model_name)
    existing = existing_content_hashes(model_identity)

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
    dimensions = None
    now = datetime.now(timezone.utc).isoformat()

    for offset in range(0, len(to_embed), batch_size):
        batch = to_embed[offset:offset + batch_size]
        texts = [entity.text for entity in batch]

        try:
            response = litellm.embedding(model=model_name, input=texts)
        except (ConnectionError, TimeoutError, OSError, ValueError) as exc:
            logging.warning(
                "Embedding API call failed for batch %d: %s",
                offset,
                exc,
            )
            errors += len(batch)
            continue

        if dimensions is None:
            dimensions = len(response.data[0]["embedding"])
            prepare_model(model_identity, dimensions, now)

        for index, entity in enumerate(batch):
            vector = response.data[index]["embedding"]
            save_embedding(
                model_identity,
                entity,
                _serialize_float32(vector),
                now,
            )
            embedded += 1

        if on_progress:
            on_progress(embedded, len(to_embed))

    return {"embedded": embedded, "skipped": skipped, "errors": errors}


def _find_similar_entities(
    entity_id: str,
    model_name: str,
    *,
    resolve_entity: ResolveEmbeddingEntity,
    vector_for: LoadEmbeddingVector,
    similar_entities: FindSimilarVectors,
    top_k: int = 10,
) -> list[dict]:
    """Find top-k similar entities using explicit vector-cache operations."""

    return _find_similar_entities_by_identity(
        entity_id,
        EmbeddingModelIdentity.from_model_name(model_name),
        resolve_entity=resolve_entity,
        vector_for=vector_for,
        similar_entities=similar_entities,
        top_k=top_k,
    )


def _find_similar_entities_by_identity(
    entity_id: str,
    model_identity: EmbeddingModelIdentity,
    *,
    resolve_entity: ResolveEmbeddingEntity,
    vector_for: LoadEmbeddingVector,
    similar_entities: FindSimilarVectors,
    top_k: int = 10,
) -> list[dict]:
    """Find top-k similar entities for an already registered model identity."""

    resolved_id, seq = resolve_entity(entity_id)
    vector = vector_for(model_identity, seq)
    if vector is None:
        raise ValueError(
            f"No embedding for {resolved_id} under model {model_identity.model_name}"
        )

    results = similar_entities(model_identity, vector, top_k + 1)
    return [result for result in results if result["id"] != resolved_id][:top_k]


def _find_similar_agree_generic(
    entity_id: str,
    models: Sequence[dict[str, Any]],
    *,
    resolve_entity: ResolveEmbeddingEntity,
    vector_for: LoadEmbeddingVector,
    similar_entities: FindSimilarVectors,
    top_k: int = 10,
) -> list[dict]:
    """Entities similar under all stored models."""

    if not models:
        return []

    result_sets = []
    for model in models:
        try:
            results = _find_similar_entities_by_identity(
                entity_id,
                EmbeddingModelIdentity.from_registry_row(model),
                resolve_entity=resolve_entity,
                vector_for=vector_for,
                similar_entities=similar_entities,
                top_k=top_k * 2,
            )
            result_sets.append({result["id"] for result in results})
        except ValueError:
            continue

    if not result_sets:
        return []

    common_ids = result_sets[0]
    for result_set in result_sets[1:]:
        common_ids &= result_set

    all_results = _find_similar_entities_by_identity(
        entity_id,
        EmbeddingModelIdentity.from_registry_row(models[0]),
        resolve_entity=resolve_entity,
        vector_for=vector_for,
        similar_entities=similar_entities,
        top_k=top_k * 2,
    )
    return [result for result in all_results if result["id"] in common_ids][:top_k]


def _find_similar_disagree_generic(
    entity_id: str,
    models: Sequence[dict[str, Any]],
    *,
    resolve_entity: ResolveEmbeddingEntity,
    vector_for: LoadEmbeddingVector,
    similar_entities: FindSimilarVectors,
    top_k: int = 10,
) -> list[dict]:
    """Entities similar under some stored models but not others."""

    if len(models) < 2:
        return []

    per_model = {}
    for model in models:
        model_identity = EmbeddingModelIdentity.from_registry_row(model)
        try:
            results = _find_similar_entities_by_identity(
                entity_id,
                model_identity,
                resolve_entity=resolve_entity,
                vector_for=vector_for,
                similar_entities=similar_entities,
                top_k=top_k * 2,
            )
            per_model[model_identity.model_name] = {
                result["id"] for result in results
            }
        except ValueError:
            continue

    if len(per_model) < 2:
        return []

    all_ids = set()
    for ids in per_model.values():
        all_ids |= ids

    disagree_ids = set()
    for candidate_id in all_ids:
        present_in = sum(1 for ids in per_model.values() if candidate_id in ids)
        if 0 < present_in < len(per_model):
            disagree_ids.add(candidate_id)

    results = []
    try:
        all_results = _find_similar_entities_by_identity(
            entity_id,
            EmbeddingModelIdentity.from_registry_row(models[0]),
            resolve_entity=resolve_entity,
            vector_for=vector_for,
            similar_entities=similar_entities,
            top_k=top_k * 3,
        )
        for result in all_results:
            if result["id"] in disagree_ids:
                result["similar_in"] = [
                    model_name
                    for model_name, ids in per_model.items()
                    if result["id"] in ids
                ]
                result["not_similar_in"] = [
                    model_name
                    for model_name, ids in per_model.items()
                    if result["id"] not in ids
                ]
                results.append(result)
    except ValueError:
        pass

    return results[:top_k]
