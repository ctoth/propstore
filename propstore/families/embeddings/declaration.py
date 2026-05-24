"""Embedding derived-store declarations and entity APIs."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Sequence
from pathlib import Path

from quire.derived_store import DerivedStoreHandle
from sqlalchemy import select
from quire.sqlalchemy_store import readonly_session
from quire.sqlite_vec_store import (
    RestoreReport,
    SqlAlchemyVecEntityStore,
    SqlAlchemyVecRegistry,
    SqlAlchemyVecSnapshotStore,
    VecEntitySnapshot,
    VecSnapshot,
)

from propstore.core.embeddings import (
    EmbeddingEntity,
    claim_embedding_text,
    concept_embedding_text,
)
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
)
from propstore.core.store_results import ClaimSimilarityHit, ConceptSimilarityHit
from propstore.heuristic.embed import (
    _embed_entities,
    _find_similar_agree_generic,
    _find_similar_disagree_generic,
    _find_similar_entities,
)
from propstore.heuristic.embedding_identity import EmbeddingModelIdentity
from propstore.families.world_charters import world_sqlalchemy_schema


@dataclasses.dataclass
class EmbeddingSnapshot:
    models: list[dict]
    claim_statuses: list[dict]
    claim_vectors: dict[str, list[tuple[int, str, bytes]]]
    concept_statuses: list[dict]
    concept_vectors: dict[str, list[tuple[int, str, bytes]]]

    @classmethod
    def from_vec_snapshot(cls, snapshot: VecSnapshot) -> "EmbeddingSnapshot":
        claim_snapshot = snapshot.entities.get(
            "claim_embeddings",
            VecEntitySnapshot(statuses=[], vectors={}),
        )
        concept_snapshot = snapshot.entities.get(
            "concept_embeddings",
            VecEntitySnapshot(statuses=[], vectors={}),
        )
        return cls(
            models=snapshot.models,
            claim_statuses=claim_snapshot.statuses,
            claim_vectors=claim_snapshot.vectors,
            concept_statuses=concept_snapshot.statuses,
            concept_vectors=concept_snapshot.vectors,
        )

    def to_vec_snapshot(self) -> VecSnapshot:
        return VecSnapshot(
            models=self.models,
            entities={
                "claim_embeddings": VecEntitySnapshot(
                    statuses=self.claim_statuses,
                    vectors=self.claim_vectors,
                ),
                "concept_embeddings": VecEntitySnapshot(
                    statuses=self.concept_statuses,
                    vectors=self.concept_vectors,
                ),
            },
        )


@dataclasses.dataclass(frozen=True)
class EmbeddingSnapshotReport:
    model_count: int
    claim_vector_count: int
    concept_vector_count: int


def _load_claim_embedding_entities(
    derived_store: DerivedStoreHandle,
    entity_ids: Sequence[str] | None = None,
) -> list[EmbeddingEntity]:
    schema = world_sqlalchemy_schema()
    claim = schema.model("claim_core")
    entities: list[EmbeddingEntity] = []
    with derived_store.readonly_session(schema) as derived:
        stmt = select(claim)
        if entity_ids:
            stmt = stmt.where(claim.id.in_(tuple(entity_ids)))
        claims = list(derived.execute(stmt).scalars())
    for claim_model in claims:
        if claim_model.seq is None:
            raise ValueError(f"Claim {claim_model.id} has no sidecar sequence")
        entities.append(
            EmbeddingEntity(
                entity_id=str(claim_model.id),
                seq=int(claim_model.seq),
                content_hash=str(claim_model.content_hash),
                text=claim_embedding_text(claim_model),
            )
        )
    return entities


def _load_concept_embedding_entities(
    derived_store: DerivedStoreHandle,
    entity_ids: Sequence[str] | None = None,
) -> list[EmbeddingEntity]:
    schema = world_sqlalchemy_schema()
    concept = schema.model("concept")
    alias = schema.model("alias")
    entities: list[EmbeddingEntity] = []
    with derived_store.readonly_session(schema) as derived:
        stmt = select(concept)
        if entity_ids:
            stmt = stmt.where(concept.id.in_(tuple(entity_ids)))
        concepts = list(derived.execute(stmt).scalars())
        concept_ids = tuple(row.id for row in concepts)
        aliases_by_concept_id: dict[str, list[str]] = {
            concept_id: [] for concept_id in concept_ids
        }
        if concept_ids:
            alias_rows = derived.execute(
                select(alias.concept_id, alias.alias_name).where(
                    alias.concept_id.in_(concept_ids)
                )
            )
            for concept_id, alias_name in alias_rows:
                aliases_by_concept_id.setdefault(str(concept_id), []).append(
                    str(alias_name)
                )
    for concept_model in concepts:
        entities.append(
            EmbeddingEntity(
                entity_id=str(concept_model.id),
                seq=int(concept_model.seq),
                content_hash=str(concept_model.content_hash),
                text=concept_embedding_text(
                    concept_model,
                    tuple(aliases_by_concept_id.get(str(concept_model.id), ())),
                ),
            )
        )
    return entities


def _existing_content_hashes(
    derived_store: DerivedStoreHandle,
    cache_name: str,
    model_identity: EmbeddingModelIdentity,
) -> dict[str, str]:
    schema = world_sqlalchemy_schema()
    with derived_store.readonly_session(schema) as derived:
        return SqlAlchemyVecEntityStore(
            derived.session.connection(),
            schema.vector_cache(cache_name),
        ).existing_content_hashes(model_identity)


def _prepare_model(
    derived_store: DerivedStoreHandle,
    cache_name: str,
    model_identity: EmbeddingModelIdentity,
    dimensions: int,
    created_at: str,
) -> None:
    schema = world_sqlalchemy_schema()
    with derived_store.writable_session(schema) as derived:
        SqlAlchemyVecEntityStore(
            derived.session.connection(),
            schema.vector_cache(cache_name),
        ).prepare_model(
            model_identity,
            created_at,
            dimensions=dimensions,
        )
        derived.commit()


def _save_embedding(
    derived_store: DerivedStoreHandle,
    cache_name: str,
    model_identity: EmbeddingModelIdentity,
    entity: EmbeddingEntity,
    vector_blob: bytes,
    embedded_at: str,
) -> None:
    schema = world_sqlalchemy_schema()
    with derived_store.writable_session(schema) as derived:
        SqlAlchemyVecEntityStore(
            derived.session.connection(),
            schema.vector_cache(cache_name),
        ).save_embedding(
            model_identity=model_identity,
            entity_id=entity.entity_id,
            seq=entity.seq,
            content_hash=entity.content_hash,
            vector_blob=vector_blob,
            embedded_at=embedded_at,
        )
        derived.commit()


def _embedding_entity_key(
    derived_store: DerivedStoreHandle,
    family_name: str,
    entity_id: str,
) -> tuple[str, int]:
    schema = world_sqlalchemy_schema()
    model = schema.model(family_name)
    with derived_store.readonly_session(schema) as derived:
        resolved_id = schema.require_reference_id(
            derived.session,
            family_name,
            entity_id,
        )
        identity_field = getattr(model, schema.identity_field(family_name))
        row = derived.execute(
            select(identity_field, model.seq).where(identity_field == resolved_id)
        ).first()
    if row is None:
        raise ValueError(f"{family_name} {entity_id} not found")
    return str(row[0]), int(row[1])


def _vector_for(
    derived_store: DerivedStoreHandle,
    cache_name: str,
    model_identity: EmbeddingModelIdentity,
    seq: int,
) -> bytes | None:
    schema = world_sqlalchemy_schema()
    with derived_store.readonly_session(schema) as derived:
        return SqlAlchemyVecEntityStore(
            derived.session.connection(),
            schema.vector_cache(cache_name),
        ).vector_for(model_identity, seq)


def _similar_vector_rows(
    derived_store: DerivedStoreHandle,
    cache_name: str,
    model_identity: EmbeddingModelIdentity,
    query_vector: bytes,
    k: int,
) -> list[dict]:
    schema = world_sqlalchemy_schema()
    with derived_store.readonly_session(schema) as derived:
        return SqlAlchemyVecEntityStore(
            derived.session.connection(),
            schema.vector_cache(cache_name),
        ).similar_entities(
            model_identity=model_identity,
            query_vector=query_vector,
            k=k,
        )


def _claim_similarity_hits(
    derived_store: DerivedStoreHandle,
    rows: Sequence[dict],
) -> list[ClaimSimilarityHit]:
    entity_ids = tuple(str(row["entity_id"]) for row in rows)
    if not entity_ids:
        return []
    schema = world_sqlalchemy_schema()
    claim = schema.model("claim_core")
    concept_link = schema.model("claim_concept_link")
    with derived_store.readonly_session(schema) as derived:
        claims = {
            model.id: model
            for model in derived.execute(
                select(claim).where(claim.id.in_(entity_ids))
            ).scalars()
        }
        concept_rows = derived.execute(
            select(concept_link.claim_id, concept_link.concept_id).where(
                concept_link.claim_id.in_(entity_ids)
            )
        )
        concepts_by_claim_id: dict[str, str] = {}
        for claim_id, concept_id in concept_rows:
            concepts_by_claim_id.setdefault(str(claim_id), str(concept_id))
    enriched: list[ClaimSimilarityHit] = []
    for row in rows:
        claim_id = str(row["entity_id"])
        claim_model = claims.get(claim_id)
        if claim_model is None:
            continue
        text_payload = claim_model.text_payload
        enriched.append(
            ClaimSimilarityHit(
                claim_id=ClaimId(claim_id),
                distance=float(row["distance"]),
                auto_summary=None if text_payload is None else text_payload.auto_summary,
                statement=None if text_payload is None else text_payload.statement,
                source_paper=claim_model.source_paper,
                concept_id=(
                    None
                    if concepts_by_claim_id.get(claim_id) is None
                    else ConceptId(str(concepts_by_claim_id[claim_id]))
                ),
            )
        )
    return enriched


def _concept_similarity_hits(
    derived_store: DerivedStoreHandle,
    rows: Sequence[dict],
) -> list[ConceptSimilarityHit]:
    entity_ids = tuple(str(row["entity_id"]) for row in rows)
    if not entity_ids:
        return []
    schema = world_sqlalchemy_schema()
    concept = schema.model("concept")
    with derived_store.readonly_session(schema) as derived:
        concepts = {
            model.id: model
            for model in derived.execute(
                select(concept).where(concept.id.in_(entity_ids))
            ).scalars()
        }
    enriched: list[ConceptSimilarityHit] = []
    for row in rows:
        concept_id = str(row["entity_id"])
        concept_model = concepts.get(concept_id)
        if concept_model is None:
            continue
        enriched.append(
            ConceptSimilarityHit(
                concept_id=ConceptId(concept_id),
                distance=float(row["distance"]),
                primary_logical_id=concept_model.primary_logical_id,
                canonical_name=concept_model.canonical_name,
                definition=concept_model.definition,
            )
        )
    return enriched


def get_registered_models(derived_store: DerivedStoreHandle) -> list[dict]:
    """Return all registered embedding models."""

    schema = world_sqlalchemy_schema()
    with derived_store.readonly_session(schema) as derived:
        return SqlAlchemyVecRegistry(derived.session.connection()).get_registered_models()


def embed_claims(
    derived_store: DerivedStoreHandle,
    model_name: str,
    claim_ids: list[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Generate and store embeddings for claims."""

    return _embed_entities(
        _load_claim_embedding_entities(derived_store, claim_ids),
        model_name,
        existing_content_hashes=lambda model_identity: _existing_content_hashes(
            derived_store,
            "claim_embeddings",
            model_identity,
        ),
        prepare_model=lambda model_identity, dimensions, created_at: _prepare_model(
            derived_store,
            "claim_embeddings",
            model_identity,
            dimensions,
            created_at,
        ),
        save_embedding=lambda model_identity, entity, vector_blob, embedded_at: (
            _save_embedding(
                derived_store,
                "claim_embeddings",
                model_identity,
                entity,
                vector_blob,
                embedded_at,
            )
        ),
        batch_size=batch_size,
        on_progress=on_progress,
    )


def embed_concepts(
    derived_store: DerivedStoreHandle,
    model_name: str,
    concept_ids: list[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Generate and store embeddings for concepts."""

    return _embed_entities(
        _load_concept_embedding_entities(derived_store, concept_ids),
        model_name,
        existing_content_hashes=lambda model_identity: _existing_content_hashes(
            derived_store,
            "concept_embeddings",
            model_identity,
        ),
        prepare_model=lambda model_identity, dimensions, created_at: _prepare_model(
            derived_store,
            "concept_embeddings",
            model_identity,
            dimensions,
            created_at,
        ),
        save_embedding=lambda model_identity, entity, vector_blob, embedded_at: (
            _save_embedding(
                derived_store,
                "concept_embeddings",
                model_identity,
                entity,
                vector_blob,
                embedded_at,
            )
        ),
        batch_size=batch_size,
        on_progress=on_progress,
    )


def find_similar(
    derived_store: DerivedStoreHandle,
    claim_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[ClaimSimilarityHit]:
    """Find top-k most similar claims by embedding distance."""

    rows = _find_similar_entities(
        claim_id,
        model_name,
        resolve_entity=lambda entity_id: _embedding_entity_key(
            derived_store,
            "claim_core",
            entity_id,
        ),
        vector_for=lambda model_identity, seq: _vector_for(
            derived_store,
            "claim_embeddings",
            model_identity,
            seq,
        ),
        similar_entities=lambda model_identity, query_vector, k: (
            _similar_vector_rows(
                derived_store,
                "claim_embeddings",
                model_identity,
                query_vector,
                k,
            )
        ),
        top_k=top_k,
    )
    return _claim_similarity_hits(derived_store, rows)


def find_similar_concepts(
    derived_store: DerivedStoreHandle,
    concept_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[ConceptSimilarityHit]:
    """Find top-k most similar concepts by embedding distance."""

    rows = _find_similar_entities(
        concept_id,
        model_name,
        resolve_entity=lambda entity_id: _embedding_entity_key(
            derived_store,
            "concept",
            entity_id,
        ),
        vector_for=lambda model_identity, seq: _vector_for(
            derived_store,
            "concept_embeddings",
            model_identity,
            seq,
        ),
        similar_entities=lambda model_identity, query_vector, k: (
            _similar_vector_rows(
                derived_store,
                "concept_embeddings",
                model_identity,
                query_vector,
                k,
            )
        ),
        top_k=top_k,
    )
    return _concept_similarity_hits(derived_store, rows)


def find_similar_agree(
    derived_store: DerivedStoreHandle,
    claim_id: str,
    top_k: int = 10,
) -> list[ClaimSimilarityHit]:
    """Claims similar under all stored models."""

    rows = _find_similar_agree_generic(
        claim_id,
        get_registered_models(derived_store),
        resolve_entity=lambda entity_id: _embedding_entity_key(
            derived_store,
            "claim_core",
            entity_id,
        ),
        vector_for=lambda model_identity, seq: _vector_for(
            derived_store,
            "claim_embeddings",
            model_identity,
            seq,
        ),
        similar_entities=lambda model_identity, query_vector, k: (
            _similar_vector_rows(
                derived_store,
                "claim_embeddings",
                model_identity,
                query_vector,
                k,
            )
        ),
        top_k=top_k,
    )
    return _claim_similarity_hits(derived_store, rows)


def find_similar_disagree(
    derived_store: DerivedStoreHandle,
    claim_id: str,
    top_k: int = 10,
) -> list[ClaimSimilarityHit]:
    """Claims similar under some stored models but not others."""

    rows = _find_similar_disagree_generic(
        claim_id,
        get_registered_models(derived_store),
        resolve_entity=lambda entity_id: _embedding_entity_key(
            derived_store,
            "claim_core",
            entity_id,
        ),
        vector_for=lambda model_identity, seq: _vector_for(
            derived_store,
            "claim_embeddings",
            model_identity,
            seq,
        ),
        similar_entities=lambda model_identity, query_vector, k: (
            _similar_vector_rows(
                derived_store,
                "claim_embeddings",
                model_identity,
                query_vector,
                k,
            )
        ),
        top_k=top_k,
    )
    return _claim_similarity_hits(derived_store, rows)


def find_similar_concepts_agree(
    derived_store: DerivedStoreHandle,
    concept_id: str,
    top_k: int = 10,
) -> list[ConceptSimilarityHit]:
    """Concepts similar under all stored models."""

    rows = _find_similar_agree_generic(
        concept_id,
        get_registered_models(derived_store),
        resolve_entity=lambda entity_id: _embedding_entity_key(
            derived_store,
            "concept",
            entity_id,
        ),
        vector_for=lambda model_identity, seq: _vector_for(
            derived_store,
            "concept_embeddings",
            model_identity,
            seq,
        ),
        similar_entities=lambda model_identity, query_vector, k: (
            _similar_vector_rows(
                derived_store,
                "concept_embeddings",
                model_identity,
                query_vector,
                k,
            )
        ),
        top_k=top_k,
    )
    return _concept_similarity_hits(derived_store, rows)


def find_similar_concepts_disagree(
    derived_store: DerivedStoreHandle,
    concept_id: str,
    top_k: int = 10,
) -> list[ConceptSimilarityHit]:
    """Concepts similar under some stored models but not others."""

    rows = _find_similar_disagree_generic(
        concept_id,
        get_registered_models(derived_store),
        resolve_entity=lambda entity_id: _embedding_entity_key(
            derived_store,
            "concept",
            entity_id,
        ),
        vector_for=lambda model_identity, seq: _vector_for(
            derived_store,
            "concept_embeddings",
            model_identity,
            seq,
        ),
        similar_entities=lambda model_identity, query_vector, k: (
            _similar_vector_rows(
                derived_store,
                "concept_embeddings",
                model_identity,
                query_vector,
                k,
            )
        ),
        top_k=top_k,
    )
    return _concept_similarity_hits(derived_store, rows)


def extract_embedding_snapshot_from_store(
    sidecar: Path,
    *,
    on_snapshot: Callable[[EmbeddingSnapshotReport], None] | None = None,
) -> EmbeddingSnapshot | None:
    if not sidecar.exists():
        return None
    try:
        schema = world_sqlalchemy_schema()
        with readonly_session(sidecar, schema) as derived:
            snapshot = SqlAlchemyVecSnapshotStore(
                derived.session.connection(),
                tuple(schema.vector_caches.values()),
            ).extract()
        if snapshot is None:
            return None
        embedding_snapshot = EmbeddingSnapshot.from_vec_snapshot(snapshot)
        if on_snapshot is not None:
            on_snapshot(
                EmbeddingSnapshotReport(
                    model_count=len(embedding_snapshot.models),
                    claim_vector_count=sum(
                        len(vectors)
                        for vectors in embedding_snapshot.claim_vectors.values()
                    ),
                    concept_vector_count=sum(
                        len(vectors)
                        for vectors in embedding_snapshot.concept_vectors.values()
                    ),
                )
            )
        return embedding_snapshot
    except ImportError:
        return None


def restore_embedding_snapshot_to_session(
    derived,
    snapshot: EmbeddingSnapshot,
) -> RestoreReport | None:
    caches = tuple(derived.schema.vector_caches.values())
    if not caches:
        return None
    return SqlAlchemyVecSnapshotStore(
        derived.session.connection(),
        caches,
    ).restore(snapshot.to_vec_snapshot())
