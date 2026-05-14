"""Sidecar-backed embedding entity and vector APIs."""

from __future__ import annotations

import dataclasses
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Protocol

from propstore.core.embeddings import (
    EmbeddingEntity,
    claim_embedding_text,
    concept_embedding_text,
)
from propstore.core.row_types import ClaimRow, ConceptRow
from propstore.sidecar.projection import (
    ProjectionColumn,
    ProjectionIndex,
    ProjectionTable,
    VecProjection,
)


class _EmbeddingModelIdentity(Protocol):
    @property
    def provider(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    @property
    def model_version(self) -> str: ...

    @property
    def content_digest(self) -> str: ...

    @property
    def identity_hash(self) -> str: ...


@dataclasses.dataclass
class EmbeddingSnapshot:
    models: list[dict]
    claim_statuses: list[dict]
    claim_vectors: dict[str, list[tuple[int, str, bytes]]]
    concept_statuses: list[dict]
    concept_vectors: dict[str, list[tuple[int, str, bytes]]]


@dataclasses.dataclass
class RestoreReport:
    restored: int = 0
    stale: int = 0
    orphaned: int = 0


EMBEDDING_MODEL_PROJECTION = ProjectionTable(
    name="embedding_model",
    columns=(
        ProjectionColumn("model_identity_hash", "TEXT", nullable=False, primary_key=True),
        ProjectionColumn("provider", "TEXT", nullable=False),
        ProjectionColumn("model_name", "TEXT", nullable=False),
        ProjectionColumn(
            "model_version",
            "TEXT",
            nullable=False,
            default_sql="''",
        ),
        ProjectionColumn("content_digest", "TEXT", nullable=False),
        ProjectionColumn("dimensions", "INTEGER", nullable=False),
        ProjectionColumn("created_at", "TEXT", nullable=False),
    ),
    if_not_exists=True,
)


EMBEDDING_STATUS_PROJECTION = ProjectionTable(
    name="embedding_status",
    columns=(
        ProjectionColumn("model_identity_hash", "TEXT", nullable=False),
        ProjectionColumn("claim_id", "TEXT", nullable=False),
        ProjectionColumn("content_hash", "TEXT", nullable=False),
        ProjectionColumn("embedded_at", "TEXT", nullable=False),
    ),
    primary_key=("model_identity_hash", "claim_id"),
    indexes=(ProjectionIndex("idx_embedding_status_model_identity", ("model_identity_hash",)),),
    if_not_exists=True,
)


CONCEPT_EMBEDDING_STATUS_PROJECTION = ProjectionTable(
    name="concept_embedding_status",
    columns=(
        ProjectionColumn("model_identity_hash", "TEXT", nullable=False),
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("content_hash", "TEXT", nullable=False),
        ProjectionColumn("embedded_at", "TEXT", nullable=False),
    ),
    primary_key=("model_identity_hash", "concept_id"),
    indexes=(
        ProjectionIndex(
            "idx_concept_embedding_status_model_identity",
            ("model_identity_hash",),
        ),
    ),
    if_not_exists=True,
)


CLAIM_VEC_PROJECTION = VecProjection(
    table="claim_vec_{model_identity_hash}",
    key_column=None,
    vector_column=ProjectionColumn("embedding", "float[{dimensions}]", nullable=False),
)


CONCEPT_VEC_PROJECTION = VecProjection(
    table="concept_vec_{model_identity_hash}",
    key_column=None,
    vector_column=ProjectionColumn("embedding", "float[{dimensions}]", nullable=False),
)


@dataclasses.dataclass(frozen=True)
class EmbeddingModelProjectionRow:
    model_identity_hash: str
    provider: str
    model_name: str
    model_version: str
    content_digest: str
    dimensions: int
    created_at: str

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "model_identity_hash": self.model_identity_hash,
            "provider": self.provider,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "content_digest": self.content_digest,
            "dimensions": self.dimensions,
            "created_at": self.created_at,
        }


@dataclasses.dataclass(frozen=True)
class EmbeddingStatusProjectionRow:
    model_identity_hash: str
    claim_id: str
    content_hash: str
    embedded_at: str

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "model_identity_hash": self.model_identity_hash,
            "claim_id": self.claim_id,
            "content_hash": self.content_hash,
            "embedded_at": self.embedded_at,
        }


@dataclasses.dataclass(frozen=True)
class ConceptEmbeddingStatusProjectionRow:
    model_identity_hash: str
    concept_id: str
    content_hash: str
    embedded_at: str

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "model_identity_hash": self.model_identity_hash,
            "concept_id": self.concept_id,
            "content_hash": self.content_hash,
            "embedded_at": self.embedded_at,
        }


def _is_missing_table_error(error: sqlite3.OperationalError) -> bool:
    return "no such table" in str(error)


def ensure_embedding_tables(conn: sqlite3.Connection) -> None:
    for projection in (
        EMBEDDING_MODEL_PROJECTION,
        EMBEDDING_STATUS_PROJECTION,
        CONCEPT_EMBEDDING_STATUS_PROJECTION,
    ):
        for statement in projection.ddl_statements():
            conn.execute(statement)


def _vec_projection(prefix: str, dimensions: int) -> VecProjection:
    if prefix == "claim_vec":
        table = CLAIM_VEC_PROJECTION.table
    elif prefix == "concept_vec":
        table = CONCEPT_VEC_PROJECTION.table
    else:
        table = f"{prefix}_{{model_identity_hash}}"
    return VecProjection(
        table=table,
        key_column=None,
        vector_column=ProjectionColumn("embedding", f"float[{dimensions}]", nullable=False),
    )


def _vec_bindings(model_identity_hash: str) -> dict[str, str]:
    return {"model_identity_hash": model_identity_hash}


def _ensure_vec_table(
    conn: sqlite3.Connection,
    model_identity_hash: str,
    dimensions: int,
    prefix: str,
) -> None:
    table_name = f"{prefix}_{model_identity_hash}"
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    if row is None:
        projection = _vec_projection(prefix, dimensions)
        for statement in projection.ddl_statements(_vec_bindings(model_identity_hash)):
            conn.execute(statement)


class SidecarEmbeddingRegistry:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_registered_models(self) -> list[dict]:
        try:
            return [
                dict(row)
                for row in self._conn.execute(
                    """
                    SELECT
                        model_identity_hash,
                        provider,
                        model_name,
                        model_version,
                        content_digest,
                        dimensions,
                        created_at
                    FROM embedding_model
                    """
                ).fetchall()
            ]
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            return []


class _SidecarEntityEmbeddingStore:
    status_table: str
    status_id_column: str
    vec_prefix: str
    join_source: str
    join_columns: str

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def ensure_storage(self) -> None:
        ensure_embedding_tables(self._conn)

    def existing_content_hashes(
        self,
        model_identity: _EmbeddingModelIdentity,
    ) -> dict[str, str]:
        existing: dict[str, str] = {}
        try:
            rows = self._conn.execute(
                f"SELECT {self.status_id_column}, content_hash "
                f"FROM {self.status_table} WHERE model_identity_hash=?",
                (model_identity.identity_hash,),
            ).fetchall()
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            return existing
        for row in rows:
            existing[str(row[self.status_id_column])] = str(row["content_hash"])
        return existing

    def prepare_model(
        self,
        model_identity: _EmbeddingModelIdentity,
        dimensions: int,
        created_at: str,
    ) -> None:
        self._conn.execute(
            EMBEDDING_MODEL_PROJECTION.insert_sql(or_replace=True),
            EmbeddingModelProjectionRow(
                model_identity_hash=model_identity.identity_hash,
                provider=model_identity.provider,
                model_name=model_identity.model_name,
                model_version=model_identity.model_version,
                content_digest=model_identity.content_digest,
                dimensions=dimensions,
                created_at=created_at,
            ).as_insert_mapping(),
        )
        _ensure_vec_table(
            self._conn,
            model_identity.identity_hash,
            dimensions,
            prefix=self.vec_prefix,
        )

    def save_embedding(
        self,
        model_identity: _EmbeddingModelIdentity,
        entity: EmbeddingEntity,
        vector_blob: bytes,
        embedded_at: str,
    ) -> None:
        model_identity_hash = model_identity.identity_hash
        vec_projection = _vec_projection(self.vec_prefix, 0)
        vec_bindings = _vec_bindings(model_identity_hash)
        self._conn.execute(
            vec_projection.delete_rowid_sql(vec_bindings),
            {"rowid": entity.seq},
        )
        self._conn.execute(
            vec_projection.insert_rowid_sql(vec_bindings),
            {"rowid": entity.seq, "embedding": vector_blob},
        )
        status_projection = (
            EMBEDDING_STATUS_PROJECTION
            if self.status_table == "embedding_status"
            else CONCEPT_EMBEDDING_STATUS_PROJECTION
        )
        status_mapping: Mapping[str, object]
        if self.status_table == "embedding_status":
            status_mapping = EmbeddingStatusProjectionRow(
                model_identity_hash=model_identity_hash,
                claim_id=entity.entity_id,
                content_hash=entity.content_hash,
                embedded_at=embedded_at,
            ).as_insert_mapping()
        else:
            status_mapping = ConceptEmbeddingStatusProjectionRow(
                model_identity_hash=model_identity_hash,
                concept_id=entity.entity_id,
                content_hash=entity.content_hash,
                embedded_at=embedded_at,
            ).as_insert_mapping()
        self._conn.execute(
            status_projection.insert_sql(or_replace=True),
            status_mapping,
        )

    def vector_for(
        self,
        model_identity: _EmbeddingModelIdentity,
        seq: int,
    ) -> bytes | None:
        table_name = f"{self.vec_prefix}_{model_identity.identity_hash}"
        row = self._conn.execute(
            f"SELECT embedding FROM [{table_name}] WHERE rowid = ?",
            (seq,),
        ).fetchone()
        return None if row is None else row["embedding"]

    def similar_entities(
        self,
        model_identity: _EmbeddingModelIdentity,
        query_vector: bytes,
        k: int,
    ) -> list[dict]:
        table_name = f"{self.vec_prefix}_{model_identity.identity_hash}"
        rows = self._conn.execute(
            f"""SELECT v.rowid, v.distance, {self.join_columns}
                FROM [{table_name}] v
                JOIN {self.join_source} c ON c.seq = v.rowid
                WHERE v.embedding MATCH ? AND k = ?
                ORDER BY v.distance""",
            (query_vector, k),
        ).fetchall()
        return [dict(row) for row in rows]


class SidecarClaimEmbeddingStore(_SidecarEntityEmbeddingStore):
    status_table = "embedding_status"
    status_id_column = "claim_id"
    vec_prefix = "claim_vec"
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
    status_table = "concept_embedding_status"
    status_id_column = "concept_id"
    vec_prefix = "concept_vec"
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
        self._conn = conn

    def extract(self) -> EmbeddingSnapshot | None:
        try:
            models = [
                dict(row)
                for row in self._conn.execute("SELECT * FROM embedding_model").fetchall()
            ]
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            return None

        if not models:
            return None

        claim_statuses = [
            dict(row)
            for row in self._conn.execute("SELECT * FROM embedding_status").fetchall()
        ]
        claim_vectors: dict[str, list[tuple[int, str, bytes]]] = {}
        for model in models:
            model_identity_hash = model["model_identity_hash"]
            table_name = f"claim_vec_{model_identity_hash}"
            try:
                rows = self._conn.execute(
                    f"""SELECT v.rowid, es.claim_id, v.embedding
                        FROM [{table_name}] v
                        JOIN embedding_status es ON es.model_identity_hash = ?
                        JOIN claim_core c ON c.seq = v.rowid AND c.id = es.claim_id
                        WHERE es.model_identity_hash = ?""",
                    (model_identity_hash, model_identity_hash),
                ).fetchall()
            except sqlite3.OperationalError as error:
                if not _is_missing_table_error(error):
                    raise
                rows = []
            claim_vectors[model_identity_hash] = [
                (int(row[0]), str(row[1]), row[2])
                for row in rows
            ]

        try:
            concept_statuses = [
                dict(row)
                for row in self._conn.execute(
                    "SELECT * FROM concept_embedding_status"
                ).fetchall()
            ]
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            concept_statuses = []

        concept_vectors: dict[str, list[tuple[int, str, bytes]]] = {}
        for model in models:
            model_identity_hash = model["model_identity_hash"]
            table_name = f"concept_vec_{model_identity_hash}"
            try:
                rows = self._conn.execute(
                    f"""SELECT v.rowid, cs.concept_id, v.embedding
                        FROM [{table_name}] v
                        JOIN concept_embedding_status cs ON cs.model_identity_hash = ?
                        JOIN concept c ON c.seq = v.rowid AND c.id = cs.concept_id
                        WHERE cs.model_identity_hash = ?""",
                    (model_identity_hash, model_identity_hash),
                ).fetchall()
            except sqlite3.OperationalError as error:
                if not _is_missing_table_error(error):
                    raise
                rows = []
            concept_vectors[model_identity_hash] = [
                (int(row[0]), str(row[1]), row[2])
                for row in rows
            ]

        return EmbeddingSnapshot(
            models=models,
            claim_statuses=claim_statuses,
            claim_vectors=claim_vectors,
            concept_statuses=concept_statuses,
            concept_vectors=concept_vectors,
        )

    def restore(self, snapshot: EmbeddingSnapshot) -> RestoreReport:
        ensure_embedding_tables(self._conn)
        report = RestoreReport()
        self._restore_claims(snapshot, report)
        self._restore_concepts(snapshot, report)
        return report

    def _restore_claims(
        self,
        snapshot: EmbeddingSnapshot,
        report: RestoreReport,
    ) -> None:
        current_claims: dict[str, tuple[int, str]] = {}
        try:
            rows = self._conn.execute(
                "SELECT id, seq, content_hash FROM claim_core"
            ).fetchall()
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            rows = []
        for row in rows:
            current_claims[str(row["id"])] = (int(row["seq"]), str(row["content_hash"]))

        status_lookup = {
            (
                status["model_identity_hash"],
                status["claim_id"],
            ): status["content_hash"]
            for status in snapshot.claim_statuses
        }
        embedded_at_lookup = {
            (
                status["model_identity_hash"],
                status["claim_id"],
            ): status.get("embedded_at", "")
            for status in snapshot.claim_statuses
        }

        for model in snapshot.models:
            model_identity_hash = model["model_identity_hash"]
            self._conn.execute(
                EMBEDDING_MODEL_PROJECTION.insert_sql(or_replace=True),
                EmbeddingModelProjectionRow(
                    model_identity_hash=str(model_identity_hash),
                    provider=str(model["provider"]),
                    model_name=str(model["model_name"]),
                    model_version=str(model["model_version"]),
                    content_digest=str(model["content_digest"]),
                    dimensions=int(model["dimensions"]),
                    created_at=str(model["created_at"]),
                ).as_insert_mapping(),
            )
            _ensure_vec_table(
                self._conn,
                model_identity_hash,
                int(model["dimensions"]),
                prefix="claim_vec",
            )
            vec_projection = _vec_projection("claim_vec", int(model["dimensions"]))
            vec_bindings = _vec_bindings(str(model_identity_hash))
            status_insert_sql = EMBEDDING_STATUS_PROJECTION.insert_sql(or_replace=True)
            for _old_seq, claim_id, blob in snapshot.claim_vectors.get(
                model_identity_hash,
                [],
            ):
                current = current_claims.get(claim_id)
                if current is None:
                    report.orphaned += 1
                    continue
                new_seq, current_hash = current
                if current_hash != status_lookup.get(
                    (model_identity_hash, claim_id),
                    "",
                ):
                    report.stale += 1
                    continue
                self._conn.execute(
                    vec_projection.insert_rowid_sql(vec_bindings),
                    {"rowid": new_seq, "embedding": blob},
                )
                self._conn.execute(
                    status_insert_sql,
                    EmbeddingStatusProjectionRow(
                        model_identity_hash=str(model_identity_hash),
                        claim_id=claim_id,
                        content_hash=current_hash,
                        embedded_at=embedded_at_lookup.get(
                            (model_identity_hash, claim_id),
                            "",
                        ),
                    ).as_insert_mapping(),
                )
                report.restored += 1

    def _restore_concepts(
        self,
        snapshot: EmbeddingSnapshot,
        report: RestoreReport,
    ) -> None:
        current_concepts: dict[str, tuple[int, str]] = {}
        try:
            rows = self._conn.execute(
                "SELECT id, seq, content_hash FROM concept"
            ).fetchall()
        except sqlite3.OperationalError as error:
            if not _is_missing_table_error(error):
                raise
            rows = []
        for row in rows:
            current_concepts[str(row["id"])] = (
                int(row["seq"]),
                str(row["content_hash"]),
            )

        status_lookup = {
            (
                status["model_identity_hash"],
                status["concept_id"],
            ): status["content_hash"]
            for status in snapshot.concept_statuses
        }
        embedded_at_lookup = {
            (
                status["model_identity_hash"],
                status["concept_id"],
            ): status.get("embedded_at", "")
            for status in snapshot.concept_statuses
        }

        for model in snapshot.models:
            model_identity_hash = model["model_identity_hash"]
            self._conn.execute(
                EMBEDDING_MODEL_PROJECTION.insert_sql(or_replace=True),
                EmbeddingModelProjectionRow(
                    model_identity_hash=str(model_identity_hash),
                    provider=str(model["provider"]),
                    model_name=str(model["model_name"]),
                    model_version=str(model["model_version"]),
                    content_digest=str(model["content_digest"]),
                    dimensions=int(model["dimensions"]),
                    created_at=str(model["created_at"]),
                ).as_insert_mapping(),
            )
            _ensure_vec_table(
                self._conn,
                model_identity_hash,
                int(model["dimensions"]),
                prefix="concept_vec",
            )
            vec_projection = _vec_projection("concept_vec", int(model["dimensions"]))
            vec_bindings = _vec_bindings(str(model_identity_hash))
            status_insert_sql = CONCEPT_EMBEDDING_STATUS_PROJECTION.insert_sql(
                or_replace=True,
            )
            for _old_seq, concept_id, blob in snapshot.concept_vectors.get(
                model_identity_hash,
                [],
            ):
                current = current_concepts.get(concept_id)
                if current is None:
                    report.orphaned += 1
                    continue
                new_seq, current_hash = current
                if current_hash != status_lookup.get(
                    (model_identity_hash, concept_id),
                    "",
                ):
                    report.stale += 1
                    continue
                self._conn.execute(
                    vec_projection.insert_rowid_sql(vec_bindings),
                    {"rowid": new_seq, "embedding": blob},
                )
                self._conn.execute(
                    status_insert_sql,
                    ConceptEmbeddingStatusProjectionRow(
                        model_identity_hash=str(model_identity_hash),
                        concept_id=concept_id,
                        content_hash=current_hash,
                        embedded_at=embedded_at_lookup.get(
                            (model_identity_hash, concept_id),
                            "",
                        ),
                    ).as_insert_mapping(),
                )
                report.restored += 1
