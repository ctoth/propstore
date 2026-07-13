"""OverlayWorld — a graph-delta overlay over a :class:`BoundWorld`.

An overlay adds synthetic claims (and/or removes existing ones) on top of a bound
belief space, then lets the ordinary parameterization + conflict + resolution
machinery decide what the overlaid world looks like. This is *overlay semantics —
not a Pearl intervention*: the existing parameterization graph is preserved and
conflict resolution decides which claim wins, rather than severing a variable's
structural equation. For Pearl ``do()`` / Halpern HP-modified intervention use
:class:`~causal_models.InterventionWorld` (via :func:`propstore.world.model.intervene`).

Charter-native: the overlay materializes the merged belief set as ``Claim``
charters in an in-memory :class:`_GraphOverlayStore`, recompiles the world graph
from those charters, and constructs its own :class:`BoundWorld` over the overlay
store. There is no ``*RowInput`` second spelling — the overlay store returns the
same canonical charters and value types every other ``WorldStore`` does.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from condition_ir import (
    ConditionSolver,
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_to_json,
)

from propstore.conflict_detector import ConflictRecord
from propstore.core.active_claims import ActiveClaim
from propstore.core.environment import WorldStore
from propstore.core.activation import activate_compiled_world_graph
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.graph_types import CompiledWorldGraph
from propstore.core.id_types import ConceptId, to_concept_id
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.families.relations import Stance
from propstore.world.bound import BoundWorld, recomputed_conflicts
from propstore.world.types import (
    BeliefSpace,
    DerivedResult,
    ResolvedResult,
    SyntheticClaim,
    ValueResult,
)

if TYPE_CHECKING:
    from propstore.core.graph_types import ParameterizationEdge, RelationEdge
    from propstore.core.store_results import (
        ClaimSimilarityHit,
        ConceptSearchHit,
        ConceptSimilarityHit,
        WorldStoreStats,
    )
    from propstore.families.micropublications import Micropublication


def _value_concept_id(claim: Claim) -> str | None:
    for candidate in (claim.output_concept, claim.target_concept, *claim.concepts):
        if candidate:
            return str(candidate)
    return None


def _claim_pair(left_id: str, right_id: str) -> tuple[str, str]:
    left, right = sorted((str(left_id), str(right_id)))
    return left, right


def _conflict_key(record: ConflictRecord) -> tuple[str, str, str]:
    left, right = _claim_pair(str(record.claim_a_id), str(record.claim_b_id))
    return left, right, str(record.concept_id)


def _numeric_value(value: float | str | None) -> float | None:
    """The numeric value a ``Claim`` charter can carry.

    The ``Claim`` charter's ``value`` column is numeric; a categorical synthetic
    value has no charter column to ride on, so it does not flow through the
    overlay's value path (a pre-existing charter limitation, not an overlay one).
    """

    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


class _GraphOverlayStore:
    """An in-memory :class:`WorldStore` over a base store plus a claim overlay.

    Claims, stances, and conflicts come from the overlaid set the
    :class:`OverlayWorld` materialized; every other read delegates to the base
    store unchanged. Returns canonical charters and value types — no ``*RowInput``.
    """

    def __init__(
        self,
        base_store: WorldStore,
        *,
        claims: Sequence[Claim],
        stances: Sequence[Stance],
        conflicts: Sequence[ConflictRecord],
    ) -> None:
        self._base = base_store
        self._claims = tuple(claims)
        self._claims_by_id = {str(claim.claim_id): claim for claim in self._claims}
        self._stances = tuple(stances)
        self._conflicts = tuple(conflicts)

    # -- overlaid reads -----------------------------------------------------

    def get_claim(self, claim_id: str) -> Claim | None:
        resolved = self.resolve_claim(claim_id) or claim_id
        return self._claims_by_id.get(resolved)

    def claims_for(self, concept_id: str | None) -> Sequence[Claim]:
        if concept_id is None:
            return self._claims
        resolved = self.resolve_concept(concept_id) or concept_id
        return [
            claim for claim in self._claims if _value_concept_id(claim) == resolved
        ]

    def claims_by_ids(self, claim_ids: set[str]) -> Mapping[str, Claim]:
        return {
            claim_id: claim
            for claim_id, claim in self._claims_by_id.items()
            if claim_id in claim_ids
        }

    def stances_between(self, claim_ids: set[str]) -> Sequence[Stance]:
        return [
            stance
            for stance in self._stances
            if str(stance.source_claim_id) in claim_ids
            and str(stance.target_claim_id) in claim_ids
        ]

    def all_claim_stances(self) -> Sequence[Stance]:
        return self._stances

    def conflicts(self) -> Sequence[ConflictRecord]:
        return self._conflicts

    def explain(self, claim_id: str) -> Sequence[Stance]:
        if claim_id not in self._claims_by_id:
            return []
        active_ids = set(self._claims_by_id)
        return [
            stance
            for stance in self._base.explain(claim_id)
            if str(stance.target_claim_id) in active_ids
        ]

    # -- delegated reads ----------------------------------------------------

    def get_concept(self, concept_id: str) -> Concept | None:
        return self._base.get_concept(concept_id)

    def resolve_alias(self, alias: str) -> str | None:
        return self._base.resolve_alias(alias)

    def resolve_concept(self, name: str) -> str | None:
        return self._base.resolve_concept(name)

    def resolve_claim(self, name: str) -> str | None:
        return self._base.resolve_claim(name)

    def all_concepts(self) -> Sequence[Concept]:
        return self._base.all_concepts()

    def all_forms(self) -> Sequence[FormDefinition]:
        return self._base.all_forms()

    def all_parameterizations(self) -> Sequence[ParameterizationEdge]:
        return self._base.all_parameterizations()

    def all_relationships(self) -> Sequence[RelationEdge]:
        return self._base.all_relationships()

    def all_micropublications(self) -> Sequence[Micropublication]:
        return self._base.all_micropublications()

    def concept_ids_for_group(self, group_id: int) -> set[str]:
        return self._base.concept_ids_for_group(group_id)

    def search(self, query: str) -> list[ConceptSearchHit]:
        return self._base.search(query)

    def similar_claims(
        self, claim_id: str, model_name: str | None = None, top_k: int = 10
    ) -> list[ClaimSimilarityHit]:
        return self._base.similar_claims(claim_id, model_name=model_name, top_k=top_k)

    def similar_concepts(
        self, concept_id: str, model_name: str | None = None, top_k: int = 10
    ) -> list[ConceptSimilarityHit]:
        return self._base.similar_concepts(concept_id, model_name=model_name, top_k=top_k)

    def stats(self) -> WorldStoreStats:
        return self._base.stats()

    def condition_solver(self) -> ConditionSolver:
        return self._base.condition_solver()

    def parameterizations_for(self, concept_id: str) -> Sequence[ParameterizationEdge]:
        return self._base.parameterizations_for(concept_id)

    def group_members(self, concept_id: str) -> list[str]:
        return self._base.group_members(concept_id)

    def chain_query(
        self,
        target_concept_id: str,
        strategy: object | None = None,
        **bindings: object,
    ) -> object:
        return self._base.chain_query(target_concept_id, strategy, **bindings)


class OverlayWorld(BeliefSpace):
    """Graph overlay, not intervention.

    An overlay world in which a synthetic claim asserting ``X = x`` is added; the
    existing parameterization graph is preserved and conflict resolution decides
    which claim wins. This is overlay semantics — not a Pearl intervention. For
    Pearl ``do()`` / Halpern HP-modified intervention, see
    :class:`~causal_models.InterventionWorld`.
    """

    def __init__(
        self,
        base: BoundWorld,
        remove: Sequence[str] | None = None,
        add: Sequence[SyntheticClaim] | None = None,
    ) -> None:
        self._base = base
        base_store = base.store

        self._removed_ids = {
            base_store.resolve_claim(claim_id) or claim_id for claim_id in (remove or [])
        }
        solver = base_store.condition_solver()
        self._synthetics = [
            SyntheticClaim(
                id=base_store.resolve_claim(synthetic.id) or synthetic.id,
                concept_id=to_concept_id(
                    base_store.resolve_concept(str(synthetic.concept_id))
                    or synthetic.concept_id
                ),
                type=synthetic.type,
                value=synthetic.value,
                conditions=list(synthetic.conditions),
                sample_size=synthetic.sample_size,
                confidence=synthetic.confidence,
            )
            for synthetic in (add or [])
        ]
        synthetics_by_id = {synthetic.id: synthetic for synthetic in self._synthetics}

        overlay_claims: list[Claim] = []
        for claim in base_store.claims_for(None):
            claim_id = str(claim.claim_id)
            replacement = synthetics_by_id.get(claim_id)
            if claim_id in self._removed_ids and replacement is None:
                continue
            if replacement is not None:
                overlay_claims.append(
                    _synthetic_claim(replacement, existing=claim, solver=solver)
                )
            else:
                overlay_claims.append(claim)

        existing_ids = {str(claim.claim_id) for claim in overlay_claims}
        for synthetic in self._synthetics:
            if synthetic.id in existing_ids:
                continue
            overlay_claims.append(_synthetic_claim(synthetic, existing=None, solver=solver))

        overlay_claim_ids = {str(claim.claim_id) for claim in overlay_claims}
        overlay_stances = list(base_store.stances_between(overlay_claim_ids))

        overlay_conflicts: list[ConflictRecord] = [
            record
            for record in base_store.conflicts()
            if str(record.claim_a_id) in overlay_claim_ids
            and str(record.claim_b_id) in overlay_claim_ids
        ]
        seen = {_conflict_key(record) for record in overlay_conflicts}
        for record in recomputed_conflicts(
            base_store,
            overlay_claims,
            lifting_system=base.lifting_system,
        ):
            key = _conflict_key(record)
            if key in seen:
                continue
            overlay_conflicts.append(record)
            seen.add(key)

        self._overlay_store = _GraphOverlayStore(
            base_store,
            claims=overlay_claims,
            stances=overlay_stances,
            conflicts=overlay_conflicts,
        )
        self._compiled: CompiledWorldGraph = build_compiled_world_graph(self._overlay_store)
        active_graph = activate_compiled_world_graph(
            self._compiled,
            environment=base.environment,
            solver=base_store.condition_solver(),
            lifting_system=base.lifting_system,
        )
        self._overlay = BoundWorld(
            self._overlay_store,
            environment=base.environment,
            lifting_system=base.lifting_system,
            policy=base.policy,
            active_graph=active_graph,
        )

    @property
    def store(self) -> WorldStore:
        """The overlaid in-memory :class:`WorldStore` (base + synthetic claims).

        Mirrors :attr:`BoundWorld.store`; an argumentation framework over the
        hypothetical world is built from *this* store so synthetic claims (absent
        from the base store) participate.
        """

        return self._overlay_store

    # -- belief-space surface ----------------------------------------------

    def active_claims(self, concept_id: str | None = None) -> list[ActiveClaim]:
        return self._overlay.active_claims(concept_id)

    def inactive_claims(self, concept_id: str | None = None) -> list[ActiveClaim]:
        return self._overlay.inactive_claims(concept_id)

    def collect_known_values(
        self, variable_concepts: Sequence[ConceptId | str]
    ) -> dict[ConceptId, object]:
        return self._overlay.collect_known_values(variable_concepts)

    def value_of(self, concept_id: str) -> ValueResult:
        return self._overlay.value_of(concept_id)

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: Mapping[str, float | str | None] | None = None,
    ) -> DerivedResult:
        return self._overlay.derived_value(concept_id, override_values=override_values)

    def resolved_value(self, concept_id: str) -> ResolvedResult:
        return self._overlay.resolved_value(concept_id)

    def is_determined(self, concept_id: str) -> bool:
        return self._overlay.is_determined(concept_id)

    def conflicts(self, concept_id: str | None = None) -> list[ConflictRecord]:
        return self._overlay.conflicts(concept_id)

    def explain(self, claim_id: str) -> list[Stance]:
        return self._overlay.explain(claim_id)

    # -- overlay-specific surface ------------------------------------------

    def recompute_conflicts(self) -> list[ConflictRecord]:
        active_ids = {str(claim.claim_id) for claim in self.active_claims()}
        active_claims = [
            claim for claim in self._compiled.claims if claim.claim_id in active_ids
        ]
        return recomputed_conflicts(
            self._overlay_store,
            active_claims,
            lifting_system=self._base.lifting_system,
        )

    def diff(self) -> dict[str, tuple[ValueResult, ValueResult]]:
        affected: set[str] = set()
        for synthetic in self._synthetics:
            affected.add(str(synthetic.concept_id))
        for claim_id in self._removed_ids:
            claim = self._base.store.get_claim(claim_id)
            if claim is not None:
                concept_id = _value_concept_id(claim)
                if concept_id is not None:
                    affected.add(concept_id)

        result: dict[str, tuple[ValueResult, ValueResult]] = {}
        for concept_id in affected:
            base_result = self._base.value_of(concept_id)
            overlay_result = self.value_of(concept_id)
            if base_result.status is not overlay_result.status or _value_set(
                base_result
            ) != _value_set(overlay_result):
                result[concept_id] = (base_result, overlay_result)
        return result


def _synthetic_claim(
    synthetic: SyntheticClaim,
    *,
    existing: Claim | None,
    solver: ConditionSolver,
) -> Claim:
    """Materialize a synthetic overlay claim as a ``Claim`` charter."""

    is_measurement = synthetic.type is ClaimType.MEASUREMENT
    conditions = tuple(str(condition) for condition in synthetic.conditions)
    conditions_ir = _conditions_ir(conditions, solver)
    return Claim(
        claim_id=synthetic.id,
        context_id=existing.context_id if existing is not None else None,
        claim_type=synthetic.type,
        output_concept=(None if is_measurement else str(synthetic.concept_id)),
        target_concept=(
            str(synthetic.concept_id)
            if is_measurement
            else (existing.target_concept if existing is not None else None)
        ),
        value=_numeric_value(synthetic.value),
        conditions=conditions,
        conditions_ir=conditions_ir,
        sample_size=(
            synthetic.sample_size
            if synthetic.sample_size is not None
            else (existing.sample_size if existing is not None else None)
        ),
        confidence=synthetic.confidence,
    )


def _conditions_ir(conditions: Sequence[str], solver: ConditionSolver) -> str | None:
    if not conditions:
        return None
    registry = solver.registry
    return json.dumps(
        checked_condition_set_to_json(
            checked_condition_set(
                check_condition_ir(source, registry) for source in conditions
            )
        ),
        sort_keys=True,
    )


def _value_set(result: ValueResult) -> set[object]:
    return {
        value
        for claim in result.claims
        if (value := claim.value) is not None
    }
