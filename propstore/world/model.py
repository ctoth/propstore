"""WorldModel — read-only reasoner over a compiled sidecar."""

from __future__ import annotations

import json
import sqlite3
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, Any

from propstore.cel_checker import ConceptInfo, KindType
from propstore.core.id_types import to_concept_id
from propstore.world.labelled import compile_environment_assumptions

if TYPE_CHECKING:
    from propstore.cli.repository import Repository
    from propstore.world.bound import BoundWorld
    from propstore.validate_contexts import ContextHierarchy
from propstore.world.resolution import resolve
from propstore.world.types import (
    ArtifactStore,
    Environment,
    ChainResult,
    ChainStep,
    DerivedResult,
    RenderPolicy,
    ResolutionStrategy,
    ValueResult,
)
from propstore.z3_conditions import Z3ConditionSolver


_KIND_TYPE_MAP = {
    "category": KindType.CATEGORY,
    "boolean": KindType.BOOLEAN,
    "structural": KindType.STRUCTURAL,
    "quantity": KindType.QUANTITY,
}


class WorldModel(ArtifactStore):
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
        self._conn = sqlite3.connect(resolved)
        self._conn.row_factory = sqlite3.Row
        self._solver: Z3ConditionSolver | None = None
        self._registry: dict[str, ConceptInfo] | None = None
        self._context_hierarchy: ContextHierarchy | None = None
        self._context_hierarchy_loaded = False
        self._table_cache: dict[str, bool] = {}
        self._column_cache: dict[tuple[str, str], bool] = {}
        self._claim_has_target_concept: bool | None = None
        self._compiled_graph_cache = None
        self._active_graph_cache: dict[str, Any] = {}

    def __enter__(self) -> WorldModel:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._compiled_graph_cache = None
        self._active_graph_cache.clear()
        self._conn.close()

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
        registry: dict[str, ConceptInfo] = {}
        if not self._has_table("concept"):
            self._registry = registry
            return registry
        rows = self._conn.execute(
            "SELECT id, canonical_name, kind_type, form, form_parameters FROM concept"
        ).fetchall()
        for row in rows:
            canonical = row["canonical_name"]
            kind = _KIND_TYPE_MAP.get(row["kind_type"], KindType.QUANTITY)
            cat_values: list[str] = []
            cat_extensible = True
            fp = row["form_parameters"]
            if fp:
                params = json.loads(fp)
                if isinstance(params, dict):
                    cat_values = params.get("values", [])
                    cat_extensible = params.get("extensible", True)
            registry[canonical] = ConceptInfo(
                id=row["id"],
                canonical_name=canonical,
                kind=kind,
                category_values=cat_values,
                category_extensible=cat_extensible,
            )
        self._registry = registry
        return registry

    def condition_solver(self) -> Z3ConditionSolver:
        return self._ensure_solver()

    def _load_context_hierarchy(self) -> ContextHierarchy | None:
        if self._context_hierarchy_loaded:
            return self._context_hierarchy
        self._context_hierarchy_loaded = True

        required_tables = {"context", "context_assumption", "context_exclusion"}
        if not all(self._has_table(name) for name in required_tables):
            self._context_hierarchy = None
            return None

        from propstore.loaded import LoadedEntry
        from propstore.validate_contexts import ContextHierarchy

        rows = self._conn.execute(
            "SELECT id, name, description, inherits FROM context ORDER BY id"
        ).fetchall()
        if not rows:
            self._context_hierarchy = None
            return None

        contexts_by_id: dict[str, dict[str, Any]] = {}
        for row in rows:
            context_id = row["id"]
            contexts_by_id[context_id] = {
                "id": context_id,
                "name": row["name"],
                "description": row["description"],
                "inherits": row["inherits"],
                "assumptions": [],
                "excludes": [],
            }

        assumption_rows = self._conn.execute(
            "SELECT context_id, assumption_cel FROM context_assumption "
            "ORDER BY context_id, seq"
        ).fetchall()
        for row in assumption_rows:
            context = contexts_by_id.get(row["context_id"])
            if context is None:
                continue
            context["assumptions"].append(row["assumption_cel"])

        exclusion_rows = self._conn.execute(
            "SELECT context_a, context_b FROM context_exclusion ORDER BY context_a, context_b"
        ).fetchall()
        for row in exclusion_rows:
            context = contexts_by_id.get(row["context_a"])
            if context is None:
                continue
            exclusion = row["context_b"]
            if exclusion not in context["excludes"]:
                context["excludes"].append(exclusion)

        loaded_contexts = [
            LoadedEntry(filename=context_id, filepath=None, data=data)
            for context_id, data in contexts_by_id.items()
        ]
        self._context_hierarchy = ContextHierarchy(loaded_contexts)
        return self._context_hierarchy

    # ── Unbound queries ──────────────────────────────────────────────

    _CLAIM_SELECT_SQL = """
        SELECT
            core.id,
            core.content_hash,
            core.seq,
            core.type,
            core.concept_id,
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
            alg.stage,
            core.source_paper,
            core.provenance_page,
            core.provenance_json,
            num.value_si,
            num.lower_bound_si,
            num.upper_bound_si,
            core.context_id
        FROM claim_core AS core
        LEFT JOIN claim_numeric_payload AS num ON num.claim_id = core.id
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        LEFT JOIN claim_algorithm_payload AS alg ON alg.claim_id = core.id
    """

    def _claim_rows(self, where_sql: str = "", params: tuple[Any, ...] = ()) -> list[dict]:
        if not self._has_table("claim_core"):
            return []
        rows = self._conn.execute(
            f"{self._CLAIM_SELECT_SQL} {where_sql}",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def get_concept(self, concept_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM concept WHERE id = ?", (concept_id,)
        ).fetchone()
        return dict(row) if row else None

    def concept_name(self, concept_id: str) -> str | None:
        """Return the canonical name for a concept, or None if not found."""
        concept = self.get_concept(concept_id)
        return concept["canonical_name"] if concept else None

    def concept_names(self) -> dict[str, str]:
        """Return ``{concept_id: canonical_name}`` for all concepts."""
        return {c["id"]: c["canonical_name"] for c in self.all_concepts()}

    def get_claim(self, claim_id: str) -> dict | None:
        if not self._has_table("claim_core"):
            return None
        rows = self._claim_rows("WHERE core.id = ?", (claim_id,))
        return rows[0] if rows else None

    def resolve_alias(self, alias: str) -> str | None:
        row = self._conn.execute(
            "SELECT concept_id FROM alias WHERE alias_name = ?", (alias,)
        ).fetchone()
        return row["concept_id"] if row else None

    def resolve_concept(self, name: str) -> str | None:
        """Resolve a concept by alias, ID, or canonical name."""
        resolved = self.resolve_alias(name)
        if resolved:
            return resolved

        concept = self.get_concept(name)
        if concept:
            return name

        row = self._conn.execute(
            "SELECT id FROM concept WHERE canonical_name = ?",
            (name,),
        ).fetchone()
        return row["id"] if row else None

    def claims_for(self, concept_id: str | None) -> list[dict]:
        if not self._has_table("claim_core"):
            return []
        if concept_id is None:
            return self._claim_rows("ORDER BY core.id")
        return self._claim_rows(
            "WHERE core.concept_id = ? OR core.target_concept = ? ORDER BY core.id",
            (concept_id, concept_id),
        )

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, dict]:
        if not claim_ids or not self._has_table("claim_core"):
            return {}
        placeholders = ",".join("?" for _ in claim_ids)
        rows = self._claim_rows(
            f"WHERE core.id IN ({placeholders})",  # noqa: S608
            tuple(claim_ids),
        )
        return {row["id"]: row for row in rows}

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        if not claim_ids or not self._has_table("relation_edge"):
            return []
        placeholders = ",".join("?" for _ in claim_ids)
        target_justification_sql = self._claim_stance_target_justification_sql()
        rows = self._conn.execute(
            f"""
            SELECT
                source_id AS claim_id,
                target_id AS target_claim_id,
                relation_type AS stance_type,
                {target_justification_sql},
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
            list(claim_ids) + list(claim_ids),
        ).fetchall()
        return [dict(row) for row in rows]

    def conflicts(self, concept_id: str | None = None) -> list[dict]:
        if not self._has_table("conflict_witness"):
            return []
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
        return [dict(r) for r in rows]

    def all_concepts(self) -> list[dict]:
        if not self._has_table("concept"):
            return []
        rows = self._conn.execute("SELECT * FROM concept").fetchall()
        return [dict(row) for row in rows]

    def all_parameterizations(self) -> list[dict]:
        if not self._has_table("parameterization"):
            return []
        rows = self._conn.execute("SELECT * FROM parameterization").fetchall()
        return [dict(row) for row in rows]

    def all_relationships(self) -> list[dict]:
        if not self._has_table("relation_edge"):
            return []
        rows = self._conn.execute(
            """
            SELECT source_id, relation_type AS type, target_id, conditions_cel, note
            FROM relation_edge
            WHERE source_kind = 'concept' AND target_kind = 'concept'
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def all_claim_stances(self) -> list[dict]:
        if not self._has_table("relation_edge"):
            return []
        target_justification_sql = self._claim_stance_target_justification_sql()
        rows = self._conn.execute(
            """
            SELECT
                source_id AS claim_id,
                target_id AS target_claim_id,
                relation_type AS stance_type,
                """ + target_justification_sql + """,
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
        return [dict(row) for row in rows]

    def concept_ids_for_group(self, group_id: int) -> set[str]:
        if not self._has_table("parameterization_group"):
            return set()
        rows = self._conn.execute(
            "SELECT concept_id FROM parameterization_group WHERE group_id = ?",
            (group_id,),
        ).fetchall()
        return {row["concept_id"] for row in rows}

    def search(self, query: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH ?",
            (query,),
        ).fetchall()
        return [dict(r) for r in rows]

    def similar_claims(
        self,
        claim_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[dict]:
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
        return find_similar(self._conn, claim_id, model_name, top_k=top_k)

    def similar_concepts(
        self,
        concept_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[dict]:
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
        return find_similar_concepts(self._conn, concept_id, model_name, top_k=top_k)

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
        if not self._has_table("form"):
            return []
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
        if not self._has_table("form_algebra"):
            return []
        rows = self._conn.execute(
            "SELECT * FROM form_algebra WHERE output_form = ?", (form_name,)
        ).fetchall()
        return [dict(r) for r in rows]

    def form_algebra_using(self, form_name: str) -> list[dict]:
        """Get all algebra entries where *form_name* is an input."""
        if not self._has_table("form_algebra"):
            return []
        rows = self._conn.execute("SELECT * FROM form_algebra").fetchall()
        results = []
        for row in rows:
            input_forms = json.loads(row["input_forms"])
            if form_name in input_forms:
                results.append(dict(row))
        return results

    def stats(self) -> dict:
        concepts = self._conn.execute("SELECT COUNT(*) FROM concept").fetchone()[0]
        if self._has_table("claim_core"):
            claims = self._conn.execute("SELECT COUNT(*) FROM claim_core").fetchone()[0]
        else:
            claims = 0
        if self._has_table("conflict_witness"):
            conflicts = self._conn.execute("SELECT COUNT(*) FROM conflict_witness").fetchone()[0]
        else:
            conflicts = 0
        return {"concepts": concepts, "claims": claims, "conflicts": conflicts}

    # ── Parameterization queries ─────────────────────────────────────

    def _parameterizations_for(self, concept_id: str) -> list[dict]:
        """Get parameterization rows where output_concept_id matches."""
        if not self._has_table("parameterization"):
            return []
        rows = self._conn.execute(
            "SELECT * FROM parameterization WHERE output_concept_id = ?",
            (concept_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def parameterizations_for(self, concept_id: str) -> list[dict]:
        return self._parameterizations_for(concept_id)

    def compiled_graph(self):
        """Build the canonical compiled semantic graph from the current sidecar."""
        from propstore.core.graph_types import CompiledWorldGraph
        from propstore.core.graph_build import build_compiled_world_graph

        if self._compiled_graph_cache is None:
            self._compiled_graph_cache = build_compiled_world_graph(self)
        return CompiledWorldGraph.from_dict(self._compiled_graph_cache.to_dict())

    def active_graph(
        self,
        environment: Environment,
        *,
        context_hierarchy: ContextHierarchy | None = None,
    ):
        from propstore.core.activation import activate_compiled_world_graph
        from propstore.core.graph_types import ActiveWorldGraph

        hierarchy = context_hierarchy or self._load_context_hierarchy()
        cache_key = json.dumps(environment.to_dict(), sort_keys=True)
        if cache_key not in self._active_graph_cache:
            self._active_graph_cache[cache_key] = activate_compiled_world_graph(
                self.compiled_graph(),
                environment=environment,
                solver=self.condition_solver(),
                context_hierarchy=hierarchy,
            )
        cached = self._active_graph_cache[cache_key]
        return ActiveWorldGraph.from_dict(cached.to_dict())

    def _group_members(self, concept_id: str) -> list[str]:
        """Get all concept_ids in the same parameterization group."""
        if not self._has_table("parameterization_group"):
            return []
        row = self._conn.execute(
            "SELECT group_id FROM parameterization_group WHERE concept_id = ?",
            (concept_id,),
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

    def explain(self, claim_id: str) -> list[dict]:
        """Walk normalized claim relation edges breadth-first from claim_id."""
        if not self._has_table("relation_edge"):
            return []
        target_justification_sql = self._claim_stance_target_justification_sql()
        result: list[dict] = []
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
                    """ + target_justification_sql + """,
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
                stance = dict(row)
                result.append(stance)
                target = stance["target_claim_id"]
                if target not in visited:
                    visited.add(target)
                    queue.append(target)

        return result

    def _has_column(self, table: str, column: str) -> bool:
        key = (table, column)
        if key in self._column_cache:
            return self._column_cache[key]
        rows = self._conn.execute(f"PRAGMA table_info({table})").fetchall()  # noqa: S608
        exists = any(row["name"] == column for row in rows)
        self._column_cache[key] = exists
        return exists

    def _claim_stance_target_justification_sql(self) -> str:
        if self._has_column("relation_edge", "target_justification_id"):
            return "target_justification_id"
        return "NULL AS target_justification_id"

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

        context_hierarchy = self._load_context_hierarchy()
        if environment.context_id is not None and context_hierarchy is not None:
            environment = Environment(
                bindings=environment.bindings,
                context_id=environment.context_id,
                effective_assumptions=tuple(
                    context_hierarchy.effective_assumptions(environment.context_id)
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
            context_hierarchy=context_hierarchy,
            policy=policy,
            active_graph=self.active_graph(
                environment,
                context_hierarchy=context_hierarchy,
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
                if vr.status == "determined":
                    value = vr.claims[0].get("value") if vr.claims else None
                    if value is not None:
                        resolved_values[cid] = value
                        steps.append(ChainStep(concept_id=cid, value=value, source="claim"))
                        visited.add(cid)
                        changed = True
                        continue

                # If conflicted and strategy given, try resolve
                if vr.status == "conflicted" and strategy is not None:
                    rr = bound.resolved_value(cid)
                    if rr.status == "resolved" and rr.value is not None:
                        resolved_values[cid] = rr.value
                        steps.append(ChainStep(concept_id=cid, value=rr.value, source="resolved"))
                        visited.add(cid)
                        changed = True
                        continue

                # Track conflicted concepts that could not be resolved
                if vr.status == "conflicted" and cid not in unresolved_conflicted:
                    unresolved_conflicted.append(cid)

                # Try derived_value
                dr = bound.derived_value(cid, override_values=resolved_values)
                if dr.status == "derived" and dr.value is not None:
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
            if dr.status == "derived":
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
