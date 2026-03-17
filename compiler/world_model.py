"""WorldModel — condition-binding reasoner over compiled knowledge.

Provides read-only queries against the sidecar SQLite, and condition-bound
views via Z3 satisfiability checking. The core insight: a claim is active
under bindings B when its conditions are NOT disjoint from B.

Features:
- value_of(): evidence — what do the claims say?
- derived_value(): inference — what can be computed from relationships?
- resolve(): policy — given disagreement, who wins?
- hypothetical(): counterfactual — what if the evidence were different?
- chain_query(): composition — traverse the graph using all of the above
"""

from __future__ import annotations

import json
import sqlite3
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from compiler.cel_checker import ConceptInfo, KindType
from compiler.z3_conditions import Z3ConditionSolver


_FORM_TO_KIND = {
    "category": KindType.CATEGORY,
    "boolean": KindType.BOOLEAN,
    "structural": KindType.STRUCTURAL,
}


# ── Data classes ──────────────────────────────────────────────────────


@dataclass
class ValueResult:
    concept_id: str
    status: str  # "determined" | "conflicted" | "underdetermined" | "no_claims"
    claims: list[dict] = field(default_factory=list)


@dataclass
class DerivedResult:
    concept_id: str
    status: str  # "derived" | "underspecified" | "no_relationship" | "conflicted"
    value: float | None = None
    formula: str | None = None
    input_values: dict[str, float] = field(default_factory=dict)
    exactness: str | None = None


class ResolutionStrategy(Enum):
    RECENCY = "recency"
    SAMPLE_SIZE = "sample_size"
    STANCE = "stance"
    OVERRIDE = "override"


@dataclass
class ResolvedResult:
    concept_id: str
    status: str  # "determined" | "conflicted" | "no_claims" | "resolved"
    value: float | str | None = None
    claims: list[dict] = field(default_factory=list)
    winning_claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None


@dataclass
class SyntheticClaim:
    id: str
    concept_id: str
    type: str = "parameter"
    value: float | str | None = None
    conditions: list[str] = field(default_factory=list)


@dataclass
class ChainStep:
    concept_id: str
    value: float | str | None
    source: str  # "binding" | "claim" | "derived" | "resolved"


@dataclass
class ChainResult:
    target_concept_id: str
    result: ValueResult | DerivedResult
    steps: list[ChainStep] = field(default_factory=list)
    bindings_used: dict[str, Any] = field(default_factory=dict)


# ── ClaimView protocol ───────────────────────────────────────────────


@runtime_checkable
class ClaimView(Protocol):
    def active_claims(self, concept_id: str | None = None) -> list[dict]: ...
    def inactive_claims(self, concept_id: str | None = None) -> list[dict]: ...
    def value_of(self, concept_id: str) -> ValueResult: ...
    def derived_value(self, concept_id: str) -> DerivedResult: ...
    def is_determined(self, concept_id: str) -> bool: ...


# ── Resolution strategy helpers ──────────────────────────────────────


def _resolve_recency(claims: list[dict]) -> tuple[str | None, str | None]:
    """Pick the claim with the most recent date in provenance_json."""
    best_id = None
    best_date = ""
    for c in claims:
        prov = c.get("provenance_json")
        if not prov:
            continue
        try:
            prov_data = json.loads(prov) if isinstance(prov, str) else prov
        except (json.JSONDecodeError, TypeError):
            continue
        date = prov_data.get("date") or ""
        if isinstance(date, str) and date > best_date:
            best_date = date
            best_id = c["id"]
    if best_id is None:
        return None, "no dates in provenance"
    return best_id, f"most recent: {best_date}"


def _resolve_sample_size(claims: list[dict]) -> tuple[str | None, str | None]:
    """Pick the claim with the largest sample_size."""
    best_id = None
    best_n: int | None = None
    for c in claims:
        n = c.get("sample_size")
        if n is not None and (best_n is None or n > best_n):
            best_n = n
            best_id = c["id"]
    if best_id is None:
        return None, "no sample_size values"
    return best_id, f"largest sample_size: {best_n}"


def _resolve_stance(claims: list[dict], world: WorldModel) -> tuple[str | None, str | None]:
    """Pick the claim with the highest net stance support (supports - contradicts)."""
    scores: dict[str, int] = {c["id"]: 0 for c in claims}
    claim_ids = set(scores.keys())

    if not world._has_table("claim_stance"):
        return None, "no stance data"

    for claim_id in claim_ids:
        # Find stances pointing AT this claim
        rows = world._conn.execute(
            "SELECT stance_type FROM claim_stance WHERE target_claim_id = ?",
            (claim_id,),
        ).fetchall()
        for row in rows:
            if row["stance_type"] == "supports":
                scores[claim_id] += 1
            elif row["stance_type"] == "contradicts":
                scores[claim_id] -= 1

    if not scores:
        return None, "no stance data"

    max_score = max(scores.values())
    winners = [cid for cid, s in scores.items() if s == max_score]
    if len(winners) > 1:
        return None, f"tied stance scores: {max_score}"
    return winners[0], f"net stance score: {max_score}"


def resolve(
    view: ClaimView,
    concept_id: str,
    strategy: ResolutionStrategy,
    *,
    world: WorldModel | None = None,
    overrides: dict[str, str] | None = None,
) -> ResolvedResult:
    """Apply a resolution strategy to a conflicted concept."""
    vr = view.value_of(concept_id)

    if vr.status == "no_claims":
        return ResolvedResult(concept_id=concept_id, status="no_claims")

    if vr.status == "determined":
        value = vr.claims[0].get("value") if vr.claims else None
        return ResolvedResult(
            concept_id=concept_id, status="determined",
            value=value, claims=vr.claims,
        )

    if vr.status != "conflicted":
        return ResolvedResult(
            concept_id=concept_id, status=vr.status, claims=vr.claims,
        )

    # Conflicted — apply strategy
    active = vr.claims
    winner_id: str | None = None
    reason: str | None = None

    if strategy == ResolutionStrategy.OVERRIDE:
        override_id = (overrides or {}).get(concept_id)
        if override_id is None:
            return ResolvedResult(
                concept_id=concept_id, status="conflicted",
                claims=active, reason="no override specified",
            )
        active_ids = {c["id"] for c in active}
        if override_id not in active_ids:
            raise ValueError(
                f"Override claim {override_id} is not an active claim for {concept_id}"
            )
        winner_id = override_id
        reason = f"override: {override_id}"

    elif strategy == ResolutionStrategy.RECENCY:
        winner_id, reason = _resolve_recency(active)

    elif strategy == ResolutionStrategy.SAMPLE_SIZE:
        winner_id, reason = _resolve_sample_size(active)

    elif strategy == ResolutionStrategy.STANCE:
        if world is None:
            # Try to get world from view
            if isinstance(view, BoundWorld):
                world = view._world
            elif isinstance(view, HypotheticalWorld):
                world = view._base._world
        if world is None:
            return ResolvedResult(
                concept_id=concept_id, status="conflicted",
                claims=active, reason="no world for stance resolution",
            )
        winner_id, reason = _resolve_stance(active, world)

    if winner_id is None:
        return ResolvedResult(
            concept_id=concept_id, status="conflicted",
            claims=active, strategy=strategy.value, reason=reason,
        )

    winning_claim = next((c for c in active if c["id"] == winner_id), None)
    value = winning_claim.get("value") if winning_claim else None
    return ResolvedResult(
        concept_id=concept_id, status="resolved",
        value=value, claims=active,
        winning_claim_id=winner_id,
        strategy=strategy.value, reason=reason,
    )


# ── WorldModel ────────────────────────────────────────────────────────


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
        return BoundWorld(self, conditions)

    # ── Chain query ──────────────────────────────────────────────────

    def chain_query(
        self,
        target_concept_id: str,
        strategy: ResolutionStrategy | None = None,
        **bindings: Any,
    ) -> ChainResult:
        """Traverse the parameter space to derive the target concept.

        Resolves intermediate concepts via claims/propagation/resolution,
        feeds those values as inputs to derive the target.
        """
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

    def _is_param_compatible(self, conditions_cel: str | None) -> bool:
        """Check if parameterization conditions are compatible with bindings."""
        if not conditions_cel:
            return True
        conds = json.loads(conditions_cel)
        if not conds:
            return True
        if not self._binding_conds:
            return True
        solver = self._world._ensure_solver()
        return not solver.are_disjoint(self._binding_conds, conds)

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

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: dict[str, float | str | None] | None = None,
    ) -> DerivedResult:
        """Derive a value for concept_id via parameterization relationships.

        Single-step only — uses value_of() on input concepts (or override_values
        from chain_query) to compute the output via SymPy.
        """
        from compiler.propagation import evaluate_parameterization

        params = self._world._parameterizations_for(concept_id)
        if not params:
            return DerivedResult(concept_id=concept_id, status="no_relationship")

        for param in params:
            # Check parameterization conditions against bindings
            if not self._is_param_compatible(param.get("conditions_cel")):
                continue

            sympy_expr = param.get("sympy")
            if not sympy_expr:
                continue

            input_ids = json.loads(param["concept_ids"])
            # Exclude self-references
            effective_inputs = [iid for iid in input_ids if iid != concept_id]

            # Collect input values
            input_values: dict[str, float] = {}
            all_determined = True
            any_conflicted = False

            for iid in effective_inputs:
                # Check override_values first (for chain_query)
                if override_values and iid in override_values:
                    ov = override_values[iid]
                    if ov is not None:
                        try:
                            input_values[iid] = float(ov)
                            continue
                        except (TypeError, ValueError):
                            pass

                vr = self.value_of(iid)
                if vr.status == "determined":
                    val = vr.claims[0].get("value") if vr.claims else None
                    if val is not None:
                        input_values[iid] = float(val)
                    else:
                        all_determined = False
                elif vr.status == "conflicted":
                    any_conflicted = True
                    all_determined = False
                else:
                    all_determined = False

            if any_conflicted:
                return DerivedResult(concept_id=concept_id, status="conflicted")

            if not all_determined or len(input_values) != len(effective_inputs):
                continue  # Try next parameterization

            result = evaluate_parameterization(sympy_expr, input_values, concept_id)
            if result is not None:
                return DerivedResult(
                    concept_id=concept_id,
                    status="derived",
                    value=result,
                    formula=param.get("formula"),
                    input_values=input_values,
                    exactness=param.get("exactness"),
                )

        # No parameterization succeeded
        if any(not self._is_param_compatible(p.get("conditions_cel")) for p in params):
            return DerivedResult(concept_id=concept_id, status="no_relationship")

        return DerivedResult(concept_id=concept_id, status="underspecified")

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


# ── HypotheticalWorld ────────────────────────────────────────────────


class HypotheticalWorld:
    """In-memory overlay on a BoundWorld — removes/adds claims without mutation.

    Known limitation: conflicts() returns base conflicts filtered by active IDs.
    It does NOT detect new conflicts from synthetic claims. Full conflict
    recomputation is deferred to Feature 7.
    """

    def __init__(
        self,
        base: BoundWorld,
        remove: list[str] | None = None,
        add: list[SyntheticClaim] | None = None,
    ) -> None:
        self._base = base
        self._removed_ids = set(remove or [])
        self._synthetics = list(add or [])

    def _synthetic_to_dict(self, sc: SyntheticClaim) -> dict:
        """Convert a SyntheticClaim to the dict format used by claims."""
        return {
            "id": sc.id,
            "concept_id": sc.concept_id,
            "type": sc.type,
            "value": sc.value,
            "conditions_cel": json.dumps(sc.conditions) if sc.conditions else None,
        }

    def active_claims(self, concept_id: str | None = None) -> list[dict]:
        base_active = self._base.active_claims(concept_id)
        # Remove specified claims
        filtered = [c for c in base_active if c["id"] not in self._removed_ids]
        # Add synthetics that match concept filter and pass _is_active
        for sc in self._synthetics:
            if concept_id is not None and sc.concept_id != concept_id:
                continue
            sc_dict = self._synthetic_to_dict(sc)
            if self._base._is_active(sc_dict):
                filtered.append(sc_dict)
        return filtered

    def inactive_claims(self, concept_id: str | None = None) -> list[dict]:
        base_inactive = self._base.inactive_claims(concept_id)
        # Remove specified claims from inactive too
        filtered = [c for c in base_inactive if c["id"] not in self._removed_ids]
        # Add synthetics that are inactive
        for sc in self._synthetics:
            if concept_id is not None and sc.concept_id != concept_id:
                continue
            sc_dict = self._synthetic_to_dict(sc)
            if not self._base._is_active(sc_dict):
                filtered.append(sc_dict)
        return filtered

    def value_of(self, concept_id: str) -> ValueResult:
        active = self.active_claims(concept_id)
        if not active:
            return ValueResult(concept_id=concept_id, status="no_claims")

        values = set()
        for c in active:
            v = c.get("value")
            if v is not None:
                values.add(v)

        if not values:
            return ValueResult(concept_id=concept_id, status="no_claims", claims=active)

        if len(values) == 1:
            return ValueResult(concept_id=concept_id, status="determined", claims=active)

        return ValueResult(concept_id=concept_id, status="conflicted", claims=active)

    def derived_value(self, concept_id: str) -> DerivedResult:
        """Derive using this hypothetical world's active claims."""
        from compiler.propagation import evaluate_parameterization

        params = self._base._world._parameterizations_for(concept_id)
        if not params:
            return DerivedResult(concept_id=concept_id, status="no_relationship")

        for param in params:
            if not self._base._is_param_compatible(param.get("conditions_cel")):
                continue

            sympy_expr = param.get("sympy")
            if not sympy_expr:
                continue

            input_ids = json.loads(param["concept_ids"])
            effective_inputs = [iid for iid in input_ids if iid != concept_id]

            input_values: dict[str, float] = {}
            all_determined = True
            any_conflicted = False

            for iid in effective_inputs:
                vr = self.value_of(iid)
                if vr.status == "determined":
                    val = vr.claims[0].get("value") if vr.claims else None
                    if val is not None:
                        input_values[iid] = float(val)
                    else:
                        all_determined = False
                elif vr.status == "conflicted":
                    any_conflicted = True
                    all_determined = False
                else:
                    all_determined = False

            if any_conflicted:
                return DerivedResult(concept_id=concept_id, status="conflicted")

            if not all_determined or len(input_values) != len(effective_inputs):
                continue

            result = evaluate_parameterization(sympy_expr, input_values, concept_id)
            if result is not None:
                return DerivedResult(
                    concept_id=concept_id,
                    status="derived",
                    value=result,
                    formula=param.get("formula"),
                    input_values=input_values,
                    exactness=param.get("exactness"),
                )

        return DerivedResult(concept_id=concept_id, status="underspecified")

    def is_determined(self, concept_id: str) -> bool:
        return self.value_of(concept_id).status == "determined"

    def diff(self) -> dict[str, tuple[ValueResult, ValueResult]]:
        """Compare base and hypothetical value_of for all affected concepts."""
        # Gather concept_ids that might differ
        affected: set[str] = set()
        for sc in self._synthetics:
            affected.add(sc.concept_id)
        for cid in self._removed_ids:
            claim = self._base._world.get_claim(cid)
            if claim and claim.get("concept_id"):
                affected.add(claim["concept_id"])

        result: dict[str, tuple[ValueResult, ValueResult]] = {}
        for cid in affected:
            base_vr = self._base.value_of(cid)
            hypo_vr = self.value_of(cid)
            if base_vr.status != hypo_vr.status or _value_set(base_vr) != _value_set(hypo_vr):
                result[cid] = (base_vr, hypo_vr)
        return result


def _value_set(vr: ValueResult) -> set:
    """Extract the set of values from a ValueResult for comparison."""
    return {c.get("value") for c in vr.claims if c.get("value") is not None}
