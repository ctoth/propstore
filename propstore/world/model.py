"""WorldModel — read-only reasoner over a compiled sidecar."""

from __future__ import annotations

import json
import sqlite3
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, Any

from propstore.cel_checker import (
    ConceptInfo,
    KindType,
    with_standard_synthetic_bindings,
)
from propstore.cel_registry import build_store_cel_registry
from propstore.cel_types import to_cel_exprs
from propstore.core.assertions import ContextReference
from propstore.core.id_types import to_concept_id, to_context_id
from propstore.core.labels import compile_environment_assumptions
from propstore.core.micropublications import ActiveMicropublication
from propstore.core.store_results import (
    WorldStoreStats,
    ClaimSimilarityHit,
    ConceptSearchHit,
    ConceptSimilarityHit,
)
from propstore.core.row_types import (
    ClaimRow,
    ConceptRow,
    ConflictRow,
    ParameterizationRow,
    RelationshipRow,
    StanceRow,
)
from quire.tree_path import FilesystemTreePath as FilesystemKnowledgePath, TreePath as KnowledgePath
from propstore.sidecar.schema import SCHEMA_VERSION, SIDECAR_META_KEY
from propstore.sidecar.sqlite import connect_sidecar

if TYPE_CHECKING:
    from propstore.repository import Repository
    from propstore.world.bound import BoundWorld
    from propstore.context_lifting import LiftingSystem
from propstore.world.resolution import resolve
from propstore.world.types import (
    WorldStore,
    Environment,
    ChainResult,
    ChainStep,
    DerivedResult,
    RenderPolicy,
    ResolutionStrategy,
    ValueResult,
    ValueStatus,
)
from propstore.z3_conditions import Z3ConditionSolver


_KIND_TYPE_MAP = {
    "category": KindType.CATEGORY,
    "boolean": KindType.BOOLEAN,
    "structural": KindType.STRUCTURAL,
    "quantity": KindType.QUANTITY,
    "timepoint": KindType.TIMEPOINT,
}

_REQUIRED_SCHEMA: dict[str, set[str]] = {
    "source": {
        "slug",
        "source_id",
        "kind",
        "origin_type",
        "origin_value",
        "origin_retrieved",
        "origin_content_ref",
        "prior_base_rate",
        "quality_json",
        "derived_from_json",
    },
    "concept": {
        "id",
        "canonical_name",
        "kind_type",
        "form",
        "form_parameters",
        "primary_logical_id",
        "logical_ids_json",
    },
    "alias": {"concept_id", "alias_name"},
    "parameterization": {"output_concept_id"},
    "parameterization_group": {"group_id", "concept_id"},
    "relation_edge": {
        "source_kind",
        "source_id",
        "relation_type",
        "target_kind",
        "target_id",
        "target_justification_id",
        "strength",
        "conditions_differ",
        "note",
        "resolution_method",
        "resolution_model",
        "embedding_model",
        "embedding_distance",
        "pass_number",
        "confidence",
        "opinion_belief",
        "opinion_disbelief",
        "opinion_uncertainty",
        "opinion_base_rate",
    },
    "form": {"name", "dimensions", "is_dimensionless"},
    "form_algebra": {"output_form", "input_forms"},
    "concept_fts": {"concept_id"},
    "context": {"id", "name", "description", "parameters_json", "perspective"},
    "context_assumption": {"context_id", "assumption_cel", "seq"},
    "context_lifting_rule": {
        "id",
        "source_context_id",
        "target_context_id",
        "conditions_cel",
        "mode",
        "justification",
    },
    "claim_core": {
        "id",
        "primary_logical_id",
        "logical_ids_json",
        "version_id",
        "content_hash",
        "seq",
        "type",
        "target_concept",
        "source_slug",
        "source_paper",
        "provenance_page",
        "provenance_json",
        "context_id",
        "premise_kind",
        "branch",
    },
    "claim_concept_link": {
        "claim_id",
        "concept_id",
        "role",
        "ordinal",
        "binding_name",
    },
    "claim_numeric_payload": {
        "claim_id",
        "value",
        "lower_bound",
        "upper_bound",
        "uncertainty",
        "uncertainty_type",
        "sample_size",
        "unit",
        "value_si",
        "lower_bound_si",
        "upper_bound_si",
    },
    "claim_text_payload": {
        "claim_id",
        "conditions_cel",
        "statement",
        "expression",
        "sympy_generated",
        "sympy_error",
        "name",
        "measure",
        "listener_population",
        "methodology",
        "notes",
        "description",
        "auto_summary",
    },
    "claim_algorithm_payload": {
        "claim_id",
        "body",
        "canonical_ast",
        "variables_json",
        "algorithm_stage",
    },
    "conflict_witness": {
        "concept_id",
        "claim_a_id",
        "claim_b_id",
        "warning_class",
        "conditions_a",
        "conditions_b",
        "value_a",
        "value_b",
        "derivation_chain",
    },
}


class WorldModel(WorldStore):
    """Read-only reasoner over a compiled sidecar."""

    @classmethod
    def from_path(cls, knowledge_dir: str | Path) -> WorldModel:
        """Open a world model from a knowledge directory path."""
        sidecar = Path(knowledge_dir) / "sidecar" / "propstore.sqlite"
        return cls(sidecar_path=sidecar)

    def __init__(
        self,
        repo: Repository | None = None,
        *,
        sidecar_path: Path | None = None,
    ) -> None:
        if sidecar_path is not None:
            resolved = sidecar_path
        elif repo is not None:
            resolved = repo.sidecar_path
        else:
            raise TypeError(
                "WorldModel requires either sidecar_path or repo argument"
            )
        if not resolved.exists():
            raise FileNotFoundError(
                f"Sidecar not found at {resolved}. Run 'pks build' first."
            )
        self._conn = connect_sidecar(resolved)
        self._conn.row_factory = sqlite3.Row
        knowledge_root = FilesystemKnowledgePath.from_filesystem_path(
            resolved.parent.parent
        )
        if repo is not None and hasattr(repo, "tree"):
            knowledge_root = repo.tree()
        self._repo = repo
        self._knowledge_root = knowledge_root
        self._grounding_bundle_cache = None
        self._solver: Z3ConditionSolver | None = None
        self._registry: dict[str, ConceptInfo] | None = None
        self._lifting_system: LiftingSystem | None = None
        self._lifting_system_loaded = False
        self._table_cache: dict[str, bool] = {}
        self._compiled_graph_cache = None
        self._active_graph_cache: dict[str, Any] = {}
        self._claim_logical_id_index: dict[str, str] | None = None
        self._concept_logical_id_index: dict[str, str] | None = None
        self._validate_schema()

    def __enter__(self) -> WorldModel:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._compiled_graph_cache = None
        self._active_graph_cache.clear()
        self._grounding_bundle_cache = None
        self._conn.close()

    def grounding_bundle(self):
        """Return the grounded-rule bundle materialized in this sidecar."""

        if self._grounding_bundle_cache is None:
            from propstore.sidecar.rules import read_grounded_bundle

            self._grounding_bundle_cache = read_grounded_bundle(self._conn)
        return self._grounding_bundle_cache

    def _validate_schema(self) -> None:
        if not self._has_table("meta"):
            raise ValueError(
                "Unsupported sidecar schema: missing table(s) meta. "
                "Rebuild with 'pks build'."
            )
        meta_row = self._conn.execute(
            "SELECT schema_version FROM meta WHERE key = ?",
            (SIDECAR_META_KEY,),
        ).fetchone()
        if meta_row is None:
            raise ValueError(
                "Unsupported sidecar schema: missing metadata row for sidecar. "
                "Rebuild with 'pks build'."
            )
        actual_version = meta_row["schema_version"]
        if actual_version != SCHEMA_VERSION:
            raise ValueError(
                "Unsupported sidecar schema version: "
                f"expected {SCHEMA_VERSION}, found {actual_version}. "
                "Rebuild with 'pks build'."
            )

        missing_tables = sorted(
            table for table in _REQUIRED_SCHEMA if not self._has_table(table)
        )
        if missing_tables:
            missing = ", ".join(missing_tables)
            raise ValueError(
                "Unsupported sidecar schema: missing table(s) "
                f"{missing}. Rebuild with 'pks build'."
            )

        missing_columns: list[str] = []
        for table, required_columns in _REQUIRED_SCHEMA.items():
            columns = self._table_columns(table)
            absent = sorted(required_columns - columns)
            missing_columns.extend(f"{table}.{column}" for column in absent)
        if missing_columns:
            missing = ", ".join(missing_columns)
            raise ValueError(
                "Unsupported sidecar schema: missing column(s) "
                f"{missing}. Rebuild with 'pks build'."
            )

    def _table_columns(self, table: str) -> set[str]:
        rows = self._conn.execute(f"PRAGMA table_info({table})").fetchall()  # noqa: S608
        return {str(row["name"]) for row in rows}

    # ── Lazy Z3 setup ────────────────────────────────────────────────

    def _ensure_solver(self) -> Z3ConditionSolver:
        if self._solver is not None:
            return self._solver
        registry = self._build_registry()
        self._solver = Z3ConditionSolver(registry)
        return self._solver

    def _build_registry(self) -> dict[str, ConceptInfo]:
        if self._registry is not None:
            return self._registry
        rows = self._conn.execute(
            "SELECT id, canonical_name, kind_type, form_parameters FROM concept"
        ).fetchall()
        normalized_rows = [
            ConceptRow.from_mapping(
                {
                    "id": row["id"],
                    "canonical_name": row["canonical_name"],
                    "kind_type": row["kind_type"],
                    "form_parameters": row["form_parameters"],
                }
            )
            for row in rows
        ]
        registry = with_standard_synthetic_bindings(
            build_store_cel_registry(normalized_rows)
        )
        self._registry = registry
        return registry

    def condition_solver(self) -> Z3ConditionSolver:
        return self._ensure_solver()

    def _load_lifting_system(self) -> LiftingSystem | None:
        if self._lifting_system_loaded:
            return self._lifting_system
        self._lifting_system_loaded = True

        from propstore.context_lifting import (
            LiftingMode,
            LiftingRule,
            LiftingSystem,
        )

        rows = self._conn.execute(
            "SELECT id FROM context ORDER BY id"
        ).fetchall()
        if not rows:
            self._lifting_system = None
            return None

        context_ids = [str(row["id"]) for row in rows]
        context_refs = tuple(
            ContextReference(id=to_context_id(context_id))
            for context_id in context_ids
        )

        assumption_rows = self._conn.execute(
            "SELECT context_id, assumption_cel FROM context_assumption "
            "ORDER BY context_id, seq"
        ).fetchall()
        assumptions_by_id: dict[str, list[str]] = {
            context_id: [] for context_id in context_ids
        }
        for row in assumption_rows:
            context_id = row["context_id"]
            if context_id not in assumptions_by_id:
                continue
            assumptions_by_id[context_id].append(row["assumption_cel"])

        lifting_rows = self._conn.execute(
            """
            SELECT id, source_context_id, target_context_id,
                   conditions_cel, mode, justification
            FROM context_lifting_rule
            ORDER BY id
            """
        ).fetchall()
        lifting_rules: list[LiftingRule] = []
        for row in lifting_rows:
            raw_conditions = row["conditions_cel"]
            if raw_conditions:
                conditions = tuple(str(item) for item in json.loads(raw_conditions))
            else:
                conditions = ()
            lifting_rules.append(
                LiftingRule(
                    id=row["id"],
                    source=ContextReference(id=to_context_id(row["source_context_id"])),
                    target=ContextReference(id=to_context_id(row["target_context_id"])),
                    conditions=to_cel_exprs(conditions),
                    mode=LiftingMode(row["mode"]),
                    justification=row["justification"],
                )
            )

        self._lifting_system = LiftingSystem(
            contexts=context_refs,
            lifting_rules=tuple(lifting_rules),
            context_assumptions={
                to_context_id(context_id): to_cel_exprs(assumptions)
                for context_id, assumptions in assumptions_by_id.items()
            },
        )
        return self._lifting_system

    # ── Unbound queries ──────────────────────────────────────────────

    def _claim_select_sql(self) -> str:
        return """
            SELECT
                core.id,
                core.id AS artifact_id,
                core.primary_logical_id,
                core.logical_ids_json,
                core.version_id,
                core.seq,
                core.type,
                num.value,
                num.lower_bound,
                num.upper_bound,
                num.uncertainty,
                num.uncertainty_type,
                num.sample_size,
                num.unit,
                txt.conditions_cel,
                txt.statement,
                txt.expression,
                txt.sympy_generated,
                txt.sympy_error,
                txt.name,
                core.target_concept,
                txt.measure,
                txt.listener_population,
                txt.methodology,
                txt.notes,
                txt.description,
                txt.auto_summary,
                alg.body,
                alg.canonical_ast,
                alg.variables_json,
                alg.algorithm_stage,
                core.source_slug,
                core.source_paper,
                src.source_id AS source_id,
                src.kind AS source_kind,
                src.origin_type AS source_origin_type,
                src.origin_value AS source_origin_value,
                src.origin_retrieved AS source_origin_retrieved,
                src.origin_content_ref AS source_origin_content_ref,
                src.prior_base_rate AS source_prior_base_rate,
                src.quality_json AS source_quality_json,
                src.derived_from_json AS source_derived_from_json,
                core.provenance_page,
                core.provenance_json,
                num.value_si,
                num.lower_bound_si,
                num.upper_bound_si,
                core.context_id,
                core.branch,
                core.build_status,
                core.stage,
                core.promotion_status
            FROM claim_core AS core
            LEFT JOIN claim_numeric_payload AS num ON num.claim_id = core.id
            LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
            LEFT JOIN claim_algorithm_payload AS alg ON alg.claim_id = core.id
            LEFT JOIN source AS src ON src.slug = core.source_slug
        """

    def _claim_rows(self, where_sql: str = "", params: tuple[Any, ...] = ()) -> list[ClaimRow]:
        rows = self._conn.execute(
            f"{self._claim_select_sql()} {where_sql}",
            params,
        ).fetchall()
        row_dicts = [dict(row) for row in rows]
        if not row_dicts:
            return []
        claim_ids = [
            str(row_dict["id"])
            for row_dict in row_dicts
            if isinstance(row_dict.get("id"), str)
        ]
        links_by_claim_id: dict[str, list[dict[str, Any]]] = {claim_id: [] for claim_id in claim_ids}
        placeholders = ",".join("?" for _ in claim_ids)
        link_rows = self._conn.execute(
            f"""
            SELECT claim_id, concept_id, role, ordinal, binding_name
            FROM claim_concept_link
            WHERE claim_id IN ({placeholders})
            ORDER BY claim_id, ordinal, concept_id
            """,  # noqa: S608
            tuple(claim_ids),
        ).fetchall()
        for link_row in link_rows:
            links_by_claim_id.setdefault(str(link_row["claim_id"]), []).append(dict(link_row))
        for row_dict in row_dicts:
            row_dict["concept_links"] = links_by_claim_id.get(str(row_dict["id"]), [])
        return [ClaimRow.from_mapping(row_dict) for row_dict in row_dicts]

    def get_concept(self, concept_id: str) -> ConceptRow | None:
        row = self._conn.execute("SELECT * FROM concept WHERE id = ?", (concept_id,)).fetchone()
        if row is None:
            resolved = self.resolve_concept(concept_id)
            if resolved is None or resolved == concept_id:
                return None
            row = self._conn.execute("SELECT * FROM concept WHERE id = ?", (resolved,)).fetchone()
        if row is None:
            return None
        data = dict(row)
        logical_ids_json = data.get("logical_ids_json")
        if isinstance(logical_ids_json, str) and logical_ids_json:
            try:
                data["logical_ids"] = json.loads(logical_ids_json)
            except json.JSONDecodeError:
                data["logical_ids"] = []
        else:
            data["logical_ids"] = []
        data["logical_id"] = data.get("primary_logical_id")
        return ConceptRow.from_mapping(data)

    def concept_name(self, concept_id: str) -> str | None:
        """Return the canonical name for a concept, or None if not found."""
        concept = self.get_concept(concept_id)
        return concept.canonical_name if concept else None

    def concept_names(self) -> dict[str, str]:
        """Return ``{concept_id: canonical_name}`` for all concepts."""
        return {
            str(concept.concept_id): concept.canonical_name
            for concept in self.all_concepts()
        }

    def get_claim(self, claim_id: str) -> ClaimRow | None:
        resolved_claim_id = self.resolve_claim(claim_id) or claim_id
        rows = self._claim_rows("WHERE core.id = ?", (resolved_claim_id,))
        return rows[0] if rows else None

    def _build_logical_id_index(self, table: str) -> dict[str, str]:
        """Return a ``name → artifact_id`` map for one of ``claim_core``/``concept``.

        Both composite ``"namespace:value"`` keys AND bare ``"value"``
        keys populate the same map so the cache covers every form the
        pre-memoized fallback already supported. A single SELECT +
        Python pass replaces per-miss full-table scans. WorldModel is
        immutable per open sidecar (all rows live under a read-only
        connection, cleared only by ``close()``), so the index is safe
        to build once and reuse for the lifetime of the instance.
        """

        if table not in ("claim_core", "concept"):
            raise ValueError(f"unsupported logical-id table: {table}")
        index: dict[str, str] = {}
        rows = self._conn.execute(
            f"SELECT id, primary_logical_id, logical_ids_json FROM {table}"  # noqa: S608
        ).fetchall()
        for row in rows:
            artifact_id = row["id"]
            primary_logical_id = row["primary_logical_id"]
            if isinstance(primary_logical_id, str) and primary_logical_id:
                index.setdefault(primary_logical_id, artifact_id)
            logical_ids_json = row["logical_ids_json"]
            if not isinstance(logical_ids_json, str) or not logical_ids_json:
                continue
            try:
                logical_ids = json.loads(logical_ids_json)
            except json.JSONDecodeError:
                continue
            if not isinstance(logical_ids, list):
                continue
            for entry in logical_ids:
                if not isinstance(entry, dict):
                    continue
                namespace = entry.get("namespace")
                value = entry.get("value")
                if isinstance(namespace, str) and isinstance(value, str):
                    index.setdefault(f"{namespace}:{value}", artifact_id)
                    index.setdefault(value, artifact_id)
        return index

    def _get_claim_logical_id_index(self) -> dict[str, str]:
        if self._claim_logical_id_index is None:
            self._claim_logical_id_index = self._build_logical_id_index(
                "claim_core"
            )
        return self._claim_logical_id_index

    def _get_concept_logical_id_index(self) -> dict[str, str]:
        if self._concept_logical_id_index is None:
            self._concept_logical_id_index = self._build_logical_id_index(
                "concept"
            )
        return self._concept_logical_id_index

    def resolve_claim(self, name: str) -> str | None:
        """Resolve a claim by artifact ID or logical ID."""
        row = self._conn.execute(
            "SELECT id FROM claim_core WHERE id = ?",
            (name,),
        ).fetchone()
        if row is not None:
            return row["id"]

        row = self._conn.execute(
            "SELECT id FROM claim_core WHERE primary_logical_id = ?",
            (name,),
        ).fetchone()
        if row is not None:
            return row["id"]

        return self._get_claim_logical_id_index().get(name)

    def resolve_alias(self, alias: str) -> str | None:
        row = self._conn.execute(
            "SELECT concept_id FROM alias WHERE alias_name = ?", (alias,)
        ).fetchone()
        return row["concept_id"] if row else None

    def resolve_concept(self, name: str) -> str | None:
        """Resolve a concept by alias, artifact ID, logical ID, or canonical name."""
        resolved = self.resolve_alias(name)
        if resolved:
            return resolved

        row = self._conn.execute(
            "SELECT id FROM concept WHERE id = ?",
            (name,),
        ).fetchone()
        if row is not None:
            return row["id"]

        row = self._conn.execute(
            "SELECT id FROM concept WHERE primary_logical_id = ?",
            (name,),
        ).fetchone()
        if row is not None:
            return row["id"]

        cached = self._get_concept_logical_id_index().get(name)
        if cached is not None:
            return cached

        row = self._conn.execute(
            "SELECT id FROM concept WHERE canonical_name = ?",
            (name,),
        ).fetchone()
        return row["id"] if row else None

    def claims_for(self, concept_id: str | None) -> list[ClaimRow]:
        where_sql, params = self._claims_linked_to_concept_where_sql(
            concept_id,
            roles=("output", "target"),
        )
        return self._claim_rows(where_sql + "ORDER BY core.id", params)

    def claims_related_to_concept(self, concept_id: str | None) -> list[ClaimRow]:
        where_sql, params = self._claims_linked_to_concept_where_sql(concept_id)
        return self._claim_rows(where_sql + "ORDER BY core.id", params)

    def _claims_linked_to_concept_where_sql(
        self,
        concept_id: str | None,
        *,
        roles: tuple[str, ...] | None = None,
    ) -> tuple[str, tuple[Any, ...]]:
        if concept_id is None:
            return "", ()
        resolved_concept_id = self.resolve_concept(concept_id) or concept_id
        predicates = [
            "link.claim_id = core.id",
            "link.concept_id = ?",
        ]
        params: list[Any] = [resolved_concept_id]
        if roles:
            placeholders = ",".join("?" for _ in roles)
            predicates.append(f"link.role IN ({placeholders})")
            params.extend(roles)
        where_sql = (
            "WHERE EXISTS ("
            "SELECT 1 FROM claim_concept_link AS link "
            f"WHERE {' AND '.join(predicates)}"
            ") "
        )
        return where_sql, tuple(params)

    def _render_policy_predicates(
        self, policy: RenderPolicy
    ) -> tuple[list[str], tuple[Any, ...]]:
        """Translate a ``RenderPolicy`` into SQL ``WHERE`` predicates on
        ``claim_core``'s lifecycle columns.

        Per axis-1 findings 3.1 / 3.2 / 3.3 (closed in
        ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``):

        - ``stage = 'draft'`` rows are hidden unless ``include_drafts=True``.
        - ``build_status = 'blocked'`` rows are hidden unless
          ``include_blocked=True`` (raw-id quarantine, Phase 3 Gate 1).
        - ``promotion_status = 'blocked'`` rows are hidden unless
          ``include_blocked=True`` (partial-promote mirror, Phase 3 Gate 3).

        A policy with all three flags at their default ``False`` produces
        three predicates that together preserve the "don't show problems
        by default" posture required by the CLAUDE.md design checklist.
        """
        predicates: list[str] = []
        params: list[Any] = []
        if not policy.include_drafts:
            predicates.append("(core.stage IS NULL OR core.stage != 'draft')")
        if not policy.include_blocked:
            predicates.append(
                "(core.build_status IS NULL OR core.build_status != 'blocked')"
            )
            predicates.append(
                "(core.promotion_status IS NULL "
                "OR core.promotion_status != 'blocked')"
            )
        return predicates, tuple(params)

    def claims_with_policy(
        self,
        concept_id: str | None,
        policy: RenderPolicy,
    ) -> list[ClaimRow]:
        """Return claim rows filtered by the lifecycle visibility flags
        on ``policy``.

        Implements the render-time contract described in
        ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
        (axis-1 findings 3.1 / 3.2 / 3.3): the source-of-truth sidecar
        holds every row, and the render layer picks what to show based
        on explicit user policy. Default policy preserves the
        pre-render-gate-removal visibility — drafts and blocked rows
        stay out of the default view but remain queryable through opt-in
        flags.
        """
        predicates, params = self._render_policy_predicates(policy)
        clauses: list[str] = []
        bound: list[Any] = list(params)
        if concept_id is not None:
            concept_clause, concept_params = self._claims_linked_to_concept_where_sql(concept_id)
            clauses.append(concept_clause.removeprefix("WHERE ").strip())
            bound.extend(concept_params)
        clauses.extend(predicates)
        where_sql = ""
        if clauses:
            where_sql = "WHERE " + " AND ".join(clauses) + " "
        return self._claim_rows(where_sql + "ORDER BY core.id", tuple(bound))

    def build_diagnostics(self, policy: RenderPolicy) -> list[dict[str, Any]]:
        """Return ``build_diagnostics`` rows when ``policy.show_quarantined``
        is ``True``; an empty list otherwise.

        Per axis-1 findings 3.1 / 3.2 / 3.3: the ``build_diagnostics``
        table is the quarantine surface for rows the sidecar accepted
        but flagged as problematic. The render layer surfaces these rows
        only under explicit opt-in, preserving the
        ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
        exit-criterion that "the default view matches pre-fix behaviour
        for clean trees."
        """
        if not policy.show_quarantined:
            return []
        if not self._has_table("build_diagnostics"):
            return []
        rows = self._conn.execute(
            """
            SELECT
                id, claim_id, source_kind, source_ref,
                diagnostic_kind, severity, blocking,
                message, file, detail_json
            FROM build_diagnostics
            ORDER BY id
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, ClaimRow]:
        if not claim_ids:
            return {}
        resolved_ids = {
            self.resolve_claim(claim_id) or claim_id
            for claim_id in claim_ids
        }
        placeholders = ",".join("?" for _ in resolved_ids)
        rows = self._claim_rows(
            f"WHERE core.id IN ({placeholders})",  # noqa: S608
            tuple(resolved_ids),
        )
        return {str(row.claim_id): row for row in rows}

    def stances_between(self, claim_ids: set[str]) -> list[StanceRow]:
        if not claim_ids:
            return []
        resolved_ids = {
            self.resolve_claim(claim_id) or claim_id
            for claim_id in claim_ids
        }
        placeholders = ",".join("?" for _ in resolved_ids)
        rows = self._conn.execute(
            f"""
            SELECT
                source_id AS claim_id,
                target_id AS target_claim_id,
                relation_type AS stance_type,
                target_justification_id,
                strength,
                conditions_differ,
                note,
                resolution_method,
                resolution_model,
                embedding_model,
                embedding_distance,
                pass_number,
                confidence,
                opinion_belief,
                opinion_disbelief,
                opinion_uncertainty,
                opinion_base_rate
            FROM relation_edge
            WHERE source_kind = 'claim'
              AND target_kind = 'claim'
              AND source_id IN ({placeholders})
              AND target_id IN ({placeholders})
            """,  # noqa: S608
            list(resolved_ids) + list(resolved_ids),
        ).fetchall()
        return [StanceRow.from_mapping(dict(row)) for row in rows]

    def conflicts(self, concept_id: str | None = None) -> list[ConflictRow]:
        if concept_id is not None:
            rows = self._conn.execute(
                """
                SELECT concept_id, claim_a_id, claim_b_id, warning_class,
                       conditions_a, conditions_b, value_a, value_b, derivation_chain
                FROM conflict_witness WHERE concept_id = ?
                """,
                (concept_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT concept_id, claim_a_id, claim_b_id, warning_class,
                       conditions_a, conditions_b, value_a, value_b, derivation_chain
                FROM conflict_witness
                """
            ).fetchall()
        return [ConflictRow.from_mapping(dict(row)) for row in rows]

    def all_concepts(self) -> list[ConceptRow]:
        rows = self._conn.execute("SELECT * FROM concept").fetchall()
        return [ConceptRow.from_mapping(dict(row)) for row in rows]

    def all_parameterizations(self) -> list[ParameterizationRow]:
        rows = self._conn.execute("SELECT * FROM parameterization").fetchall()
        return [ParameterizationRow.from_mapping(dict(row)) for row in rows]

    def all_relationships(self) -> list[RelationshipRow]:
        rows = self._conn.execute(
            """
            SELECT source_id, relation_type AS type, target_id, conditions_cel, note
            FROM relation_edge
            WHERE source_kind = 'concept' AND target_kind = 'concept'
            """
        ).fetchall()
        return [RelationshipRow.from_mapping(dict(row)) for row in rows]

    def all_claim_stances(self) -> list[StanceRow]:
        rows = self._conn.execute(
            """
            SELECT
                source_id AS claim_id,
                target_id AS target_claim_id,
                relation_type AS stance_type,
                target_justification_id,
                strength,
                conditions_differ,
                note,
                resolution_method,
                resolution_model,
                embedding_model,
                embedding_distance,
                pass_number,
                confidence,
                opinion_belief,
                opinion_disbelief,
                opinion_uncertainty,
                opinion_base_rate
            FROM relation_edge
            WHERE source_kind = 'claim' AND target_kind = 'claim'
            """
        ).fetchall()
        return [StanceRow.from_mapping(dict(row)) for row in rows]

    def all_micropublications(self) -> list[ActiveMicropublication]:
        if not self._has_table("micropublication"):
            return []
        rows = self._conn.execute(
            """
            SELECT
                mp.id AS artifact_id,
                mp.context_id,
                mp.assumptions_json,
                mp.stance,
                mp.source_slug,
                (
                    SELECT json_group_array(mc.claim_id)
                    FROM micropublication_claim mc
                    WHERE mc.micropublication_id = mp.id
                    ORDER BY mc.seq
                ) AS claim_ids
            FROM micropublication mp
            ORDER BY mp.id
            """
        ).fetchall()
        return [
            ActiveMicropublication.from_mapping(
                {
                    "artifact_id": row["artifact_id"],
                    "context_id": row["context_id"],
                    "claim_ids": row["claim_ids"],
                    "assumptions": row["assumptions_json"],
                    "stance": row["stance"],
                    "source": row["source_slug"],
                }
            )
            for row in rows
        ]

    def concept_ids_for_group(self, group_id: int) -> set[str]:
        rows = self._conn.execute(
            "SELECT concept_id FROM parameterization_group WHERE group_id = ?",
            (group_id,),
        ).fetchall()
        return {row["concept_id"] for row in rows}

    def search(self, query: str) -> list[ConceptSearchHit]:
        rows = self._conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH ?",
            (query,),
        ).fetchall()
        return [ConceptSearchHit.from_mapping(dict(row)) for row in rows]

    def similar_claims(
        self,
        claim_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[ClaimSimilarityHit]:
        """Find claims similar to the given claim by embedding distance.

        Requires sqlite-vec extension and pre-computed embeddings.
        """
        from propstore.embed import find_similar, _load_vec_extension, get_registered_models
        _load_vec_extension(self._conn)

        if model_name is None:
            models = get_registered_models(self._conn)
            if not models:
                return []
            model_name = models[0]["model_name"]

        assert model_name is not None  # narrowed above
        return [
            ClaimSimilarityHit.from_mapping(result)
            for result in find_similar(self._conn, claim_id, model_name, top_k=top_k)
        ]

    def similar_concepts(
        self,
        concept_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[ConceptSimilarityHit]:
        """Find concepts similar to the given concept by embedding distance.

        Requires sqlite-vec extension and pre-computed embeddings.
        """
        from propstore.embed import find_similar_concepts, _load_vec_extension, get_registered_models
        _load_vec_extension(self._conn)

        if model_name is None:
            models = get_registered_models(self._conn)
            if not models:
                return []
            model_name = models[0]["model_name"]

        assert model_name is not None  # narrowed above
        return [
            ConceptSimilarityHit.from_mapping(result)
            for result in find_similar_concepts(self._conn, concept_id, model_name, top_k=top_k)
        ]

    def _has_table(self, name: str) -> bool:
        if name in self._table_cache:
            return self._table_cache[name]
        row = self._conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        result = row is not None
        self._table_cache[name] = result
        return result

    def has_table(self, name: str) -> bool:
        return self._has_table(name)

    # ── Form algebra queries ────────────────────────────────────────

    def forms_by_dimensions(self, dims: dict[str, int]) -> list[dict]:
        """Find all forms with matching SI dimensions."""
        from bridgman import dims_equal
        rows = self._conn.execute("SELECT * FROM form").fetchall()
        results = []
        for row in rows:
            row_dims_json = row["dimensions"]
            if row_dims_json is None:
                row_dims: dict[str, int] = {}
                if not row["is_dimensionless"]:
                    continue  # No dimensions and not dimensionless — skip
            else:
                row_dims = json.loads(row_dims_json)
            if dims_equal(row_dims, dims):
                results.append(dict(row))
        return results

    def form_algebra_for(self, form_name: str) -> list[dict]:
        """Get all algebra decompositions that produce *form_name*."""
        rows = self._conn.execute(
            "SELECT * FROM form_algebra WHERE output_form = ?", (form_name,)
        ).fetchall()
        return [dict(r) for r in rows]

    def form_algebra_using(self, form_name: str) -> list[dict]:
        """Get all algebra entries where *form_name* is an input."""
        rows = self._conn.execute("SELECT * FROM form_algebra").fetchall()
        results = []
        for row in rows:
            input_forms = json.loads(row["input_forms"])
            if form_name in input_forms:
                results.append(dict(row))
        return results

    def stats(self) -> WorldStoreStats:
        concepts = self._conn.execute("SELECT COUNT(*) FROM concept").fetchone()[0]
        claims = self._conn.execute("SELECT COUNT(*) FROM claim_core").fetchone()[0]
        conflicts = self._conn.execute("SELECT COUNT(*) FROM conflict_witness").fetchone()[0]
        return WorldStoreStats(
            concepts=int(concepts),
            claims=int(claims),
            conflicts=int(conflicts),
        )

    # ── Parameterization queries ─────────────────────────────────────

    def _parameterizations_for(self, concept_id: str) -> list[ParameterizationRow]:
        """Get parameterization rows where output_concept_id matches."""
        resolved_concept_id = self.resolve_concept(concept_id) or concept_id
        rows = self._conn.execute(
            "SELECT * FROM parameterization WHERE output_concept_id = ?",
            (resolved_concept_id,),
        ).fetchall()
        return [
            ParameterizationRow.from_mapping(
                dict(row),
                output_concept_id=resolved_concept_id,
            )
            for row in rows
        ]

    def parameterizations_for(self, concept_id: str) -> list[ParameterizationRow]:
        return self._parameterizations_for(concept_id)

    def compiled_graph(self):
        """Build the canonical compiled semantic graph from the current sidecar."""
        from propstore.core.graph_types import CompiledWorldGraph
        from propstore.core.graph_build import build_compiled_world_graph

        if self._compiled_graph_cache is None:
            self._compiled_graph_cache = build_compiled_world_graph(
                self,
                prefer_logical_claim_ids=False,
            )
        return CompiledWorldGraph.from_dict(self._compiled_graph_cache.to_dict())

    def active_graph(
        self,
        environment: Environment,
        *,
        lifting_system: LiftingSystem | None = None,
    ):
        from propstore.core.activation import activate_compiled_world_graph
        from propstore.core.graph_types import ActiveWorldGraph

        resolved_lifting_system = lifting_system or self._load_lifting_system()
        cache_key = json.dumps(environment.to_dict(), sort_keys=True)
        if cache_key not in self._active_graph_cache:
            self._active_graph_cache[cache_key] = activate_compiled_world_graph(
                self.compiled_graph(),
                environment=environment,
                solver=self.condition_solver(),
                lifting_system=resolved_lifting_system,
            )
        cached = self._active_graph_cache[cache_key]
        return ActiveWorldGraph.from_dict(cached.to_dict())

    def _group_members(self, concept_id: str) -> list[str]:
        """Get all concept_ids in the same parameterization group."""
        resolved_concept_id = self.resolve_concept(concept_id) or concept_id
        row = self._conn.execute(
            "SELECT group_id FROM parameterization_group WHERE concept_id = ?",
            (resolved_concept_id,),
        ).fetchone()
        if row is None:
            return []
        rows = self._conn.execute(
            "SELECT concept_id FROM parameterization_group WHERE group_id = ?",
            (row["group_id"],),
        ).fetchall()
        return [r["concept_id"] for r in rows]

    def group_members(self, concept_id: str) -> list[str]:
        return self._group_members(concept_id)

    # ── Stance graph ─────────────────────────────────────────────────

    def explain(self, claim_id: str) -> list[StanceRow]:
        """Walk normalized claim relation edges breadth-first from claim_id."""
        result: list[StanceRow] = []
        visited: set[str] = set()
        queue: deque[str] = deque([claim_id])
        visited.add(claim_id)

        while queue:
            current = queue.popleft()
            rows = self._conn.execute(
                """
                SELECT
                    source_id AS claim_id,
                    target_id AS target_claim_id,
                    relation_type AS stance_type,
                    target_justification_id,
                    strength,
                    conditions_differ,
                    note,
                    resolution_method,
                    resolution_model,
                    embedding_model,
                    embedding_distance,
                    pass_number,
                    confidence,
                    opinion_belief,
                    opinion_disbelief,
                    opinion_uncertainty,
                    opinion_base_rate
                FROM relation_edge
                WHERE source_kind = 'claim' AND target_kind = 'claim' AND source_id = ?
                """,
                (current,),
            ).fetchall()
            for row in rows:
                stance = StanceRow.from_mapping(dict(row))
                result.append(stance)
                target = str(stance.target_claim_id)
                if target not in visited:
                    visited.add(target)
                    queue.append(target)

        return result

    # ── Condition binding ────────────────────────────────────────────

    def bind(
        self,
        environment: Environment | None = None,
        *,
        policy: RenderPolicy | None = None,
        **conditions: Any,
    ) -> BoundWorld:
        from propstore.world.bound import BoundWorld

        if environment is None:
            environment = Environment(bindings=conditions)
        else:
            merged = dict(environment.bindings)
            if conditions:
                merged.update(conditions)
            environment = Environment(
                bindings=merged,
                context_id=environment.context_id,
                effective_assumptions=tuple(environment.effective_assumptions),
                assumptions=tuple(environment.assumptions),
            )

        lifting_system = self._load_lifting_system()
        if environment.context_id is not None and lifting_system is not None:
            environment = Environment(
                bindings=environment.bindings,
                context_id=environment.context_id,
                effective_assumptions=tuple(
                    lifting_system.effective_assumptions(environment.context_id)
                ),
                assumptions=tuple(environment.assumptions),
            )

        environment = Environment(
            bindings=environment.bindings,
            context_id=environment.context_id,
            effective_assumptions=tuple(environment.effective_assumptions),
            assumptions=compile_environment_assumptions(
                bindings=environment.bindings,
                effective_assumptions=environment.effective_assumptions,
                context_id=environment.context_id,
            ),
        )

        return BoundWorld(
            self,
            environment=environment,
            lifting_system=lifting_system,
            policy=policy,
            active_graph=self.active_graph(
                environment,
                lifting_system=lifting_system,
            ),
        )

    # ── Chain query ──────────────────────────────────────────────────

    def chain_query(
        self,
        target_concept_id: str,
        strategy: ResolutionStrategy | None = None,
        **bindings: Any,
    ) -> ChainResult:
        """Traverse the parameter space to derive the target concept."""
        policy = RenderPolicy(strategy=strategy) if strategy is not None else None
        bound = self.bind(policy=policy, **bindings)
        steps: list[ChainStep] = []
        resolved_values: dict[str, float | str | None] = {}
        visited: set[str] = set()
        unresolved_conflicted: list[str] = []

        # Record initial bindings as steps
        for key, value in bindings.items():
            steps.append(ChainStep(concept_id=key, value=value, source="binding"))

        # Get parameterization group for target
        group = self._group_members(target_concept_id)
        if not group:
            group = [target_concept_id]

        # Iterative resolution: keep trying until no more progress
        changed = True
        while changed:
            changed = False
            for cid in group:
                if cid in visited:
                    continue

                # Try value_of first
                vr = bound.value_of(cid)
                if vr.status is ValueStatus.DETERMINED:
                    value = vr.claims[0].value if vr.claims else None
                    if value is not None:
                        resolved_values[cid] = value
                        steps.append(ChainStep(concept_id=cid, value=value, source="claim"))
                        visited.add(cid)
                        changed = True
                        continue

                # If conflicted and strategy given, try resolve
                if vr.status is ValueStatus.CONFLICTED and strategy is not None:
                    rr = bound.resolved_value(cid)
                    if rr.status is ValueStatus.RESOLVED and rr.value is not None:
                        resolved_values[cid] = rr.value
                        steps.append(ChainStep(concept_id=cid, value=rr.value, source="resolved"))
                        visited.add(cid)
                        changed = True
                        continue

                # Track conflicted concepts that could not be resolved
                if vr.status is ValueStatus.CONFLICTED and cid not in unresolved_conflicted:
                    unresolved_conflicted.append(cid)

                # Try derived_value
                dr = bound.derived_value(cid, override_values=resolved_values)
                if dr.status is ValueStatus.DERIVED and dr.value is not None:
                    resolved_values[cid] = dr.value
                    steps.append(ChainStep(concept_id=cid, value=dr.value, source="derived"))
                    visited.add(cid)
                    changed = True

        # Get the target's result
        if target_concept_id in resolved_values:
            # Find the step for the target to determine result type
            target_step = next(
                (s for s in steps if s.concept_id == target_concept_id), None
            )
            if target_step and target_step.source == "derived":
                dr = bound.derived_value(target_concept_id, override_values=resolved_values)
                result: ValueResult | DerivedResult = dr
            else:
                result = bound.value_of(target_concept_id)
        else:
            # Try one more time with all resolved values
            dr = bound.derived_value(target_concept_id, override_values=resolved_values)
            if dr.status is ValueStatus.DERIVED:
                result = dr
            else:
                result = bound.value_of(target_concept_id)

        return ChainResult(
            target_concept_id=to_concept_id(target_concept_id),
            result=result,
            steps=steps,
            bindings_used=bindings,
            unresolved_dependencies=[to_concept_id(concept_id) for concept_id in unresolved_conflicted],
        )
