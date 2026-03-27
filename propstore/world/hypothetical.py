"""HypotheticalWorld — graph-delta overlay on a BoundWorld."""

from __future__ import annotations

import json

from propstore.core.activation import activate_compiled_world_graph
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.graph_types import (
    ClaimNode,
    CompiledWorldGraph,
    ConflictWitness,
    GraphDelta,
)
from propstore.world.bound import BoundWorld, _recomputed_conflicts
from propstore.world.types import (
    BeliefSpace,
    DerivedResult,
    ResolvedResult,
    SyntheticClaim,
    ValueResult,
)


def _claim_pair(left_id: str, right_id: str) -> tuple[str, str]:
    return tuple(sorted((str(left_id), str(right_id))))


def _conflict_witness_from_row(row: dict) -> ConflictWitness:
    return ConflictWitness(
        left_claim_id=str(row["claim_a_id"]),
        right_claim_id=str(row["claim_b_id"]),
        kind=str(row.get("warning_class") or row.get("conflict_class") or "conflict"),
        details={
            str(key): value
            for key, value in row.items()
            if key not in {"claim_a_id", "claim_b_id", "warning_class", "conflict_class"}
            and value is not None
        },
    )


def _compiled_graph_for_bound(base: BoundWorld) -> CompiledWorldGraph:
    if base._active_graph is not None:
        return base._active_graph.compiled
    compiled_getter = getattr(base._store, "compiled_graph", None)
    if callable(compiled_getter):
        return compiled_getter()
    return build_compiled_world_graph(base._store)


def _claim_node_for_synthetic(
    synthetic: SyntheticClaim,
    *,
    compiled: CompiledWorldGraph,
) -> ClaimNode:
    existing = next(
        (claim for claim in compiled.claims if claim.claim_id == synthetic.id),
        None,
    )
    attributes = dict(existing.attributes) if existing is not None else {}
    if synthetic.conditions:
        attributes["conditions_cel"] = json.dumps(synthetic.conditions)
    else:
        attributes.pop("conditions_cel", None)
    return ClaimNode(
        claim_id=synthetic.id,
        concept_id=synthetic.concept_id,
        claim_type=synthetic.type,
        scalar_value=synthetic.value,
        provenance=(existing.provenance if existing is not None else None),
        label=(existing.label if existing is not None else None),
        attributes=attributes,
    )


def _synthetic_row(
    synthetic: SyntheticClaim,
    *,
    existing_row: dict | None,
) -> dict:
    row = dict(existing_row) if existing_row is not None else {"id": synthetic.id}
    row["id"] = synthetic.id
    row["concept_id"] = synthetic.concept_id
    row["type"] = synthetic.type
    row["value"] = synthetic.value
    row["conditions_cel"] = json.dumps(synthetic.conditions) if synthetic.conditions else None
    return row


class _GraphOverlayStore:
    def __init__(
        self,
        base_store,
        *,
        claims: list[dict],
        stances: list[dict],
        conflicts: list[dict],
        compiled: CompiledWorldGraph,
    ) -> None:
        self._base = base_store
        self._claims = [dict(claim) for claim in claims]
        self._claims_by_id = {claim["id"]: dict(claim) for claim in self._claims}
        self._stances = [dict(stance) for stance in stances]
        self._conflicts = [dict(conflict) for conflict in conflicts]
        self._compiled = compiled

    def __getattr__(self, name: str):
        return getattr(self._base, name)

    def get_claim(self, claim_id: str) -> dict | None:
        claim = self._claims_by_id.get(claim_id)
        return None if claim is None else dict(claim)

    def claims_for(self, concept_id: str | None) -> list[dict]:
        if concept_id is None:
            return [dict(claim) for claim in self._claims]
        return [
            dict(claim)
            for claim in self._claims
            if claim.get("concept_id") == concept_id or claim.get("target_concept") == concept_id
        ]

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, dict]:
        return {
            claim_id: dict(claim)
            for claim_id, claim in self._claims_by_id.items()
            if claim_id in claim_ids
        }

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        return [
            dict(stance)
            for stance in self._stances
            if stance.get("claim_id") in claim_ids
            and stance.get("target_claim_id") in claim_ids
        ]

    def conflicts(self) -> list[dict]:
        return [dict(conflict) for conflict in self._conflicts]

    def all_claim_stances(self) -> list[dict]:
        return [dict(stance) for stance in self._stances]

    def explain(self, claim_id: str) -> list[dict]:
        if claim_id not in self._claims_by_id:
            return []
        active_ids = set(self._claims_by_id)
        return [
            dict(stance)
            for stance in self._base.explain(claim_id)
            if stance.get("target_claim_id") in active_ids
        ]

    def compiled_graph(self) -> CompiledWorldGraph:
        return CompiledWorldGraph.from_dict(self._compiled.to_dict())


class HypotheticalWorld(BeliefSpace):
    """Graph-delta overlay on a BoundWorld without mutating the base."""

    def __init__(
        self,
        base: BoundWorld,
        remove: list[str] | None = None,
        add: list[SyntheticClaim] | None = None,
    ) -> None:
        self._base = base
        self._removed_ids = set(remove or [])
        self._synthetics = list(add or [])

        self._base_compiled = _compiled_graph_for_bound(base)
        self._graph_delta = GraphDelta(
            add_claims=tuple(
                _claim_node_for_synthetic(synthetic, compiled=self._base_compiled)
                for synthetic in self._synthetics
            ),
            remove_claim_ids=tuple(self._removed_ids),
        )
        self._compiled_graph = self._graph_delta.apply(self._base_compiled)

        base_claim_rows = [dict(claim) for claim in base._store.claims_for(None)]
        base_claim_rows_by_id = {claim["id"]: dict(claim) for claim in base_claim_rows}
        synthetics_by_id = {synthetic.id: synthetic for synthetic in self._synthetics}

        overlay_claims: list[dict] = []
        for claim in base_claim_rows:
            claim_id = claim.get("id")
            replacement = synthetics_by_id.get(claim_id)
            if claim_id in self._removed_ids and replacement is None:
                continue
            if replacement is not None:
                overlay_claims.append(
                    _synthetic_row(replacement, existing_row=claim)
                )
            else:
                overlay_claims.append(dict(claim))

        existing_ids = {claim["id"] for claim in overlay_claims if claim.get("id") is not None}
        for synthetic in self._synthetics:
            if synthetic.id in existing_ids:
                continue
            overlay_claims.append(
                _synthetic_row(
                    synthetic,
                    existing_row=base_claim_rows_by_id.get(synthetic.id),
                )
            )

        overlay_claim_ids = {
            str(claim["id"])
            for claim in overlay_claims
            if claim.get("id") is not None
        }
        stances_between = getattr(base._store, "stances_between", None)
        overlay_stances = (
            list(stances_between(overlay_claim_ids))
            if callable(stances_between)
            else []
        )

        conflicts_fn = getattr(base._store, "conflicts", None)
        overlay_conflicts = [
            dict(conflict)
            for conflict in (conflicts_fn() if callable(conflicts_fn) else [])
            if conflict.get("claim_a_id") in overlay_claim_ids
            and conflict.get("claim_b_id") in overlay_claim_ids
        ]
        seen_conflict_pairs = {
            _claim_pair(conflict["claim_a_id"], conflict["claim_b_id"])
            for conflict in overlay_conflicts
        }
        all_concepts = getattr(base._store, "all_concepts", None)
        if callable(all_concepts):
            for conflict in _recomputed_conflicts(base._store, overlay_claims):
                pair = _claim_pair(conflict["claim_a_id"], conflict["claim_b_id"])
                if pair in seen_conflict_pairs:
                    continue
                overlay_conflicts.append(conflict)
                seen_conflict_pairs.add(pair)

        self._compiled_graph = CompiledWorldGraph(
            concepts=self._compiled_graph.concepts,
            claims=self._compiled_graph.claims,
            relations=self._compiled_graph.relations,
            parameterizations=self._compiled_graph.parameterizations,
            conflicts=tuple(_conflict_witness_from_row(row) for row in overlay_conflicts),
        )
        self._overlay_store = _GraphOverlayStore(
            base._store,
            claims=overlay_claims,
            stances=overlay_stances,
            conflicts=overlay_conflicts,
            compiled=self._compiled_graph,
        )
        self._active_graph = activate_compiled_world_graph(
            self._compiled_graph,
            environment=base._environment,
            solver=self._overlay_store.condition_solver(),
            context_hierarchy=base._context_hierarchy,
        )
        self._overlay = BoundWorld(
            self._overlay_store,
            environment=base._environment,
            context_hierarchy=base._context_hierarchy,
            policy=base._policy,
            active_graph=self._active_graph,
        )

    def _synthetic_to_dict(self, sc: SyntheticClaim) -> dict:
        return _synthetic_row(sc, existing_row=self._base._store.get_claim(sc.id))

    def active_claims(self, concept_id: str | None = None) -> list[dict]:
        return self._overlay.active_claims(concept_id)

    def inactive_claims(self, concept_id: str | None = None) -> list[dict]:
        return self._overlay.inactive_claims(concept_id)

    def collect_known_values(self, variable_concepts: list[str]) -> dict:
        return self._overlay.collect_known_values(variable_concepts)

    def value_of(self, concept_id: str) -> ValueResult:
        return self._overlay.value_of(concept_id)

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: dict[str, float | str | None] | None = None,
    ) -> DerivedResult:
        return self._overlay.derived_value(
            concept_id,
            override_values=override_values,
        )

    def resolved_value(self, concept_id: str) -> ResolvedResult:
        return self._overlay.resolved_value(concept_id)

    def is_determined(self, concept_id: str) -> bool:
        return self._overlay.is_determined(concept_id)

    def conflicts(self, concept_id: str | None = None) -> list[dict]:
        return self._overlay.conflicts(concept_id)

    def explain(self, claim_id: str) -> list[dict]:
        return self._overlay.explain(claim_id)

    def recompute_conflicts(self) -> list[dict]:
        return _recomputed_conflicts(self._overlay_store, self.active_claims())

    def diff(self) -> dict[str, tuple[ValueResult, ValueResult]]:
        affected: set[str] = set()
        for synthetic in self._synthetics:
            affected.add(synthetic.concept_id)
        for claim_id in self._removed_ids:
            claim = self._base._store.get_claim(claim_id)
            if claim and claim.get("concept_id"):
                affected.add(claim["concept_id"])

        result: dict[str, tuple[ValueResult, ValueResult]] = {}
        for concept_id in affected:
            base_result = self._base.value_of(concept_id)
            hypothetical_result = self.value_of(concept_id)
            if (
                base_result.status != hypothetical_result.status
                or _value_set(base_result) != _value_set(hypothetical_result)
            ):
                result[concept_id] = (base_result, hypothetical_result)
        return result


def _value_set(vr: ValueResult) -> set:
    return {claim.get("value") for claim in vr.claims if claim.get("value") is not None}
