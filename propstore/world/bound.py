"""BoundWorld — condition-bound view over a WorldQuery."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from propstore.core.conditions import checked_condition_set, checked_condition_set_from_json
from propstore.core.conditions.cel_frontend import check_condition_ir
from propstore.cel_types import CelExpr
from propstore.core.activation import is_claim_active
from propstore.families.claims.types import ClaimType
from propstore.core.environment import ConceptCatalogStore, WorldStore
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    ContextId,
)
from propstore.families.claims.declaration import Claim
from propstore.families.relations.declaration import (
    ConflictWitness,
    Stance,
)
from propstore.families.concepts.declaration import (
    Concept,
    Parameterization,
)
from propstore.core.labels import (
    AssumptionRef,
    EnvironmentKey,
    Label,
    SupportQuality,
    binding_condition_to_cel,
    combine_labels,
    merge_labels,
)
from propstore.world.value_resolver import ClaimValueResolver, collect_known_values
from propstore.world.conflict_projection import (
    ConflictDetectorInputs,
    WorldConflictProjectionStore,
    conflict_detector_inputs_for_world,
)
from propstore.world.types import (
    ATMSConceptInterventionPlan,
    ATMSConceptRelevanceReport,
    ATMSConceptStabilityReport,
    ATMSConceptWhyOutReport,
    ATMSLabelVerificationReport,
    ATMSNodeExplanation,
    ATMSNodeStatus,
    ATMSNogoodDetail,
    ATMSFutureStatusReport,
    ATMSInspection,
    ATMSNextQuerySuggestion,
    ATMSNodeInterventionPlan,
    ATMSNodeRelevanceReport,
    ATMSNodeStabilityReport,
    BeliefSpace,
    DerivedResult,
    Environment,
    QueryableAssumption,
    RenderPolicy,
    ResolutionStrategy,
    ResolvedResult,
    ValueStatus,
    ValueResult,
)
from propstore.support_revision.belief_set_adapter import (
    DEFAULT_ITERATED_OPERATOR,
    DEFAULT_MAX_ALPHABET_SIZE,
    decide_contract,
    decide_expand,
    decide_revise,
)
from propstore.support_revision.input_normalization import (
    RevisionInput,
    normalize_revision_input,
    normalize_revision_targets,
)
from propstore.support_revision.realization import realize_formal_decision

if TYPE_CHECKING:
    from propstore.core.graph_types import WorldActivationGraph
    from propstore.families.contexts.lifting import LiftingSystem
    from propstore.world.atms import ATMSEngine

@runtime_checkable
class _LiftingSystemLoader(Protocol):
    def _load_lifting_system(self) -> LiftingSystem | None: ...


def _recomputed_conflicts(
    world,
    claims: list[Claim],
    *,
    precomputed_inputs: ConflictDetectorInputs | None = None,
) -> list[ConflictWitness]:
    """Revalidate active conflicts against the live belief space.

    ``precomputed_inputs`` is an optional typed cache payload carrying the
    concept + CEL registry. When ``None`` (the default, used by overlay call
    sites in ``propstore.world.overlay``), the registry is rebuilt from
    ``world`` — this is the correct behavior for ``_GraphOverlayStore``,
    because overlay instances must not share cache state with the base
    ``BoundWorld._store``. ``BoundWorld.conflicts`` passes its own per-instance
    cached inputs through to skip the rebuild.
    """

    from propstore.conflict_detector import detect_conflicts
    from propstore.conflict_detector.collectors import conflict_claim_from_claim

    if len(claims) < 2:
        return []
    if not isinstance(world, WorldConflictProjectionStore):
        return []

    conflict_claims = [
        conflict_claim
        for active_claim in claims
        if (conflict_claim := conflict_claim_from_claim(active_claim)) is not None
    ]
    if precomputed_inputs is None:
        inputs = conflict_detector_inputs_for_world(world)
        concept_registry = inputs.concept_registry
        cel_registry = inputs.cel_registry
    else:
        concept_registry = precomputed_inputs.concept_registry
        cel_registry = precomputed_inputs.cel_registry
    lifting_system = (
        world._load_lifting_system()
        if isinstance(world, _LiftingSystemLoader)
        else None
    )
    records = detect_conflicts(
        conflict_claims,
        concept_registry,
        cel_registry,
        lifting_system=lifting_system,
    )
    return [
        ConflictWitness(
            concept_id=ConceptId(record.concept_id),
            claim_a_id=ClaimId(record.claim_a_id),
            claim_b_id=ClaimId(record.claim_b_id),
            warning_class=record.warning_class.value,
            conditions_a=json.dumps(record.conditions_a),
            conditions_b=json.dumps(record.conditions_b),
            value_a=record.value_a,
            value_b=record.value_b,
            derivation_chain=record.derivation_chain,
        )
        for record in records
    ]


class BoundWorld(BeliefSpace):
    """The world under specific condition bindings, optionally scoped to a context."""

    def __init__(
        self,
        world: WorldStore,
        bindings: Mapping[str, object] | None = None,
        context_id: str | None = None,
        lifting_system: LiftingSystem | None = None,
        *,
        environment: Environment | None = None,
        policy: RenderPolicy | None = None,
        active_graph: WorldActivationGraph | None = None,
    ) -> None:
        self._store = world
        if environment is None:
            environment_bindings = {} if bindings is None else bindings
            environment = Environment(
                bindings=environment_bindings,
                context_id=(None if context_id is None else ContextId(context_id)),
            )
        self._environment = environment
        self._policy = policy
        self._active_graph = active_graph
        self._active_claim_id_set = (
            self._normalize_claim_id_set(active_graph.active_claim_ids)
            if active_graph is not None
            else None
        )
        self._inactive_claim_id_set = (
            self._normalize_claim_id_set(active_graph.inactive_claim_ids)
            if active_graph is not None
            else None
        )
        self._atms_engine: ATMSEngine | None = None
        self._bindings = dict(environment.bindings)
        self._binding_conds = self._bindings_to_cel(self._bindings)
        self._assumptions_by_cel: dict[CelExpr, list[AssumptionRef]] = {}
        for assumption in environment.assumptions:
            self._assumptions_by_cel.setdefault(assumption.cel, []).append(assumption)
        for assumption in environment.effective_assumptions:
            if assumption not in self._binding_conds:
                self._binding_conds.append(assumption)
        self._context_id = environment.context_id
        self._lifting_system = lifting_system
        self._conflicts_cache: dict[str | None, list[ConflictWitness]] = {}
        # Typed per-instance memo of the concept + CEL registry used to
        # revalidate conflicts at render time. Built lazily on the first
        # `.conflicts()` call that misses `_conflicts_cache`. Safe to memoize
        # on the instance because `self._store` is set once in __init__ and
        # never rebound. MUST NOT be shared across BoundWorld instances —
        # OverlayWorld overlays construct their own BoundWorld over a
        # _GraphOverlayStore and rely on getting a fresh cache.
        self._conflict_inputs_cache: ConflictDetectorInputs | None = None
        self._resolver = ClaimValueResolver(
            parameterizations_for=lambda concept_id: list(
                self._store.parameterizations_for(str(concept_id))
            ),
            is_param_compatible=self.is_parameterization_compatible,
            value_of=self.value_of,
            extract_variable_concepts=self.extract_variable_concepts,
            collect_known_values=self.collect_known_values,
            extract_bindings=self.extract_bindings,
            concept_symbol_candidates=self._concept_symbol_candidates,
        )

    @property
    def environment(self) -> Environment:
        return self._environment

    @property
    def lifting_system(self) -> LiftingSystem | None:
        return self._lifting_system

    @property
    def active_graph(self) -> WorldActivationGraph | None:
        return self._active_graph

    @property
    def store(self) -> WorldStore:
        return self._store

    @property
    def policy(self) -> RenderPolicy | None:
        return self._policy

    def _normalize_claim_id_set(self, claim_ids: Sequence[str]) -> set[str]:
        return {str(claim_id) for claim_id in claim_ids}

    @staticmethod
    def _bindings_to_cel(bindings: Mapping[str, object]) -> list[CelExpr]:
        """Convert keyword bindings to CEL condition strings."""
        return [binding_condition_to_cel(key, value) for key, value in bindings.items()]

    def rebind(
        self,
        environment: Environment,
        *,
        policy: RenderPolicy | None = None,
    ) -> BoundWorld:
        """Create the same bound-world view over a new environment."""
        return self.__class__(
            self._store,
            environment=environment,
            lifting_system=self._lifting_system,
            policy=policy,
        )

    def is_active(self, claim: Claim) -> bool:
        """Check if a claim is active under the current bindings and context."""
        claim_id = str(claim.id)
        if self._active_claim_id_set is not None:
            if claim_id in self._active_claim_id_set:
                return True
            inactive_claim_ids = self._inactive_claim_id_set or set()
            if claim_id in inactive_claim_ids:
                return False

        try:
            solver = self._store.condition_solver()
        except AttributeError:
            solver = None

        return is_claim_active(
            claim_id=claim_id,
            claim_context_id=claim.context_id,
            claim_conditions=claim.checked_conditions,
            source_artifact=claim.source_slug or claim.id,
            environment=self._environment,
            solver=solver,
            lifting_system=self._lifting_system,
        )

    def is_param_compatible(self, parameterization: Parameterization) -> bool:
        return self.is_parameterization_compatible(parameterization)

    def is_parameterization_compatible(self, parameterization: Parameterization) -> bool:
        """Check if parameterization conditions are compatible with bindings."""
        if not parameterization.conditions_ir:
            if parameterization.conditions_cel:
                raise ValueError(
                    "parameterization row is missing conditions_ir; rebuild the sidecar"
                )
            return True
        loaded_conditions = json.loads(parameterization.conditions_ir)
        if not isinstance(loaded_conditions, Mapping):
            raise ValueError("parameterization conditions_ir must decode to a mapping")
        condition_set = checked_condition_set_from_json(loaded_conditions)
        if not condition_set.conditions:
            return True
        if not self._binding_conds:
            return True
        solver = self._store.condition_solver()
        registry = solver.registry
        return not solver.are_disjoint(
            checked_condition_set(
                check_condition_ir(str(condition), registry)
                for condition in self._binding_conds
            ),
            condition_set,
        )

    def active_claims(self, concept_id: str | None = None) -> list[Claim]:
        all_claims = list(self._store.claims_for(concept_id))
        if self._active_claim_id_set is not None:
            return [
                claim for claim in all_claims
                if str(claim.id) in self._active_claim_id_set
            ]
        return [c for c in all_claims if self.is_active(c)]

    def inactive_claims(self, concept_id: str | None = None) -> list[Claim]:
        all_claims = list(self._store.claims_for(concept_id))
        if self._inactive_claim_id_set is not None:
            return [
                claim for claim in all_claims
                if str(claim.id) in self._inactive_claim_id_set
            ]
        return [c for c in all_claims if not self.is_active(c)]

    def algorithm_for(self, concept_id: str) -> list[Claim]:
        """Return all active algorithm claims relevant to the given concept."""
        active = self.active_claims(concept_id)
        return [c for c in active if c.type is ClaimType.ALGORITHM]

    def _concept_symbol_candidates(self, concept_id: ConceptId | str) -> list[str]:
        candidates: list[str] = []
        concept_row = self._store.get_concept(str(concept_id))
        if concept_row is None:
            for row in self._store.all_concepts():
                if (
                    str(row.concept_id) == str(concept_id)
                    or row.canonical_name == str(concept_id)
                ):
                    concept_row = row
                    break
        if concept_row is None:
            return candidates

        seen: set[str] = set()

        def add(candidate: object) -> None:
            if not isinstance(candidate, str) or not candidate:
                return
            if candidate in seen:
                return
            seen.add(candidate)
            candidates.append(candidate)

        add(concept_row.canonical_name)
        logical_ids = concept_row.parsed_logical_ids()
        if isinstance(logical_ids, list):
            for entry in logical_ids:
                if not isinstance(entry, dict):
                    continue
                add(entry.get("value"))
                namespace = entry.get("namespace")
                value = entry.get("value")
                if isinstance(namespace, str) and isinstance(value, str) and namespace and value:
                    add(f"{namespace}:{value}")
        return candidates

    def collect_known_values(
        self,
        variable_concepts: Sequence[ConceptId | str],
    ) -> dict[ConceptId, float]:
        """Resolve numeric values for a list of concept IDs."""
        return collect_known_values(variable_concepts, self.value_of)

    def extract_variable_concepts(self, claim: Claim) -> list[str]:
        """Extract concept IDs referenced by an algorithm claim's variables."""
        return list(claim.variable_concept_ids())

    def extract_bindings(self, claim: Claim) -> dict[str, str]:
        """Extract variable name -> concept mapping from an algorithm claim."""
        return claim.variable_bindings()

    def value_of(self, concept_id: str) -> ValueResult:
        active = self.active_claims(concept_id)
        if self._reasoning_backend() == "atms":
            supported_ids = self.atms_engine().supported_claim_ids(concept_id)
            active = [
                claim for claim in active
                if str(claim.id) in supported_ids
            ]
        result = self._resolver.value_of_from_active(active, concept_id)
        if self._reasoning_backend() == "atms":
            return self._attach_atms_value_label(result)
        return self._attach_value_label(result)

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: Mapping[str, float | str | None] | None = None,
    ) -> DerivedResult:
        """Derive a value for concept_id via parameterization relationships."""
        normalized_override_values = self._normalize_override_values(override_values)
        result = self._resolver.derived_value(
            concept_id,
            override_values=normalized_override_values,
        )
        if self._reasoning_backend() == "atms":
            return self._attach_atms_derived_label(result)
        return self._attach_derived_label(result, override_values=normalized_override_values)

    def resolved_value(
        self,
        concept_id: str,
        *,
        strategy: ResolutionStrategy | None = None,
        policy: RenderPolicy | None = None,
    ) -> ResolvedResult:
        from propstore.world.resolution import resolve

        effective_policy = policy or self._policy
        result = resolve(
            self, concept_id,
            strategy=strategy,
            policy=effective_policy,
            world=self._store,
        )
        if self._reasoning_backend() == "atms":
            return self._attach_atms_resolved_label(concept_id, result)
        return self._attach_resolved_label(concept_id, result)

    def atms_engine(self):
        if self._atms_engine is None:
            from propstore.world.atms import ATMSEngine

            self._atms_engine = ATMSEngine(self)
        return self._atms_engine

    def revision_base(self):
        """Project this bound world into a revision-facing belief base."""
        from propstore.support_revision.projection import project_belief_base

        return project_belief_base(self)

    def revision_entrenchment(self, *, overrides: Mapping[str, Mapping[str, object]] | None = None):
        """Compute the current revision-facing entrenchment ordering."""
        from propstore.support_revision.entrenchment import compute_entrenchment

        return compute_entrenchment(self, self.revision_base(), overrides=overrides)

    def expand(self, atom):
        """Expand the scoped revision belief base without mutating source storage."""
        base = self.revision_base()
        normalized = normalize_revision_input(base, atom)
        decision = decide_expand(
            base,
            normalized,
            max_alphabet_size=DEFAULT_MAX_ALPHABET_SIZE,
        )
        return realize_formal_decision(
            base,
            decision,
            extra_atoms=(normalized,),
            accepted_reason="expanded",
        )

    def contract(
        self,
        targets: RevisionInput | Sequence[RevisionInput],
        *,
        max_candidates: int,
        overrides: Mapping[str, Mapping[str, object]] | None = None,
    ):
        """Contract the scoped revision belief base using the current entrenchment."""
        base = self.revision_base()
        target_ids = normalize_revision_targets(base, targets)
        decision = decide_contract(
            base,
            target_ids,
            max_alphabet_size=DEFAULT_MAX_ALPHABET_SIZE,
        )
        return realize_formal_decision(
            base,
            decision,
            rejected_reason="contracted",
            support_entrenchment=self.revision_entrenchment(overrides=overrides),
            max_candidates=max_candidates,
        )

    def revise(
        self,
        atom,
        *,
        max_candidates: int,
        overrides: Mapping[str, Mapping[str, object]] | None = None,
        conflicts: Mapping[str, Sequence[str]] | None = None,
    ):
        """Revise the scoped belief base by delegating to the revision package."""
        base = self.revision_base()
        normalized = normalize_revision_input(base, atom)
        decision = decide_revise(
            base,
            normalized,
            conflicts=(
                ()
                if conflicts is None
                else tuple(str(conflict) for conflict in conflicts.get(normalized.atom_id, ()))
            ),
            max_alphabet_size=DEFAULT_MAX_ALPHABET_SIZE,
        )
        return realize_formal_decision(
            base,
            decision,
            extra_atoms=(normalized,),
            accepted_reason="revised_in",
            rejected_reason="revised_out",
            support_entrenchment=self.revision_entrenchment(overrides=overrides),
            max_candidates=max_candidates,
        )

    def revision_explain(
        self,
        result,
        *,
        overrides: Mapping[str, Mapping[str, object]] | None = None,
    ):
        """Render the default explanation payload for a revision result."""
        from propstore.support_revision.explain import build_revision_explanation

        return build_revision_explanation(
            result,
            entrenchment=self.revision_entrenchment(overrides=overrides),
        )

    def epistemic_state(
        self,
        *,
        overrides: Mapping[str, Mapping[str, object]] | None = None,
    ):
        """Build the explicit iterated revision state for this scoped world."""
        from propstore.support_revision.iterated import make_epistemic_state

        return make_epistemic_state(
            self.revision_base(),
            self.revision_entrenchment(overrides=overrides),
        )

    def revision_state_snapshot(self, state):
        """Render an iterated revision state as the worldline persistence payload."""
        from propstore.support_revision.history import EpistemicSnapshot

        return EpistemicSnapshot.from_state(state)

    def iterated_revise(
        self,
        atom,
        *,
        max_candidates: int,
        overrides: Mapping[str, Mapping[str, object]] | None = None,
        conflicts: Mapping[str, Sequence[str]] | None = None,
        operator: str = DEFAULT_ITERATED_OPERATOR,
        state=None,
    ):
        """Revise an explicit epistemic state using the selected iterated operator."""
        from propstore.support_revision.iterated import iterated_revise as iterated_revise_state

        current_state = state or self.epistemic_state(overrides=overrides)
        return iterated_revise_state(
            current_state,
            atom,
            max_candidates=max_candidates,
            conflicts=None if conflicts is None else dict(conflicts),
            operator=operator,
        )

    def claim_status(self, claim_id: str) -> ATMSInspection:
        """Return the ATMS-native status and support-quality metadata for a claim."""
        return self.atms_engine().claim_status(claim_id)

    def claim_essential_support(self, claim_id: str) -> EnvironmentKey | None:
        """Return Dixon-style essential support for a claim under this bound world."""
        return self.claim_status(claim_id).essential_support

    def claim_future_statuses(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        *,
        limit: int | None,
    ) -> ATMSFutureStatusReport:
        """Return bounded future-environment status changes for one claim."""
        self._require_atms_backend()
        return self.atms_engine().claim_future_statuses(
            claim_id,
            queryables,
            limit=limit,
        )
    def concept_future_statuses(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        *,
        limit: int | None,
    ) -> dict[str, ATMSFutureStatusReport]:
        """Return bounded future-environment status changes for active claims of a concept."""
        self._require_atms_backend()
        return {
            str(claim.id): self.atms_engine().claim_future_statuses(
                str(claim.id),
                queryables,
                limit=limit,
            )
            for claim in sorted(self.active_claims(concept_id), key=lambda row: str(row.id))
        }
    def claim_stability(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        *,
        limit: int | None,
    ) -> ATMSNodeStabilityReport:
        """Return bounded ATMS stability for one claim over replayed future worlds."""
        self._require_atms_backend()
        return self.atms_engine().claim_stability(
            claim_id,
            queryables,
            limit=limit,
        )
    def claim_is_stable(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        *,
        limit: int | None,
    ) -> bool:
        """Whether a claim keeps the same ATMS status in all bounded consistent futures."""
        self._require_atms_backend()
        return self.atms_engine().claim_is_stable(
            claim_id,
            queryables,
            limit=limit,
        )
    def concept_stability(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        *,
        limit: int | None,
    ) -> ATMSConceptStabilityReport:
        """Return bounded value-status stability for one concept over replayed future worlds."""
        self._require_atms_backend()
        return self.atms_engine().concept_stability(
            concept_id,
            queryables,
            limit=limit,
        )
    def concept_is_stable(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        *,
        limit: int | None,
    ) -> bool:
        """Whether a concept keeps the same value status in all bounded consistent futures."""
        self._require_atms_backend()
        return self.atms_engine().concept_is_stable(
            concept_id,
            queryables,
            limit=limit,
        )
    def claim_relevance(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        *,
        limit: int | None,
    ) -> ATMSNodeRelevanceReport:
        """Return which bounded queryables can flip a claim's ATMS status."""
        self._require_atms_backend()
        return self.atms_engine().claim_relevance(
            claim_id,
            queryables,
            limit=limit,
        )
    def claim_relevant_queryables(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        *,
        limit: int | None,
    ) -> list[str]:
        """Return the bounded queryables that matter to a claim's ATMS status."""
        self._require_atms_backend()
        return self.atms_engine().claim_relevant_queryables(
            claim_id,
            queryables,
            limit=limit,
        )
    def concept_relevance(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        *,
        limit: int | None,
    ) -> ATMSConceptRelevanceReport:
        """Return which bounded queryables can flip a concept's value status."""
        self._require_atms_backend()
        return self.atms_engine().concept_relevance(
            concept_id,
            queryables,
            limit=limit,
        )
    def concept_relevant_queryables(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        *,
        limit: int | None,
    ) -> list[str]:
        """Return the bounded queryables that matter to a concept's value status."""
        self._require_atms_backend()
        return self.atms_engine().concept_relevant_queryables(
            concept_id,
            queryables,
            limit=limit,
        )
    def claim_interventions(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        target_status: ATMSNodeStatus,
        *,
        limit: int | None,
        max_plans: int | None = None,
    ) -> list[ATMSNodeInterventionPlan]:
        """Return bounded additive intervention plans for one claim."""
        self._require_atms_backend()
        return self.atms_engine().claim_interventions(
            claim_id,
            queryables,
            target_status,
            limit=limit,
            max_plans=max_plans,
        )

    def concept_interventions(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        target_value_status: ValueStatus,
        *,
        limit: int | None,
        max_plans: int | None = None,
    ) -> list[ATMSConceptInterventionPlan]:
        """Return bounded additive intervention plans for one concept."""
        self._require_atms_backend()
        return self.atms_engine().concept_interventions(
            concept_id,
            queryables,
            target_value_status,
            limit=limit,
            max_plans=max_plans,
        )

    def claim_next_queryables(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        target_status: ATMSNodeStatus,
        *,
        limit: int | None,
        max_suggestions: int | None = None,
    ) -> list[ATMSNextQuerySuggestion]:
        """Return bounded next-query suggestions derived from claim intervention plans."""
        self._require_atms_backend()
        return self.atms_engine().next_queryables_for_claim(
            claim_id,
            queryables,
            target_status,
            limit=limit,
            max_suggestions=max_suggestions,
        )

    def concept_next_queryables(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        target_value_status: ValueStatus,
        *,
        limit: int | None,
        max_suggestions: int | None = None,
    ) -> list[ATMSNextQuerySuggestion]:
        """Return bounded next-query suggestions derived from concept intervention plans."""
        self._require_atms_backend()
        return self.atms_engine().next_queryables_for_concept(
            concept_id,
            queryables,
            target_value_status,
            limit=limit,
            max_suggestions=max_suggestions,
        )

    def why_concept_out(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption] | None = None,
        *,
        limit: int | None,
    ) -> ATMSConceptWhyOutReport:
        """Explain why a concept currently lacks exact ATMS support."""
        self._require_atms_backend()
        supported_ids = self.atms_engine().supported_claim_ids(concept_id)
        claim_reasons = {
            str(claim.id): self.atms_engine().why_out(
                self.claim_status(str(claim.id)).node_id,
                queryables=queryables,
                limit=limit,
            )
            for claim in sorted(self.active_claims(concept_id), key=lambda row: str(row.id))
        }
        return ATMSConceptWhyOutReport(
            concept_id=concept_id,
            value_status=self.value_of(concept_id).status,
            supported_claim_ids=tuple(sorted(supported_ids)),
            claim_reasons=claim_reasons,
        )

    def explain_nogood(
        self,
        environment: EnvironmentKey,
    ) -> ATMSNogoodDetail | None:
        return self.atms_engine().explain_nogood(environment)

    def verify_atms_labels(self) -> ATMSLabelVerificationReport:
        self._require_atms_backend()
        return self.atms_engine().verify_labels()

    def claims_in_environment(
        self,
        environment: EnvironmentKey,
    ) -> list[str]:
        """Return assertion IDs whose exact ATMS support is visible inside the environment."""
        return [
            node_id
            for node_id in self.atms_engine().nodes_in_environment(environment)
            if node_id.startswith("ps:assertion:")
        ]

    def explain_claim_support(self, claim_id: str) -> ATMSNodeExplanation:
        """Return the ATMS justification trace and support metadata for a claim."""
        return self.atms_engine().explain_node(self.claim_status(claim_id).node_id)

    def claim_support(self, claim: Claim) -> tuple[Label | None, SupportQuality]:
        """Return exact label support when reconstructible, plus honesty metadata."""
        label = self._claim_support_label(claim)
        if label is not None:
            return label, SupportQuality.EXACT
        return None, self._support_quality(claim)

    def is_determined(self, concept_id: str) -> bool:
        return self.value_of(concept_id).status is ValueStatus.DETERMINED

    def _get_or_build_conflict_inputs(self) -> ConflictDetectorInputs:
        """Return the cached concept + CEL registry, building it on first miss.

        The registry iterates every concept in the store, so rebuilding it on
        every `.conflicts()` call with a new concept id was O(|concepts|) of
        wasted work. Memoized here because `self._store` is immutable for the
        lifetime of the BoundWorld. Must NOT be called against an overlay
        store — OverlayWorld overlays construct their own BoundWorld
        and reach this helper through their own instance.
        """
        if self._conflict_inputs_cache is None:
            self._conflict_inputs_cache = conflict_detector_inputs_for_world(self._store)
        return self._conflict_inputs_cache

    def conflicts(self, concept_id: str | None = None) -> list[ConflictWitness]:
        """Return active conflicts, revalidated against the current belief space."""
        concept = (
            self._store.get_concept(concept_id)
            if concept_id is not None and isinstance(self._store, ConceptCatalogStore)
            else None
        )
        resolved_concept_id = (
            None
            if concept_id is None
            else str(concept.id) if concept is not None else concept_id
        )
        if resolved_concept_id in self._conflicts_cache:
            return self._conflicts_cache[resolved_concept_id]
        active_claims = self.active_claims(resolved_concept_id)
        if len(active_claims) < 2:
            self._conflicts_cache[resolved_concept_id] = []
            return []
        active_ids = {str(claim.id) for claim in active_claims}

        result: list[ConflictWitness] = []
        all_conflicts = list(self._store.conflicts())
        for conflict in all_conflicts:
            if conflict.claim_a_id in active_ids and conflict.claim_b_id in active_ids:
                if resolved_concept_id is None or conflict.concept_id == resolved_concept_id:
                    result.append(conflict)
        seen = {
            (str(conflict.claim_a_id), str(conflict.claim_b_id), str(conflict.concept_id) if conflict.concept_id is not None else None)
            for conflict in result
        }
        if not isinstance(self._store, ConceptCatalogStore):
            self._conflicts_cache[resolved_concept_id] = result
            return result
        precomputed = self._get_or_build_conflict_inputs()
        for conflict in _recomputed_conflicts(
            self._store,
            active_claims,
            precomputed_inputs=precomputed,
        ):
            concept_key = str(conflict.concept_id) if conflict.concept_id is not None else None
            key = (str(conflict.claim_a_id), str(conflict.claim_b_id), concept_key)
            reverse_key = (str(conflict.claim_b_id), str(conflict.claim_a_id), concept_key)
            if key not in seen and reverse_key not in seen:
                result.append(conflict)
                seen.add(key)
        self._conflicts_cache[resolved_concept_id] = result
        return result

    def explain(self, claim_id: str) -> list[Stance]:
        """Stance walk filtered to active claims."""
        claim = self._store.get_claim(claim_id)
        if claim is None or not self.is_active(claim):
            return []

        full_chain = self._store.explain(claim_id)
        result: list[Stance] = []
        for stance in full_chain:
            target = self._store.get_claim(stance.target_claim_id)
            if target is not None and self.is_active(target):
                result.append(stance)
        return result

    def _attach_value_label(self, result: ValueResult) -> ValueResult:
        if result.status is not ValueStatus.DETERMINED or not result.claims:
            return result

        claim_labels: list[Label] = []
        for claim in result.claims:
            claim_label = self._claim_support_label(claim)
            if claim_label is None:
                return result
            claim_labels.append(claim_label)
        return replace(result, label=merge_labels(claim_labels))

    def _normalize_override_values(
        self,
        override_values: Mapping[str, float | str | None] | None,
    ) -> Mapping[str, float | str | None] | None:
        if override_values is None:
            return None

        normalized: dict[str, float | str | None] = {}
        for key, value in override_values.items():
            concept = self._store.get_concept(key)
            resolved_key = str(concept.id) if concept is not None else key
            normalized[resolved_key] = value
        return normalized

    def _attach_atms_value_label(self, result: ValueResult) -> ValueResult:
        if result.status is not ValueStatus.DETERMINED or not result.claims:
            return result

        engine = self.atms_engine()
        claim_labels: list[Label] = []
        for claim in result.claims:
            claim_id = str(claim.id)
            claim_label = engine.claim_label(claim_id)
            if claim_label is None:
                return result
            claim_labels.append(claim_label)
        return replace(result, label=merge_labels(claim_labels, nogoods=engine.nogoods))

    def _attach_derived_label(
        self,
        result: DerivedResult,
        *,
        override_values: Mapping[str, float | str | None] | None,
    ) -> DerivedResult:
        if result.status is not ValueStatus.DERIVED:
            return result

        input_labels: list[Label] = []
        for input_id in result.input_values:
            input_label = self._label_for_input(
                input_id,
                override_values=override_values,
                seen={result.concept_id},
            )
            if input_label is None:
                return result
            input_labels.append(input_label)
        return replace(result, label=combine_labels(*input_labels))

    def _attach_atms_derived_label(self, result: DerivedResult) -> DerivedResult:
        if result.status is not ValueStatus.DERIVED or result.value is None:
            return result

        label = self.atms_engine().derived_label(result.concept_id, result.value)
        if label is None:
            return result
        return replace(result, label=label)

    def _attach_resolved_label(
        self,
        concept_id: str,
        result: ResolvedResult,
    ) -> ResolvedResult:
        if result.status is ValueStatus.DETERMINED:
            return replace(result, label=self.value_of(concept_id).label)

        if result.status is not ValueStatus.RESOLVED or not result.winning_claim_id:
            return result

        winning_claim = next(
            (claim for claim in result.claims if str(claim.id) == result.winning_claim_id),
            None,
        )
        if winning_claim is None:
            return result

        claim_label = self._claim_support_label(winning_claim)
        if claim_label is None:
            return result
        return replace(result, label=claim_label)

    def _attach_atms_resolved_label(
        self,
        concept_id: str,
        result: ResolvedResult,
    ) -> ResolvedResult:
        if result.status is ValueStatus.DETERMINED:
            return replace(result, label=self.value_of(concept_id).label)

        if result.status is not ValueStatus.RESOLVED or not result.winning_claim_id:
            return result

        label = self.atms_engine().claim_label(result.winning_claim_id)
        if label is None:
            return result
        return replace(result, label=label)

    def _label_for_input(
        self,
        concept_id: str,
        *,
        override_values: Mapping[str, float | str | None] | None,
        seen: set[str],
    ) -> Label | None:
        if override_values and concept_id in override_values:
            return None

        value_result = self.value_of(concept_id)
        if value_result.status is ValueStatus.DETERMINED:
            return value_result.label

        if concept_id in seen:
            return None

        seen.add(concept_id)
        try:
            derived = self.derived_value(concept_id, override_values=override_values)
        finally:
            seen.discard(concept_id)
        if derived.status is ValueStatus.DERIVED:
            return derived.label
        return None

    def _claim_support_label(self, claim: Claim) -> Label | None:
        # Labels are only attached when the active support can be reconstructed
        # exactly from compiled assumptions and context labels.
        labels: list[Label] = []
        if claim.context_id is not None:
            labels.append(Label.context(claim.context_id))

        if not claim.conditions:
            return combine_labels(*labels) if labels else Label.empty()

        for condition in claim.conditions:
            matches = self._assumptions_by_cel.get(condition)
            if not matches:
                return None
            labels.append(
                Label(
                    tuple(
                        EnvironmentKey((assumption.assumption_id,))
                        for assumption in matches
                    )
                )
            )
        return combine_labels(*labels)

    def _support_quality(self, claim: Claim) -> SupportQuality:
        has_conditions = bool(claim.conditions)
        has_context = claim.context_id is not None
        if has_context and has_conditions:
            return SupportQuality.MIXED
        if has_context:
            return SupportQuality.CONTEXT_VISIBLE_ONLY
        if has_conditions:
            return SupportQuality.SEMANTIC_COMPATIBLE
        return SupportQuality.SEMANTIC_COMPATIBLE

    def _reasoning_backend(self) -> str:
        if self._policy is None:
            return "claim_graph"
        return self._policy.reasoning_backend.value

    def _require_atms_backend(self) -> None:
        if self._reasoning_backend() != "atms":
            raise ValueError("Future ATMS analysis requires backend='atms'")
