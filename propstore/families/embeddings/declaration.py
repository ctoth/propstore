"""Embedding derived-store declarations and entity APIs."""

from __future__ import annotations

import dataclasses
import importlib
import sqlite3
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import ClassVar

from quire.derived_store import DerivedStoreHandle
from sqlalchemy import or_, select
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
from propstore.heuristic.embed import (
    _embed_entities,
    _find_similar_agree_generic,
    _find_similar_disagree_generic,
    _find_similar_entities,
)
from propstore.families.world_charters import world_sqlalchemy_schema


def _require_sqlite_vec():
    try:
        return importlib.import_module("sqlite_vec")
    except ImportError:
        raise ImportError(
            "sqlite-vec is required for embedding commands. "
            "Install with: uv pip install 'propstore[embeddings]'"
        )


def load_vec_extension(conn: sqlite3.Connection) -> None:
    sqlite_vec = _require_sqlite_vec()
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)


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


def ensure_embedding_tables(_conn: sqlite3.Connection) -> None:
    return None


class _SidecarEntityEmbeddingStore:
    cache_name: ClassVar[str]

    def __init__(self, derived_store: DerivedStoreHandle) -> None:
        self._derived_store = derived_store

    def ensure_storage(self) -> None:
        return None

    def existing_content_hashes(self, model_identity) -> dict[str, str]:
        schema = world_sqlalchemy_schema()
        cache = schema.vector_cache(self.cache_name)
        with self._derived_store.readonly_session(schema) as derived:
            return SqlAlchemyVecEntityStore(
                derived.session.connection(),
                cache,
            ).existing_content_hashes(model_identity)

    def prepare_model(
        self,
        model_identity,
        dimensions: int,
        created_at: str,
    ) -> None:
        schema = world_sqlalchemy_schema()
        cache = schema.vector_cache(self.cache_name)
        with self._derived_store.writable_session(schema) as derived:
            SqlAlchemyVecEntityStore(
                derived.session.connection(),
                cache,
            ).prepare_model(
                model_identity,
                created_at,
                dimensions=dimensions,
            )
            derived.commit()

    def save_embedding(
        self,
        model_identity,
        entity: EmbeddingEntity,
        vector_blob: bytes,
        embedded_at: str,
    ) -> None:
        schema = world_sqlalchemy_schema()
        cache = schema.vector_cache(self.cache_name)
        with self._derived_store.writable_session(schema) as derived:
            SqlAlchemyVecEntityStore(
                derived.session.connection(),
                cache,
            ).save_embedding(
                model_identity=model_identity,
                entity_id=entity.entity_id,
                seq=entity.seq,
                content_hash=entity.content_hash,
                vector_blob=vector_blob,
                embedded_at=embedded_at,
            )
            derived.commit()

    def vector_for(
        self,
        model_identity,
        seq: int,
    ) -> bytes | None:
        schema = world_sqlalchemy_schema()
        cache = schema.vector_cache(self.cache_name)
        with self._derived_store.readonly_session(schema) as derived:
            return SqlAlchemyVecEntityStore(
                derived.session.connection(),
                cache,
            ).vector_for(model_identity, seq)

    def similar_entities(
        self,
        model_identity,
        query_vector: bytes,
        k: int,
    ) -> list[dict]:
        schema = world_sqlalchemy_schema()
        cache = schema.vector_cache(self.cache_name)
        with self._derived_store.readonly_session(schema) as derived:
            rows = SqlAlchemyVecEntityStore(
                derived.session.connection(),
                cache,
            ).similar_entities(
                model_identity=model_identity,
                query_vector=query_vector,
                k=k,
            )
        return self._similarity_rows(rows)

    def _similarity_rows(self, rows: list[dict]) -> list[dict]:
        return rows


class SidecarClaimEmbeddingStore(_SidecarEntityEmbeddingStore):
    cache_name = "claim_embeddings"

    def load_entities(
        self,
        entity_ids: Sequence[str] | None = None,
    ) -> list[EmbeddingEntity]:
        schema = world_sqlalchemy_schema()
        claim = schema.model("claim_core")
        entities: list[EmbeddingEntity] = []
        with self._derived_store.readonly_session(schema) as derived:
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

    def resolve_entity(self, entity_id: str) -> tuple[str, int]:
        schema = world_sqlalchemy_schema()
        claim = schema.model("claim_core")
        with self._derived_store.readonly_session(schema) as derived:
            row = derived.execute(
                select(claim.id, claim.seq).where(claim.id == entity_id)
            ).first()
        if row is None:
            raise ValueError(f"Claim {entity_id} not found")
        return str(row[0]), int(row[1])

    def _similarity_rows(self, rows: list[dict]) -> list[dict]:
        entity_ids = tuple(str(row["entity_id"]) for row in rows)
        if not entity_ids:
            return []
        schema = world_sqlalchemy_schema()
        claim = schema.model("claim_core")
        concept_link = schema.model("claim_concept_link")
        with self._derived_store.readonly_session(schema) as derived:
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
        enriched: list[dict] = []
        for row in rows:
            claim_id = str(row["entity_id"])
            claim_model = claims.get(claim_id)
            if claim_model is None:
                continue
            text_payload = claim_model.text_payload
            enriched.append(
                {
                    "id": claim_id,
                    "distance": row["distance"],
                    "rowid": row["rowid"],
                    "auto_summary": (
                        None if text_payload is None else text_payload.auto_summary
                    ),
                    "statement": (
                        None if text_payload is None else text_payload.statement
                    ),
                    "source_paper": claim_model.source_paper,
                    "concept_id": concepts_by_claim_id.get(claim_id),
                }
            )
        return enriched


class SidecarConceptEmbeddingStore(_SidecarEntityEmbeddingStore):
    cache_name = "concept_embeddings"

    def load_entities(
        self,
        entity_ids: Sequence[str] | None = None,
    ) -> list[EmbeddingEntity]:
        schema = world_sqlalchemy_schema()
        concept = schema.model("concept")
        alias = schema.model("alias")
        entities: list[EmbeddingEntity] = []
        with self._derived_store.readonly_session(schema) as derived:
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

    def resolve_entity(self, entity_id: str) -> tuple[str, int]:
        schema = world_sqlalchemy_schema()
        concept = schema.model("concept")
        with self._derived_store.readonly_session(schema) as derived:
            row = derived.execute(
                select(concept.id, concept.seq).where(
                    or_(concept.id == entity_id, concept.canonical_name == entity_id)
                )
            ).first()
        if row is None:
            raise ValueError(f"Concept {entity_id} not found")
        return str(row[0]), int(row[1])

    def _similarity_rows(self, rows: list[dict]) -> list[dict]:
        entity_ids = tuple(str(row["entity_id"]) for row in rows)
        if not entity_ids:
            return []
        schema = world_sqlalchemy_schema()
        concept = schema.model("concept")
        with self._derived_store.readonly_session(schema) as derived:
            concepts = {
                model.id: model
                for model in derived.execute(
                    select(concept).where(concept.id.in_(entity_ids))
                ).scalars()
            }
        enriched: list[dict] = []
        for row in rows:
            concept_id = str(row["entity_id"])
            concept_model = concepts.get(concept_id)
            if concept_model is None:
                continue
            enriched.append(
                {
                    "id": concept_id,
                    "distance": row["distance"],
                    "rowid": row["rowid"],
                    "primary_logical_id": concept_model.primary_logical_id,
                    "canonical_name": concept_model.canonical_name,
                    "definition": concept_model.definition,
                }
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
        SidecarClaimEmbeddingStore(derived_store),
        model_name,
        claim_ids,
        batch_size,
        on_progress,
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
        SidecarConceptEmbeddingStore(derived_store),
        model_name,
        concept_ids,
        batch_size,
        on_progress,
    )


def find_similar(
    derived_store: DerivedStoreHandle,
    claim_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[dict]:
    """Find top-k most similar claims by embedding distance."""

    return _find_similar_entities(
        SidecarClaimEmbeddingStore(derived_store),
        claim_id,
        model_name,
        top_k,
    )


def find_similar_concepts(
    derived_store: DerivedStoreHandle,
    concept_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[dict]:
    """Find top-k most similar concepts by embedding distance."""

    return _find_similar_entities(
        SidecarConceptEmbeddingStore(derived_store),
        concept_id,
        model_name,
        top_k,
    )


def find_similar_agree(
    derived_store: DerivedStoreHandle,
    claim_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Claims similar under all stored models."""

    return _find_similar_agree_generic(
        SidecarClaimEmbeddingStore(derived_store),
        claim_id,
        get_registered_models(derived_store),
        top_k,
    )


def find_similar_disagree(
    derived_store: DerivedStoreHandle,
    claim_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Claims similar under some stored models but not others."""

    return _find_similar_disagree_generic(
        SidecarClaimEmbeddingStore(derived_store),
        claim_id,
        get_registered_models(derived_store),
        top_k,
    )


def find_similar_concepts_agree(
    derived_store: DerivedStoreHandle,
    concept_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Concepts similar under all stored models."""

    return _find_similar_agree_generic(
        SidecarConceptEmbeddingStore(derived_store),
        concept_id,
        get_registered_models(derived_store),
        top_k,
    )


def find_similar_concepts_disagree(
    derived_store: DerivedStoreHandle,
    concept_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Concepts similar under some stored models but not others."""

    return _find_similar_disagree_generic(
        SidecarConceptEmbeddingStore(derived_store),
        concept_id,
        get_registered_models(derived_store),
        top_k,
    )


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

