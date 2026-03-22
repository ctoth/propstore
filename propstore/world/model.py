"""WorldModel — read-only reasoner over a compiled sidecar."""

from __future__ import annotations

import json
import sqlite3
from collections import deque
from typing import TYPE_CHECKING, Any

from propstore.cel_checker import ConceptInfo, KindType

if TYPE_CHECKING:
    from propstore.world.bound import BoundWorld
from propstore.world.resolution import resolve
from propstore.world.types import (
    ChainResult,
    ChainStep,
    DerivedResult,
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


class WorldModel:
    """Read-only reasoner over a compiled sidecar."""

    def __init__(self, repo: object) -> None:
        sidecar_path = repo.sidecar_path  # type: ignore[union-attr]
        if not sidecar_path.exists():
            raise FileNotFoundError(
                f"Sidecar not found at {sidecar_path}. Run 'pks build' first."
            )
        self._conn = sqlite3.connect(sidecar_path)
        self._conn.row_factory = sqlite3.Row
        self._solver: Z3ConditionSolver | None = None
        self._registry: dict[str, ConceptInfo] | None = None

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
            rows = self._conn.execute(
                "SELECT * FROM claim WHERE concept_id = ?", (concept_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def conflicts(self) -> list[dict]:
        if not self._has_table("conflicts"):
            return []
        rows = self._conn.execute("SELECT * FROM conflicts").fetchall()
        return [dict(r) for r in rows]

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

        return find_similar_concepts(self._conn, concept_id, model_name, top_k=top_k)

    def _has_table(self, name: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None

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

    def bind(self, **conditions: Any) -> BoundWorld:
        from propstore.world.bound import BoundWorld
        return BoundWorld(self, conditions)

    # ── Chain query ──────────────────────────────────────────────────

    def chain_query(
        self,
        target_concept_id: str,
        strategy: ResolutionStrategy | None = None,
        **bindings: Any,
    ) -> ChainResult:
        """Traverse the parameter space to derive the target concept."""
        bound = self.bind(**bindings)
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
                    rr = resolve(bound, cid, strategy, world=self)
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
