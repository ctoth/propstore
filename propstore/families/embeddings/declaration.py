"""Embedding derived-store declarations and entity APIs."""

from __future__ import annotations

import dataclasses
import importlib
import sqlite3
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import ClassVar

from quire.derived_store import DerivedStoreHandle
from quire.derived_runtime import connect_sqlite_store
from sqlalchemy import or_, select
from quire.sqlite_vec_store import (
    EMBEDDING_MODEL_PROJECTION,
    RestoreReport,
    SqliteVecEntityStore,
    SqliteVecRegistry,
    SqliteVecSnapshotStore,
    VecEntitySnapshot,
    VecEntityStoreSpec,
    VecSnapshot,
    ensure_embedding_tables as ensure_quire_embedding_tables,
    is_missing_table_error,
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
from propstore.families.claims.declaration import (
    CLAIM_EMBEDDING_JOIN_COLUMNS,
    CLAIM_EMBEDDING_JOIN_SOURCE,
    CLAIM_EMBEDDING_STATUS_PROJECTION,
    CLAIM_VEC_PROJECTION,
    resolve_claim_embedding_entity,
    select_claim_embedding_rows,
)
from propstore.families.concepts.declaration import (
    CONCEPT_EMBEDDING_STATUS_PROJECTION,
    CONCEPT_VEC_PROJECTION,
)
from propstore.families.world_charters import world_sqlalchemy_schema


CLAIM_VEC_SPEC = VecEntityStoreSpec(
    name="claim",
    status_projection=CLAIM_EMBEDDING_STATUS_PROJECTION,
    status_id_column="claim_id",
    vector_projection=CLAIM_VEC_PROJECTION,
    source_table="claim_core",
)


CONCEPT_VEC_SPEC = VecEntityStoreSpec(
    name="concept",
    status_projection=CONCEPT_EMBEDDING_STATUS_PROJECTION,
    status_id_column="concept_id",
    vector_projection=CONCEPT_VEC_PROJECTION,
    source_table="concept",
)


EMBEDDING_SPECS = (CLAIM_VEC_SPEC, CONCEPT_VEC_SPEC)


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
            CLAIM_VEC_SPEC.name,
            VecEntitySnapshot(statuses=[], vectors={}),
        )
        concept_snapshot = snapshot.entities.get(
            CONCEPT_VEC_SPEC.name,
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
                CLAIM_VEC_SPEC.name: VecEntitySnapshot(
                    statuses=self.claim_statuses,
                    vectors=self.claim_vectors,
                ),
                CONCEPT_VEC_SPEC.name: VecEntitySnapshot(
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


def ensure_embedding_tables(conn: sqlite3.Connection) -> None:
    ensure_quire_embedding_tables(conn, EMBEDDING_SPECS)


class SidecarEmbeddingRegistry:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._registry = SqliteVecRegistry(conn)

    def get_registered_models(self) -> list[dict]:
        return self._registry.get_registered_models()


class _SidecarEntityEmbeddingStore:
    spec: ClassVar[VecEntityStoreSpec]
    join_source: ClassVar[str]
    join_columns: ClassVar[str]

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._vectors = SqliteVecEntityStore(conn, self.spec)

    def ensure_storage(self) -> None:
        ensure_embedding_tables(self._conn)

    def existing_content_hashes(self, model_identity) -> dict[str, str]:
        return self._vectors.existing_content_hashes(model_identity)

    def prepare_model(
        self,
        model_identity,
        dimensions: int,
        created_at: str,
    ) -> None:
        self._vectors.prepare_model(model_identity, dimensions, created_at)

    def save_embedding(
        self,
        model_identity,
        entity: EmbeddingEntity,
        vector_blob: bytes,
        embedded_at: str,
    ) -> None:
        self._vectors.save_embedding(
            model_identity=model_identity,
            entity_id=entity.entity_id,
            seq=entity.seq,
            content_hash=entity.content_hash,
            vector_blob=vector_blob,
            embedded_at=embedded_at,
        )

    def vector_for(
        self,
        model_identity,
        seq: int,
    ) -> bytes | None:
        return self._vectors.vector_for(model_identity, seq)

    def similar_entities(
        self,
        model_identity,
        query_vector: bytes,
        k: int,
    ) -> list[dict]:
        return self._vectors.similar_entities(
            model_identity=model_identity,
            query_vector=query_vector,
            k=k,
            join_source=self.join_source,
            join_columns=self.join_columns,
        )


class SidecarClaimEmbeddingStore(_SidecarEntityEmbeddingStore):
    spec = CLAIM_VEC_SPEC
    join_source = CLAIM_EMBEDDING_JOIN_SOURCE
    join_columns = CLAIM_EMBEDDING_JOIN_COLUMNS

    def load_entities(
        self,
        entity_ids: Sequence[str] | None = None,
    ) -> list[EmbeddingEntity]:
        entities: list[EmbeddingEntity] = []
        for claim in select_claim_embedding_rows(self._conn, entity_ids):
            if claim.seq is None:
                raise ValueError(f"Claim {claim.claim_id} has no sidecar sequence")
            entities.append(
                EmbeddingEntity(
                    entity_id=str(claim.claim_id),
                    seq=claim.seq,
                    content_hash=str(claim.content_hash),
                    text=claim_embedding_text(claim),
                )
            )
        return entities

    def resolve_entity(self, entity_id: str) -> tuple[str, int]:
        return resolve_claim_embedding_entity(self._conn, entity_id)


class SidecarConceptEmbeddingStore(_SidecarEntityEmbeddingStore):
    spec = CONCEPT_VEC_SPEC
    join_source = "concept"
    join_columns = "c.id, c.primary_logical_id, c.canonical_name, c.definition"

    def __init__(self, conn: sqlite3.Connection, derived_store: DerivedStoreHandle) -> None:
        super().__init__(conn)
        self._derived_store = derived_store

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
                    entity_id=str(concept_model.concept_id),
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


class SidecarEmbeddingSnapshotStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._snapshots = SqliteVecSnapshotStore(conn, EMBEDDING_SPECS)

    def extract(self) -> EmbeddingSnapshot | None:
        snapshot = self._snapshots.extract()
        if snapshot is None:
            return None
        return EmbeddingSnapshot.from_vec_snapshot(snapshot)

    def restore(self, snapshot: EmbeddingSnapshot) -> RestoreReport:
        return self._snapshots.restore(snapshot.to_vec_snapshot())


_is_missing_table_error = is_missing_table_error


def get_registered_models(conn: sqlite3.Connection) -> list[dict]:
    """Return all registered embedding models."""

    return SidecarEmbeddingRegistry(conn).get_registered_models()


def embed_claims(
    conn: sqlite3.Connection,
    model_name: str,
    claim_ids: list[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Generate and store embeddings for claims."""

    return _embed_entities(
        SidecarClaimEmbeddingStore(conn),
        model_name,
        claim_ids,
        batch_size,
        on_progress,
    )


def embed_concepts(
    conn: sqlite3.Connection,
    model_name: str,
    *,
    derived_store: DerivedStoreHandle,
    concept_ids: list[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Generate and store embeddings for concepts."""

    return _embed_entities(
        SidecarConceptEmbeddingStore(conn, derived_store),
        model_name,
        concept_ids,
        batch_size,
        on_progress,
    )


def find_similar(
    conn: sqlite3.Connection,
    claim_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[dict]:
    """Find top-k most similar claims by embedding distance."""

    return _find_similar_entities(
        SidecarClaimEmbeddingStore(conn),
        claim_id,
        model_name,
        top_k,
    )


def find_similar_concepts(
    conn: sqlite3.Connection,
    concept_id: str,
    model_name: str,
    *,
    derived_store: DerivedStoreHandle,
    top_k: int = 10,
) -> list[dict]:
    """Find top-k most similar concepts by embedding distance."""

    return _find_similar_entities(
        SidecarConceptEmbeddingStore(conn, derived_store),
        concept_id,
        model_name,
        top_k,
    )


def find_similar_agree(
    conn: sqlite3.Connection,
    claim_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Claims similar under all stored models."""

    return _find_similar_agree_generic(
        SidecarClaimEmbeddingStore(conn),
        claim_id,
        get_registered_models(conn),
        top_k,
    )


def find_similar_disagree(
    conn: sqlite3.Connection,
    claim_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Claims similar under some stored models but not others."""

    return _find_similar_disagree_generic(
        SidecarClaimEmbeddingStore(conn),
        claim_id,
        get_registered_models(conn),
        top_k,
    )


def find_similar_concepts_agree(
    conn: sqlite3.Connection,
    concept_id: str,
    *,
    derived_store: DerivedStoreHandle,
    top_k: int = 10,
) -> list[dict]:
    """Concepts similar under all stored models."""

    return _find_similar_agree_generic(
        SidecarConceptEmbeddingStore(conn, derived_store),
        concept_id,
        get_registered_models(conn),
        top_k,
    )


def find_similar_concepts_disagree(
    conn: sqlite3.Connection,
    concept_id: str,
    *,
    derived_store: DerivedStoreHandle,
    top_k: int = 10,
) -> list[dict]:
    """Concepts similar under some stored models but not others."""

    return _find_similar_disagree_generic(
        SidecarConceptEmbeddingStore(conn, derived_store),
        concept_id,
        get_registered_models(conn),
        top_k,
    )


def extract_embeddings(conn: sqlite3.Connection) -> EmbeddingSnapshot | None:
    """Extract all embedding data before sidecar rebuild."""

    return SidecarEmbeddingSnapshotStore(conn).extract()


def extract_embedding_snapshot_from_store(
    sidecar: Path,
    *,
    on_snapshot: Callable[[EmbeddingSnapshotReport], None] | None = None,
) -> EmbeddingSnapshot | None:
    if not sidecar.exists():
        return None
    snapshot_conn = None
    try:
        snapshot_conn = connect_sqlite_store(sidecar)
        snapshot_conn.row_factory = sqlite3.Row
        load_vec_extension(snapshot_conn)
        snapshot = extract_embeddings(snapshot_conn)
        if snapshot is None:
            return None
        if on_snapshot is not None:
            on_snapshot(
                EmbeddingSnapshotReport(
                    model_count=len(snapshot.models),
                    claim_vector_count=sum(
                        len(vectors) for vectors in snapshot.claim_vectors.values()
                    ),
                    concept_vector_count=sum(
                        len(vectors) for vectors in snapshot.concept_vectors.values()
                    ),
                )
            )
        return snapshot
    except ImportError:
        return None
    finally:
        if snapshot_conn is not None:
            snapshot_conn.close()


def restore_embeddings(
    conn: sqlite3.Connection,
    snapshot: EmbeddingSnapshot,
) -> RestoreReport:
    """Restore embeddings after sidecar rebuild."""

    return SidecarEmbeddingSnapshotStore(conn).restore(snapshot)


def restore_embedding_snapshot(
    conn: sqlite3.Connection,
    snapshot: EmbeddingSnapshot,
) -> RestoreReport:
    conn.row_factory = sqlite3.Row
    try:
        load_vec_extension(conn)
        return restore_embeddings(conn, snapshot)
    finally:
        conn.row_factory = None
