"""HypotheticalWorld — graph-delta overlay on a BoundWorld."""

from __future__ import annotations

import json
from dataclasses import dataclass
from collections.abc import Sequence
from typing import Any, Mapping

from propstore.core.environment import (
    ArtifactStore,
    ClaimCatalogStore,
    CompiledGraphStore,
    ConceptCatalogStore,
    ParameterizationCatalogStore,
    ParameterizationLookupStore,
    StanceStore,
)
from propstore.core.activation import activate_compiled_world_graph
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.id_types import ConceptId, to_claim_id, to_claim_ids, to_concept_id
from propstore.core.graph_types import (
    ClaimNode,
    CompiledWorldGraph,
    ConflictWitness,
    GraphDelta,
)
from propstore.core.row_types import (
    ClaimRow,
    ClaimRowInput,
    coerce_claim_row,
    coerce_concept_row,
    coerce_conflict_row,
    coerce_parameterization_row,
    coerce_relationship_row,
    coerce_stance_row,
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
    left, right = sorted((str(left_id), str(right_id)))
    return left, right


def _claim_mapping(claim_input: ClaimRowInput | dict[str, Any]) -> dict[str, Any]:
    return coerce_claim_row(claim_input).to_dict()


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


def _compiled_graph_for_bound(base: BoundWorld) -> CompiledWorldGraph | None:
    if base._active_graph is not None:
        return base._active_graph.compiled
    if isinstance(base._store, CompiledGraphStore):
        return base._store.compiled_graph()
    if (
        isinstance(base._store, ConceptCatalogStore)
        and isinstance(base._store, ClaimCatalogStore)
        and isinstance(base._store, ParameterizationLookupStore)
        and isinstance(base._store, StanceStore)
    ):
        return build_compiled_world_graph(
            _ParameterizationCatalogAdapter(base._store)
        )
    if (
        isinstance(base._store, ConceptCatalogStore)
        and isinstance(base._store, ClaimCatalogStore)
        and isinstance(base._store, ParameterizationCatalogStore)
    ):
        return build_compiled_world_graph(base._store)
    return None


@dataclass(frozen=True)
class _ParameterizationCatalogAdapter:
    base: ArtifactStore

    def all_concepts(self):
        return list(self.base.all_concepts())

    def claims_for(self, concept_id: str | None):
        return list(self.base.claims_for(concept_id))

    def conflicts(self):
        return list(self.base.conflicts())

    def stances_between(self, claim_ids: set[str]):
        return list(self.base.stances_between(claim_ids))

    def all_parameterizations(self) -> list[dict[str, Any]]:
        seen: set[tuple[object, ...]] = set()
        rows: list[dict[str, Any]] = []
        for concept_input in self.base.all_concepts():
            concept_id = str(coerce_concept_row(concept_input).concept_id)
            for row_input in self.base.parameterizations_for(concept_id):
                row = coerce_parameterization_row(
                    row_input,
                    output_concept_id=concept_id,
                )
                row_key = (
                    row.output_concept_id,
                    row.concept_ids,
                    row.formula,
                    row.sympy,
                    row.exactness,
                    row.conditions_cel,
                    tuple(sorted(row.attributes.items())),
                )
                if row_key in seen:
                    continue
                seen.add(row_key)
                rows.append(row.to_dict())
        return rows


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
    existing_row: ClaimRowInput | None,
) -> ClaimRow:
    row: dict[str, Any] = (
        _claim_mapping(existing_row)
        if existing_row is not None
        else {"id": synthetic.id, "artifact_id": synthetic.id}
    )
    row["id"] = synthetic.id
    row["artifact_id"] = row.get("artifact_id") or synthetic.id
    row["concept_id"] = synthetic.concept_id
    row["type"] = synthetic.type
    row["value"] = synthetic.value
    row["conditions_cel"] = json.dumps(synthetic.conditions) if synthetic.conditions else None
    return ClaimRow.from_mapping(row)


class _GraphOverlayStore:
    def __init__(
        self,
        base_store: ArtifactStore,
        *,
        claims: list[ClaimRowInput],
        stances: list[dict],
        conflicts: list[dict],
        compiled: CompiledWorldGraph | None,
    ) -> None:
        self._base = base_store
        self._claims = [coerce_claim_row(claim) for claim in claims]
        self._claims_by_id = {str(claim.claim_id): claim for claim in self._claims}
        self._stances = [dict(stance) for stance in stances]
        self._conflicts = [dict(conflict) for conflict in conflicts]
        self._compiled = compiled

    def __getattr__(self, name: str):
        return getattr(self._base, name)

    def get_concept(self, concept_id: str):
        getter = getattr(self._base, "get_concept", None)
        if callable(getter):
            concept = getter(concept_id)
            return concept
        if not hasattr(self._base, "all_concepts"):
            return None
        for concept_input in self._base.all_concepts():
            concept = coerce_concept_row(concept_input)
            if str(concept.concept_id) == concept_id or concept.canonical_name == concept_id:
                return concept
        return None

    def get_claim(self, claim_id: str) -> ClaimRow | None:
        resolved_claim_id = self.resolve_claim(claim_id) or claim_id
        return self._claims_by_id.get(resolved_claim_id)

    def resolve_claim(self, name: str) -> str | None:
        resolver = getattr(self._base, "resolve_claim", None)
        if callable(resolver):
            return resolver(name)
        return None

    def resolve_alias(self, alias: str) -> str | None:
        resolver = getattr(self._base, "resolve_alias", None)
        if callable(resolver):
            return resolver(alias)
        return None

    def resolve_concept(self, name: str) -> str | None:
        resolver = getattr(self._base, "resolve_concept", None)
        if callable(resolver):
            return resolver(name)
        return None

    def all_concepts(self):
        return list(self._base.all_concepts())

    def claims_for(self, concept_id: str | None) -> list[ClaimRow]:
        if concept_id is None:
            return list(self._claims)
        resolved_concept_id = self.resolve_concept(concept_id) or concept_id
        return [
            claim
            for claim in self._claims
            if str(claim.concept_id or "") == resolved_concept_id
            or str(claim.target_concept or "") == resolved_concept_id
        ]

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, ClaimRow]:
        return {
            claim_id: claim
            for claim_id, claim in self._claims_by_id.items()
            if claim_id in claim_ids
        }

    def stances_between(self, claim_ids: set[str]):
        return [
            stance
            for stance in self._stances
            if coerce_stance_row(stance).claim_id in claim_ids
            and coerce_stance_row(stance).target_claim_id in claim_ids
        ]

    def conflicts(self):
        return list(self._conflicts)

    def all_parameterizations(self):
        return list(self._base.all_parameterizations())

    def all_relationships(self):
        return list(self._base.all_relationships())

    def all_claim_stances(self):
        return list(self._stances)

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

    def parameterizations_for(self, concept_id: str):
        return list(self._base.parameterizations_for(concept_id))

    def explain(self, claim_id: str) -> list[dict]:
        if claim_id not in self._claims_by_id:
            return []
        active_ids = set(self._claims_by_id)
        return [
            stance.to_dict()
            for stance_input in self._base.explain(claim_id)
            if (stance := coerce_stance_row(stance_input)).target_claim_id in active_ids
        ]

    def compiled_graph(self) -> CompiledWorldGraph:
        if self._compiled is None:
            raise TypeError("compiled_graph() is unavailable for semantic-only overlays")
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
        claim_resolver = getattr(base._store, "resolve_claim", None)
        concept_resolver = getattr(base._store, "resolve_concept", None)
        self._removed_ids = {
            claim_resolver(claim_id) or claim_id
            if callable(claim_resolver)
            else claim_id
            for claim_id in (remove or [])
        }
        self._synthetics = [
            SyntheticClaim(
                id=(
                    claim_resolver(synthetic.id) or synthetic.id
                    if callable(claim_resolver)
                    else synthetic.id
                ),
                concept_id=(
                    concept_resolver(synthetic.concept_id) or synthetic.concept_id
                    if callable(concept_resolver)
                    else synthetic.concept_id
                ),
                type=synthetic.type,
                value=synthetic.value,
                conditions=list(synthetic.conditions),
            )
            for synthetic in (add or [])
        ]

        self._base_compiled = _compiled_graph_for_bound(base)
        if self._base_compiled is not None:
            self._graph_delta = GraphDelta(
                add_claims=tuple(
                    _claim_node_for_synthetic(synthetic, compiled=self._base_compiled)
                    for synthetic in self._synthetics
                ),
                remove_claim_ids=to_claim_ids(self._removed_ids),
            )
            self._compiled_graph = self._graph_delta.apply(self._base_compiled)
        else:
            self._graph_delta = None
            self._compiled_graph = None

        base_claim_rows = [_claim_mapping(claim) for claim in base._store.claims_for(None)]
        base_claim_rows_by_id = {claim["id"]: dict(claim) for claim in base_claim_rows}
        synthetics_by_id = {synthetic.id: synthetic for synthetic in self._synthetics}

        overlay_claims: list[ClaimRow] = []
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
                overlay_claims.append(coerce_claim_row(claim))

        existing_ids = {str(claim.claim_id) for claim in overlay_claims}
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
            str(claim.claim_id)
            for claim in overlay_claims
        }
        overlay_stances = (
            [
                coerce_stance_row(stance).to_dict()
                for stance in base._store.stances_between(overlay_claim_ids)
            ]
            if isinstance(base._store, StanceStore)
            else []
        )

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
        for conflict in _recomputed_conflicts(
            base._store,
            [claim.to_dict() for claim in overlay_claims],
        ):
            pair = _claim_pair(conflict["claim_a_id"], conflict["claim_b_id"])
            if pair in seen_conflict_pairs:
                continue
            overlay_conflicts.append(conflict)
            seen_conflict_pairs.add(pair)

        if self._compiled_graph is not None:
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
        self._active_graph = (
            activate_compiled_world_graph(
                self._compiled_graph,
                environment=base._environment,
                solver=self._overlay_store.condition_solver(),
                context_hierarchy=base._context_hierarchy,
            )
            if self._compiled_graph is not None
            else None
        )
        self._overlay = BoundWorld(
            self._overlay_store,
            environment=base._environment,
            context_hierarchy=base._context_hierarchy,
            policy=base._policy,
            active_graph=self._active_graph,
        )

    def _synthetic_to_dict(self, sc: SyntheticClaim) -> dict:
        return _synthetic_row(sc, existing_row=self._base._store.get_claim(sc.id)).to_dict()

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
            if claim and coerce_claim_row(claim).concept_id is not None:
                affected.add(str(coerce_claim_row(claim).concept_id))

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
