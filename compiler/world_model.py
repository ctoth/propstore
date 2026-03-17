"""WorldModel — condition-binding reasoner over compiled knowledge.

Provides read-only queries against the sidecar SQLite, and condition-bound
views via Z3 satisfiability checking. The core insight: a claim is active
under bindings B when its conditions are NOT disjoint from B.
"""

from __future__ import annotations

import json
import sqlite3
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from compiler.cel_checker import ConceptInfo, KindType
from compiler.z3_conditions import Z3ConditionSolver


_FORM_TO_KIND = {
    "category": KindType.CATEGORY,
    "boolean": KindType.BOOLEAN,
    "structural": KindType.STRUCTURAL,
}


@dataclass
class ValueResult:
    concept_id: str
    status: str  # "determined" | "conflicted" | "underdetermined" | "no_claims"
    claims: list[dict] = field(default_factory=list)


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
            form = row["form"] or ""
            kind = _FORM_TO_KIND.get(form, KindType.QUANTITY)
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
        if concept_id is None:
            rows = self._conn.execute("SELECT * FROM claim").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM claim WHERE concept_id = ?", (concept_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def conflicts(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM conflicts").fetchall()
        return [dict(r) for r in rows]

    def search(self, query: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH ?",
            (query,),
        ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict:
        concepts = self._conn.execute("SELECT COUNT(*) FROM concept").fetchone()[0]
        claims = self._conn.execute("SELECT COUNT(*) FROM claim").fetchone()[0]
        conflicts = self._conn.execute("SELECT COUNT(*) FROM conflicts").fetchone()[0]
        return {"concepts": concepts, "claims": claims, "conflicts": conflicts}

    # ── Stance graph ─────────────────────────────────────────────────

    def explain(self, claim_id: str) -> list[dict]:
        """Walk claim_stance edges breadth-first from claim_id."""
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
        return BoundWorld(self, conditions)


class BoundWorld:
    """The world under specific condition bindings."""

    def __init__(self, world: WorldModel, bindings: dict[str, Any]) -> None:
        self._world = world
        self._bindings = bindings
        self._binding_conds = self._bindings_to_cel(bindings)

    @staticmethod
    def _bindings_to_cel(bindings: dict[str, Any]) -> list[str]:
        """Convert keyword bindings to CEL condition strings."""
        conds: list[str] = []
        for key, value in bindings.items():
            if isinstance(value, str):
                conds.append(f"{key} == '{value}'")
            elif isinstance(value, bool):
                conds.append(f"{key} == {'true' if value else 'false'}")
            else:
                conds.append(f"{key} == {value}")
        return conds

    def _is_active(self, claim: dict) -> bool:
        """Check if a claim is active under the current bindings."""
        conds_json = claim.get("conditions_cel")
        if not conds_json:
            return True  # unconditional → always active
        claim_conds = json.loads(conds_json)
        if not claim_conds:
            return True  # empty conditions → always active
        if not self._binding_conds:
            return True  # no bindings → everything active

        solver = self._world._ensure_solver()
        return not solver.are_disjoint(self._binding_conds, claim_conds)

    def active_claims(self, concept_id: str | None = None) -> list[dict]:
        all_claims = self._world.claims_for(concept_id)
        return [c for c in all_claims if self._is_active(c)]

    def inactive_claims(self, concept_id: str | None = None) -> list[dict]:
        all_claims = self._world.claims_for(concept_id)
        return [c for c in all_claims if not self._is_active(c)]

    def value_of(self, concept_id: str) -> ValueResult:
        active = self.active_claims(concept_id)
        if not active:
            return ValueResult(concept_id=concept_id, status="no_claims")

        # Check if all active claims agree on value
        values = set()
        for c in active:
            v = c.get("value")
            if v is not None:
                values.add(v)

        if not values:
            # No value-bearing claims (e.g. only observations/equations)
            return ValueResult(concept_id=concept_id, status="no_claims", claims=active)

        if len(values) == 1:
            return ValueResult(concept_id=concept_id, status="determined", claims=active)

        return ValueResult(concept_id=concept_id, status="conflicted", claims=active)

    def is_determined(self, concept_id: str) -> bool:
        return self.value_of(concept_id).status == "determined"

    def conflicts(self, concept_id: str | None = None) -> list[dict]:
        """Return world conflicts that are still active under current bindings."""
        all_conflicts = self._world.conflicts()
        active_ids = {c["id"] for c in self.active_claims(concept_id)}

        result = []
        for conflict in all_conflicts:
            # Both claims in the conflict must be active
            if conflict["claim_a_id"] in active_ids and conflict["claim_b_id"] in active_ids:
                if concept_id is None or conflict.get("concept_id") == concept_id:
                    result.append(conflict)
        return result

    def explain(self, claim_id: str) -> list[dict]:
        """Stance walk filtered to active claims."""
        # If the claim itself is inactive, return nothing
        claim = self._world.get_claim(claim_id)
        if claim is None or not self._is_active(claim):
            return []

        active_ids = {c["id"] for c in self.active_claims()}
        full_chain = self._world.explain(claim_id)
        # Filter: only include stances where the target is also active
        return [s for s in full_chain if s["target_claim_id"] in active_ids]
