"""WorldModel — read-only reasoner over a compiled sidecar."""

from __future__ import annotations

import json
import sqlite3
from collections import deque
from typing import TYPE_CHECKING, Any

from propstore.cel_checker import ConceptInfo, KindType

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

    def __init__(self, repo: Repository) -> None:
        sidecar_path = repo.sidecar_path
        if not sidecar_path.exists():
            raise FileNotFoundError(
                f"Sidecar not found at {sidecar_path}. Run 'pks build' first."
            )
        self._conn = sqlite3.connect(sidecar_path)
        self._conn.row_factory = sqlite3.Row
        self._solver: Z3ConditionSolver | None = None
        self._registry: dict[str, ConceptInfo] | None = None
        self._context_hierarchy: ContextHierarchy | None = None
        self._context_hierarchy_loaded = False
        self._table_cache: dict[str, bool] = {}
        self._claim_has_target_concept: bool | None = None

    def __enter__(self) -> WorldModel:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
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

        from propstore.validate_contexts import ContextHierarchy, LoadedContext

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
            LoadedContext(filename=context_id, filepath=None, data=data)
            for context_id, data in contexts_by_id.items()
        ]
        self._context_hierarchy = ContextHierarchy(loaded_contexts)
        return self._context_hierarchy

    # ── Unbound queries ──────────────────────────────────────────────

    def get_concept(self, concept_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM concept WHERE id = ?", (concept_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_claim(self, claim_id: str) -> dict | None:
        if not self._has_table("claim"):
            return None
        row = self._conn.execute(
            "SELECT * FROM claim WHERE id = ?", (claim_id,)
        ).fetchone()
        return dict(row) if row else None

    def resolve_alias(self, alias: str) -> str | None:
        row = self._conn.execute(
            "SELECT concept_id FROM alias WHERE alias_name = ?", (alias,)
        ).fetchone()
        return row["concept_id"] if row else None

    def claims_for(self, concept_id: str | None) -> list[dict]:
        if not self._has_table("claim"):
            return []
        if concept_id is None:
            rows = self._conn.execute("SELECT * FROM claim").fetchall()
        else:
            if self._claim_has_target_concept is None:
                self._claim_has_target_concept = (
                    self._conn.execute(
                        "SELECT 1 FROM pragma_table_info('claim') WHERE name = 'target_concept'"
                    ).fetchone()
                    is not None
                )
            if self._claim_has_target_concept:
                rows = self._conn.execute(
                    "SELECT * FROM claim WHERE concept_id = ? OR target_concept = ?",
                    (concept_id, concept_id),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM claim WHERE concept_id = ?", (concept_id,)
                ).fetchall()
        return [dict(r) for r in rows]

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, dict]:
        if not claim_ids or not self._has_table("claim"):
            return {}
        placeholders = ",".join("?" for _ in claim_ids)
        rows = self._conn.execute(
            f"SELECT * FROM claim WHERE id IN ({placeholders})",  # noqa: S608
            list(claim_ids),
        ).fetchall()
        return {row["id"]: dict(row) for row in rows}

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        if not claim_ids or not self._has_table("claim_stance"):
            return []
        placeholders = ",".join("?" for _ in claim_ids)
        rows = self._conn.execute(
            f"SELECT * FROM claim_stance "  # noqa: S608
            f"WHERE claim_id IN ({placeholders}) "
            f"AND target_claim_id IN ({placeholders})",
            list(claim_ids) + list(claim_ids),
        ).fetchall()
        return [dict(row) for row in rows]

    def conflicts(self) -> list[dict]:
        if not self._has_table("conflicts"):
            return []
        rows = self._conn.execute("SELECT * FROM conflicts").fetchall()
        return [dict(r) for r in rows]

    def all_concepts(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM concept").fetchall()
        return [dict(row) for row in rows]

    def all_parameterizations(self) -> list[dict]:
        if not self._has_table("parameterization"):
            return []
        rows = self._conn.execute("SELECT * FROM parameterization").fetchall()
        return [dict(row) for row in rows]

    def all_relationships(self) -> list[dict]:
        if not self._has_table("relationship"):
            return []
        rows = self._conn.execute("SELECT * FROM relationship").fetchall()
        return [dict(row) for row in rows]

    def all_claim_stances(self) -> list[dict]:
        if not self._has_table("claim_stance"):
            return []
        rows = self._conn.execute("SELECT * FROM claim_stance").fetchall()
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

    def stats(self) -> dict:
        concepts = self._conn.execute("SELECT COUNT(*) FROM concept").fetchone()[0]
        if self._has_table("claim"):
            claims = self._conn.execute("SELECT COUNT(*) FROM claim").fetchone()[0]
        else:
            claims = 0
        if self._has_table("conflicts"):
            conflicts = self._conn.execute("SELECT COUNT(*) FROM conflicts").fetchone()[0]
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
        """Walk claim_stance edges breadth-first from claim_id."""
        if not self._has_table("claim_stance"):
            return []
        result: list[dict] = []
        visited: set[str] = set()
        queue: deque[str] = deque([claim_id])
        visited.add(claim_id)

        while queue:
            current = queue.popleft()
            rows = self._conn.execute(
                "SELECT * FROM claim_stance WHERE claim_id = ?", (current,)
            ).fetchall()
            for row in rows:
                stance = dict(row)
                result.append(stance)
                target = stance["target_claim_id"]
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
            )

        context_hierarchy = self._load_context_hierarchy()
        if environment.context_id is not None and context_hierarchy is not None:
            environment = Environment(
                bindings=environment.bindings,
                context_id=environment.context_id,
                effective_assumptions=tuple(
                    context_hierarchy.effective_assumptions(environment.context_id)
                ),
            )

        return BoundWorld(
            self,
            environment=environment,
            context_hierarchy=context_hierarchy,
            policy=policy,
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
            target_concept_id=target_concept_id,
            result=result,
            steps=steps,
            bindings_used=bindings,
        )
