"""OverlayWorld — graph-delta overlay on a BoundWorld."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from collections.abc import Sequence
from typing import Any, Callable, Mapping, cast

from propstore.conflict_detector import ConflictClass
from propstore.core.conditions.registry import ConceptInfo
from propstore.core.environment import (
    WorldStore,
    ClaimCatalogStore,
    CompiledGraphStore,
    ConceptCatalogStore,
    ParameterizationCatalogStore,
    ParameterizationLookupStore,
    StanceStore,
)
from propstore.core.activation import activate_compiled_world_graph
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
)
from propstore.core.graph_types import (
    CompiledWorldGraph,
    ConflictWitness,
    GraphDelta,
)
from propstore.core.store_results import (
    WorldStoreStats,
    ClaimSimilarityHit,
    ConceptSearchHit,
    ConceptSimilarityHit,
)
from propstore.families.claims.declaration import (
    Claim,
)
from propstore.families.claims.graph import claim_node_from_claim, synthetic_claim_to_claim
from propstore.families.micropublications.declaration import Micropublication
from propstore.families.relations.declaration import (
    ConceptRelation,
    ConflictWitness as RelationConflictWitness,
    Stance,
)
from propstore.families.concepts.declaration import (
    Concept,
    Parameterization,
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


def _conflict_witness_from_model(row: RelationConflictWitness) -> ConflictWitness:
    conflict = row
    return ConflictWitness(
        left_claim_id=ClaimId(conflict.claim_a_id),
        right_claim_id=ClaimId(conflict.claim_b_id),
        kind=(
            warning_class.value
            if isinstance(
                warning_class := (conflict.warning_class or conflict.conflict_class),
                ConflictClass,
            )
            else str(warning_class or "conflict")
        ),
        details=tuple(
            entry
            for entry in (
                (("concept_id", conflict.concept_id) if conflict.concept_id is not None else None),
                *tuple(conflict.attribute_mapping().items()),
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
    base: WorldStore

    def all_concepts(self):
        return list(self.base.all_concepts())

    def claims_for(self, concept_id: str | None):
        return list(self.base.claims_for(concept_id))

    def conflicts(self):
        return list(self.base.conflicts())

    def stances_between(self, claim_ids: set[str]):
        return list(self.base.stances_between(claim_ids))

    def all_parameterizations(self) -> list[Parameterization]:
        seen: set[tuple[object, ...]] = set()
        rows: list[Parameterization] = []
        for concept in self.base.all_concepts():
            concept_id = str(concept.concept_id)
            for row in self.base.parameterizations_for(concept_id):
                row_key = (
                    row.output_concept_id,
                    row.concept_ids,
                    row.formula,
                    row.sympy,
                    row.exactness,
                    row.conditions_cel,
                )
                if row_key in seen:
                    continue
                seen.add(row_key)
                rows.append(row)
        return rows


class _GraphOverlayStore:
    def __init__(
        self,
        base_store: WorldStore,
        *,
        claims: Sequence[Claim],
        stances: list[Stance],
        conflicts: list[RelationConflictWitness],
        compiled: CompiledWorldGraph | None,
    ) -> None:
        self._base = base_store
        self._claims = list(claims)
        self._claims_by_id = {str(claim.id): claim for claim in self._claims}
        self._stances = list(stances)
        self._conflicts = list(conflicts)
        self._compiled = compiled

    def __getattr__(self, name: str) -> Any:
        return getattr(self._base, name)

    def get_concept(self, concept_id: str) -> Concept | None:
        getter = getattr(self._base, "get_concept", None)
        if callable(getter):
            concept = cast(Callable[[str], Concept | None], getter)(concept_id)
            if concept is not None:
                return concept
        if not hasattr(self._base, "all_concepts"):
            return None
        for concept in self._base.all_concepts():
            if str(concept.concept_id) == concept_id or concept.canonical_name == concept_id:
                return concept
        return None

    def get_claim(self, claim_id: str) -> Claim | None:
        claim = self._claims_by_id.get(claim_id)
        if claim is not None:
            return claim
        base_get_claim = getattr(self._base, "get_claim", None)
        if not callable(base_get_claim):
            return None
        base_claim = cast(Callable[[str], Claim | None], base_get_claim)(claim_id)
        if base_claim is None:
            return None
        return self._claims_by_id.get(str(base_claim.id))

    def all_concepts(self) -> Sequence[Concept]:
        return list(self._base.all_concepts())

    def claims_for(self, concept_id: str | None) -> list[Claim]:
        if concept_id is None:
            return list(self._claims)
        concept = self.get_concept(concept_id)
        resolved_concept_id = str(concept.id) if concept is not None else concept_id
        return [
            claim
            for claim in self._claims
            if str(claim.value_concept_id or "") == resolved_concept_id
        ]

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, Claim]:
        return {
            claim_id: claim
            for claim_id, claim in self._claims_by_id.items()
            if claim_id in claim_ids
        }

    def stances_between(self, claim_ids: set[str]) -> Sequence[Stance]:
        return [
            stance
            for stance in self._stances
            if str(stance.claim_id) in claim_ids
            and str(stance.target_claim_id) in claim_ids
        ]

    def conflicts(self) -> Sequence[RelationConflictWitness]:
        return list(self._conflicts)

    def all_parameterizations(self) -> Sequence[Parameterization]:
        return list(self._base.all_parameterizations())

    def all_relationships(self) -> Sequence[ConceptRelation]:
        return list(self._base.all_relationships())

    def all_claim_stances(self) -> Sequence[Stance]:
        return list(self._stances)

    def all_micropublications(self) -> Sequence[Micropublication]:
        return list(self._base.all_micropublications())

    def concept_ids_for_group(self, group_id: int) -> set[str]:
        return set(self._base.concept_ids_for_group(group_id))

    def search(self, query: str) -> list[ConceptSearchHit]:
        return list(self._base.search(query))

    def similar_claims(
        self,
        claim_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[ClaimSimilarityHit]:
        return list(
            self._base.similar_claims(
                claim_id,
                model_name=model_name,
                top_k=top_k,
            )
        )

    def similar_concepts(
        self,
        concept_id: str,
        model_name: str | None = None,
        top_k: int = 10,
    ) -> list[ConceptSimilarityHit]:
        return list(
            self._base.similar_concepts(
                concept_id,
                model_name=model_name,
                top_k=top_k,
            )
        )

    def stats(self) -> WorldStoreStats:
        return self._base.stats()

    def parameterizations_for(self, concept_id: str) -> Sequence[Parameterization]:
        return list(self._base.parameterizations_for(concept_id))

    def explain(self, claim_id: str) -> list[Stance]:
        if claim_id not in self._claims_by_id:
            return []
        active_ids = set(self._claims_by_id)
        return [
            stance
            for stance in self._base.explain(claim_id)
            if str(stance.target_claim_id) in active_ids
        ]

    def compiled_graph(self) -> CompiledWorldGraph:
        if self._compiled is None:
            raise TypeError("compiled_graph() is unavailable for semantic-only overlays")
        return CompiledWorldGraph.from_dict(self._compiled.to_dict())

    def condition_solver(self):
        return self._base.condition_solver()

    def group_members(self, concept_id: str) -> list[str]:
        return list(self._base.group_members(concept_id))

    def chain_query(self, target_concept_id: str, strategy=None, **bindings: Any):
        return self._base.chain_query(
            target_concept_id,
            strategy=strategy,
            **bindings,
        )


class OverlayWorld(BeliefSpace):
    """Graph overlay, not intervention.

    An overlay world in which a synthetic claim asserting `X = x` is added;
    the existing parameterization graph is preserved and conflict resolution
    decides which claim wins. This is overlay semantics — not a Pearl intervention.
    For Pearl `do()` / Halpern HP-modified intervention, see `InterventionWorld`
    (WS-J2).
    """

    def __init__(
        self,
        base: BoundWorld,
        remove: list[str] | None = None,
        add: list[SyntheticClaim] | None = None,
    ) -> None:
        self._base = base

        def store_claim_id(claim_id: str) -> str:
            claim = base._store.get_claim(claim_id)
            return str(claim.id) if claim is not None else claim_id

        self._removed_ids = {
            store_claim_id(claim_id)
            for claim_id in (remove or [])
        }

        def resolve_synthetic_claim_id(claim_id: str) -> str:
            return store_claim_id(claim_id)

        def resolve_synthetic_concept_id(concept_id: ConceptId) -> ConceptId:
            concept = base._store.get_concept(str(concept_id))
            if concept is None:
                return concept_id
            return ConceptId(str(concept.id))

        self._synthetics = [
            replace(
                synthetic,
                id=resolve_synthetic_claim_id(synthetic.id),
                concept_id=resolve_synthetic_concept_id(synthetic.concept_id),
            )
            for synthetic in (add or [])
        ]

        cel_registry = base._store.condition_solver().registry
        base_claims = list(base._store.claims_for(None))
        base_claims_by_id = {
            str(claim.id): claim
            for claim in base_claims
        }
        synthetic_claims_by_id = {
            synthetic.id: synthetic_claim_to_claim(
                synthetic,
                existing_claim=base_claims_by_id.get(synthetic.id),
                cel_registry=cel_registry,
            )
            for synthetic in self._synthetics
        }

        self._base_compiled = _compiled_graph_for_bound(base)
        if self._base_compiled is not None:
            self._graph_delta = GraphDelta(
                add_claims=tuple(
                    claim_node_from_claim(claim)
                    for claim in synthetic_claims_by_id.values()
                ),
                remove_claim_ids=tuple(ClaimId(value) for value in self._removed_ids),
            )
            self._compiled_graph = self._graph_delta.apply(self._base_compiled)
        else:
            self._graph_delta = None
            self._compiled_graph = None

        synthetics_by_id = {synthetic.id: synthetic for synthetic in self._synthetics}

        overlay_claims: list[Claim] = []
        for claim in base_claims:
            claim_id = str(claim.id)
            replacement = synthetics_by_id.get(claim_id)
            if claim_id in self._removed_ids and replacement is None:
                continue
            if replacement is not None:
                overlay_claims.append(synthetic_claims_by_id[replacement.id])
            else:
                overlay_claims.append(claim)

        existing_ids = {str(claim.id) for claim in overlay_claims}
        for synthetic in self._synthetics:
            if synthetic.id in existing_ids:
                continue
            overlay_claims.append(synthetic_claims_by_id[synthetic.id])

        overlay_claim_ids = {
            str(claim.id)
            for claim in overlay_claims
        }
        overlay_stances = (
            [
                stance
                for stance in base._store.stances_between(overlay_claim_ids)
            ]
            if isinstance(base._store, StanceStore)
            else []
        )

        overlay_conflicts = [
            conflict
            for conflict in (
                conflict
                for conflict in base._store.conflicts()
            )
            if conflict.claim_a_id in overlay_claim_ids
            and conflict.claim_b_id in overlay_claim_ids
        ]
        seen_conflict_pairs = {
            _claim_pair(str(conflict.claim_a_id), str(conflict.claim_b_id))
            for conflict in overlay_conflicts
        }
        for conflict in _recomputed_conflicts(
            base._store,
            overlay_claims,
        ):
            pair = _claim_pair(str(conflict.claim_a_id), str(conflict.claim_b_id))
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
                conflicts=tuple(_conflict_witness_from_model(row) for row in overlay_conflicts),
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
                lifting_system=base._lifting_system,
            )
            if self._compiled_graph is not None
            else None
        )
        self._overlay = BoundWorld(
            self._overlay_store,
            environment=base._environment,
            lifting_system=base._lifting_system,
            policy=base._policy,
            active_graph=self._active_graph,
        )

    def active_claims(self, concept_id: str | None = None) -> list[Claim]:
        return self._overlay.active_claims(concept_id)

    def inactive_claims(self, concept_id: str | None = None) -> list[Claim]:
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

    def conflicts(self, concept_id: str | None = None) -> list[RelationConflictWitness]:
        return self._overlay.conflicts(concept_id)

    def explain(self, claim_id: str) -> list[Stance]:
        return self._overlay.explain(claim_id)

    def get_claim(self, claim_id: str) -> Claim | None:
        return self._overlay_store.get_claim(claim_id)

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, Claim]:
        return self._overlay_store.claims_by_ids(claim_ids)

    def stances_between(self, claim_ids: set[str]) -> Sequence[Stance]:
        return self._overlay_store.stances_between(claim_ids)

    def all_claim_stances(self) -> Sequence[Stance]:
        return self._overlay_store.all_claim_stances()

    def recompute_conflicts(self) -> list[RelationConflictWitness]:
        return _recomputed_conflicts(self._overlay_store, self.active_claims())

    def diff(self) -> dict[str, tuple[ValueResult, ValueResult]]:
        affected: set[str] = set()
        for synthetic in self._synthetics:
            affected.add(synthetic.concept_id)
        for claim_id in self._removed_ids:
            claim = self._base._store.get_claim(claim_id)
            if claim:
                if claim.value_concept_id is not None:
                    affected.add(str(claim.value_concept_id))

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
    return {
        numeric_payload.value
        for claim in vr.claims
        if (numeric_payload := claim.numeric_payload) is not None
        and numeric_payload.value is not None
    }
