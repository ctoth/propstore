"""HypotheticalWorld — graph-delta overlay on a BoundWorld."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Mapping

from propstore.core.environment import ArtifactStore, CompiledGraphStore, StanceStore
from propstore.core.activation import activate_compiled_world_graph
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.id_types import ConceptId, to_claim_id, to_claim_ids, to_concept_id
from propstore.core.graph_types import (
    ClaimNode,
    CompiledWorldGraph,
    ConflictWitness,
    GraphDelta,
)
from propstore.core.row_types import coerce_conflict_row, coerce_stance_row
from propstore.world.bound import BoundWorld, _recomputed_conflicts
from propstore.world.types import (
    BeliefSpace,
    DerivedResult,
    ResolvedResult,
    SyntheticClaim,
    ValueResult,
)


def _claim_pair(left_id: str, right_id: str) -> tuple[str, str]:
    left, right = sorted((str(left_id), str(right_id)))
    return left, right


def _conflict_witness_from_row(row: dict) -> ConflictWitness:
    conflict = coerce_conflict_row(row)
    return ConflictWitness(
        left_claim_id=conflict.claim_a_id,
        right_claim_id=conflict.claim_b_id,
        kind=str(conflict.warning_class or conflict.conflict_class or "conflict"),
        details=tuple(
            entry
            for entry in (
                (("concept_id", conflict.concept_id) if conflict.concept_id is not None else None),
                *tuple(conflict.attributes.items()),
            )
            if entry is not None
        ),
    )


def _compiled_graph_for_bound(base: BoundWorld) -> CompiledWorldGraph:
    if base._active_graph is not None:
        return base._active_graph.compiled
    if isinstance(base._store, CompiledGraphStore):
        return base._store.compiled_graph()
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
        claim_id=to_claim_id(synthetic.id),
        concept_id=to_concept_id(synthetic.concept_id),
        claim_type=synthetic.type,
        scalar_value=synthetic.value,
        provenance=(existing.provenance if existing is not None else None),
        label=(existing.label if existing is not None else None),
        attributes=tuple(attributes.items()),
    )


def _synthetic_row(
    synthetic: SyntheticClaim,
    *,
    existing_row: dict | None,
) -> dict:
    row: dict[str, Any] = (
        dict(existing_row)
        if existing_row is not None
        else {"id": synthetic.id}
    )
    row["id"] = synthetic.id
    row["concept_id"] = synthetic.concept_id
    row["type"] = synthetic.type
    row["value"] = synthetic.value
    row["conditions_cel"] = json.dumps(synthetic.conditions) if synthetic.conditions else None
    return row


class _GraphOverlayStore:
    def __init__(
        self,
        base_store: ArtifactStore,
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

    def get_concept(self, concept_id: str) -> dict | None:
        concept = self._base.get_concept(concept_id)
        return None if concept is None else dict(concept)

    def get_claim(self, claim_id: str) -> dict | None:
        claim = self._claims_by_id.get(claim_id)
        return None if claim is None else dict(claim)

    def resolve_alias(self, alias: str) -> str | None:
        return self._base.resolve_alias(alias)

    def resolve_concept(self, name: str) -> str | None:
        return self._base.resolve_concept(name)

    def all_concepts(self) -> list[dict]:
        return [dict(concept) for concept in self._base.all_concepts()]

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

    def all_parameterizations(self) -> list[dict]:
        return [dict(row) for row in self._base.all_parameterizations()]

    def all_relationships(self) -> list[dict]:
        return [dict(row) for row in self._base.all_relationships()]

    def all_claim_stances(self) -> list[dict]:
        return [dict(stance) for stance in self._stances]

    def concept_ids_for_group(self, group_id: int) -> set[str]:
        return set(self._base.concept_ids_for_group(group_id))

    def search(self, query: str) -> list[dict]:
        return [dict(row) for row in self._base.search(query)]

    def similar_claims(
        self,
        claim_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[dict]:
        return [
            dict(row)
            for row in self._base.similar_claims(
                claim_id,
                model_name=model_name,
                top_k=top_k,
            )
        ]

    def similar_concepts(
        self,
        concept_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[dict]:
        return [
            dict(row)
            for row in self._base.similar_concepts(
                concept_id,
                model_name=model_name,
                top_k=top_k,
            )
        ]

    def stats(self) -> dict:
        return dict(self._base.stats())

    def parameterizations_for(self, concept_id: str) -> list[dict]:
        return [dict(row) for row in self._base.parameterizations_for(concept_id)]

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

    def condition_solver(self):
        return self._base.condition_solver()

    def has_table(self, name: str) -> bool:
        return self._base.has_table(name)

    def group_members(self, concept_id: str) -> list[str]:
        return list(self._base.group_members(concept_id))

    def chain_query(self, target_concept_id: str, strategy=None, **bindings: Any):
        return self._base.chain_query(
            target_concept_id,
            strategy=strategy,
            **bindings,
        )


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
            remove_claim_ids=to_claim_ids(self._removed_ids),
        )
        self._compiled_graph = self._graph_delta.apply(self._base_compiled)

        base_claim_rows = [dict(claim) for claim in base._store.claims_for(None)]
        base_claim_rows_by_id = {claim["id"]: dict(claim) for claim in base_claim_rows}
        synthetics_by_id = {synthetic.id: synthetic for synthetic in self._synthetics}

        overlay_claims: list[dict] = []
        for claim in base_claim_rows:
            claim_id = claim.get("id")
            if not isinstance(claim_id, str):
                continue
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
        if not isinstance(base._store, StanceStore):
            raise TypeError("HypotheticalWorld requires stances_between() on the base store")
        overlay_stances = [
            coerce_stance_row(stance).to_dict()
            for stance in base._store.stances_between(overlay_claim_ids)
        ]

        overlay_conflicts = [
            conflict.to_dict()
            for conflict in (
                coerce_conflict_row(conflict_input)
                for conflict_input in base._store.conflicts()
            )
            if conflict.claim_a_id in overlay_claim_ids
            and conflict.claim_b_id in overlay_claim_ids
        ]
        seen_conflict_pairs = {
            _claim_pair(conflict["claim_a_id"], conflict["claim_b_id"])
            for conflict in overlay_conflicts
        }
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

    def collect_known_values(
        self,
        variable_concepts: Sequence[ConceptId | str],
    ) -> dict[ConceptId, Any]:
        return self._overlay.collect_known_values(variable_concepts)

    def value_of(self, concept_id: str) -> ValueResult:
        return self._overlay.value_of(concept_id)

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: Mapping[str, float | str | None] | None = None,
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
