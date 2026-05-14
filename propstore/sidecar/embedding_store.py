"""Sidecar-backed embedding entity APIs."""

from __future__ import annotations

import dataclasses
import sqlite3
from collections.abc import Sequence
from typing import ClassVar

from quire.sqlite_vec_store import (
    EMBEDDING_MODEL_PROJECTION,
    RestoreReport,
    SqliteVecEntityStore,
    SqliteVecRegistry,
    SqliteVecSnapshotStore,
    VecEntitySnapshot,
    VecEntityStoreSpec,
    VecSnapshot,
    embedding_status_projection,
    ensure_embedding_tables as ensure_quire_embedding_tables,
    is_missing_table_error,
    rowid_vec_projection,
)

from propstore.core.embeddings import (
    EmbeddingEntity,
    claim_embedding_text,
    concept_embedding_text,
)
from propstore.core.row_types import ClaimRow, ConceptRow


EMBEDDING_STATUS_PROJECTION = embedding_status_projection(
    name="embedding_status",
    entity_id_column="claim_id",
    index_name="idx_embedding_status_model_identity",
)


CONCEPT_EMBEDDING_STATUS_PROJECTION = embedding_status_projection(
    name="concept_embedding_status",
    entity_id_column="concept_id",
    index_name="idx_concept_embedding_status_model_identity",
)


CLAIM_VEC_PROJECTION = rowid_vec_projection("claim_vec_{model_identity_hash}")
CONCEPT_VEC_PROJECTION = rowid_vec_projection("concept_vec_{model_identity_hash}")


CLAIM_VEC_SPEC = VecEntityStoreSpec(
    name="claim",
    status_projection=EMBEDDING_STATUS_PROJECTION,
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
    join_source = """
        (
            SELECT
                core.id,
                core.seq,
                core.type,
                core.source_paper,
                COALESCE(output_link.concept_id, target_link.concept_id, core.target_concept) AS concept_id,
                txt.auto_summary,
                txt.statement
            FROM claim_core AS core
            LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
            LEFT JOIN claim_concept_link AS output_link
                ON output_link.claim_id = core.id AND output_link.role = 'output'
            LEFT JOIN claim_concept_link AS target_link
                ON target_link.claim_id = core.id AND target_link.role = 'target'
        )
    """
    join_columns = (
        "c.id, c.type, c.auto_summary, c.statement, c.source_paper, c.concept_id"
    )

    def load_entities(
        self,
        entity_ids: Sequence[str] | None = None,
    ) -> list[EmbeddingEntity]:
        query = """
            SELECT
                core.id,
                core.id AS artifact_id,
                core.seq,
                core.content_hash,
                txt.auto_summary,
                txt.statement,
                txt.expression,
                txt.name
            FROM claim_core AS core
            LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        """
        params: tuple[str, ...] = ()
        if entity_ids:
            placeholders = ",".join("?" for _ in entity_ids)
            query += f" WHERE core.id IN ({placeholders})"
            params = tuple(entity_ids)
        rows = self._conn.execute(query, params).fetchall()
        entities: list[EmbeddingEntity] = []
        for row in rows:
            claim = ClaimRow.from_mapping(dict(row))
            if claim.seq is None:
                raise ValueError(f"Claim {claim.claim_id} has no sidecar sequence")
            entities.append(
                EmbeddingEntity(
                    entity_id=str(claim.claim_id),
                    seq=claim.seq,
                    content_hash=str(row["content_hash"]),
                    text=claim_embedding_text(claim),
                )
            )
        return entities

    def resolve_entity(self, entity_id: str) -> tuple[str, int]:
        row = self._conn.execute(
            "SELECT id, seq FROM claim_core WHERE id = ?",
            (entity_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Claim {entity_id} not found")
        return str(row["id"]), int(row["seq"])


class SidecarConceptEmbeddingStore(_SidecarEntityEmbeddingStore):
    spec = CONCEPT_VEC_SPEC
    join_source = "concept"
    join_columns = "c.id, c.primary_logical_id, c.canonical_name, c.definition"

    def load_entities(
        self,
        entity_ids: Sequence[str] | None = None,
    ) -> list[EmbeddingEntity]:
        query = """
            SELECT
                id,
                seq,
                content_hash,
                canonical_name,
                definition
            FROM concept
        """
        params: tuple[str, ...] = ()
        if entity_ids:
            placeholders = ",".join("?" for _ in entity_ids)
            query += f" WHERE id IN ({placeholders})"
            params = tuple(entity_ids)
        rows = self._conn.execute(query, params).fetchall()
        aliases = self._aliases_by_concept_id(tuple(str(row["id"]) for row in rows))
        entities: list[EmbeddingEntity] = []
        for row in rows:
            concept = ConceptRow.from_mapping(dict(row))
            entities.append(
                EmbeddingEntity(
                    entity_id=str(concept.concept_id),
                    seq=int(row["seq"]),
                    content_hash=str(row["content_hash"]),
                    text=concept_embedding_text(
                        concept,
                        aliases.get(str(concept.concept_id), ()),
                    ),
                )
            )
        return entities

    def resolve_entity(self, entity_id: str) -> tuple[str, int]:
        row = self._conn.execute(
            "SELECT id, seq FROM concept WHERE id = ? OR canonical_name = ?",
            (entity_id, entity_id),
        ).fetchone()
        if row is None:
            raise ValueError(f"Concept {entity_id} not found")
        return str(row["id"]), int(row["seq"])

    def _aliases_by_concept_id(
        self,
        concept_ids: Sequence[str],
    ) -> dict[str, tuple[str, ...]]:
        if not concept_ids:
            return {}
        placeholders = ",".join("?" for _ in concept_ids)
        rows = self._conn.execute(
            f"SELECT concept_id, alias_name FROM alias WHERE concept_id IN ({placeholders})",
            tuple(concept_ids),
        ).fetchall()
        aliases: dict[str, list[str]] = {}
        for row in rows:
            aliases.setdefault(str(row["concept_id"]), []).append(str(row["alias_name"]))
        return {
            concept_id: tuple(names)
            for concept_id, names in aliases.items()
        }


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
