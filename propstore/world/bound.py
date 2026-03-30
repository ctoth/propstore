"""BoundWorld — condition-bound view over a WorldModel."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from propstore.core.activation import is_claim_mapping_active
from propstore.core.environment import ArtifactStore
from propstore.core.id_types import ConceptId, to_context_id
from propstore.core.row_types import coerce_conflict_row, coerce_parameterization_row
from propstore.world.labelled import (
    AssumptionRef,
    EnvironmentKey,
    Label,
    SupportQuality,
    binding_condition_to_cel,
    combine_labels,
    merge_labels,
)
from propstore.world.value_resolver import ActiveClaimResolver, collect_known_values
from propstore.world.types import (
    ATMSConceptInterventionPlan,
    ATMSConceptRelevanceReport,
    ATMSConceptStabilityReport,
    ATMSLabelVerificationReport,
    ATMSNodeExplanation,
    ATMSNogoodDetail,
    ATMSFutureStatusReport,
    ATMSInspection,
    ATMSNextQuerySuggestion,
    ATMSNodeInterventionPlan,
    ATMSNodeRelevanceReport,
    ATMSNodeStabilityReport,
    BeliefSpace,
    QueryableInput,
    DerivedResult,
    Environment,
    QueryableAssumption,
    RenderPolicy,
    ResolutionStrategy,
    ResolvedResult,
    ValueResult,
    coerce_queryable_assumptions,
)

if TYPE_CHECKING:
    from propstore.core.graph_types import ActiveWorldGraph
    from propstore.fragility import FragilityReport
    from propstore.validate_contexts import ContextHierarchy
    from propstore.world.atms import ATMSEngine

@runtime_checkable
class _ContextHierarchyLoader(Protocol):
    def _load_context_hierarchy(self) -> ContextHierarchy | None: ...


def _concept_registry_for_store(world) -> dict[str, dict]:
    registry: dict[str, dict] = {}
    for concept in world.all_concepts():
        cdata = dict(concept)
        cid = cdata["id"]
        form_parameters = cdata.get("form_parameters")
        if isinstance(form_parameters, str):
            try:
                cdata["form_parameters"] = json.loads(form_parameters)
            except json.JSONDecodeError:
                cdata["form_parameters"] = {}
        params = world.parameterizations_for(cid)
        if params:
            cdata["parameterization_relationships"] = []
            for param_input in params:
                param = coerce_parameterization_row(param_input)
                cdata["parameterization_relationships"].append({
                    "inputs": json.loads(param.concept_ids),
                    "sympy": param.sympy,
                    "exactness": param.exactness,
                    "conditions": (
                        json.loads(param.conditions_cel)
                        if param.conditions_cel
                        else []
                    ),
                })
        registry[cid] = cdata
    return registry


def _claim_row_to_source_claim(claim: dict) -> dict:
    source = dict(claim)
    if claim.get("conditions_cel"):
        source["conditions"] = json.loads(claim["conditions_cel"])
    else:
        source["conditions"] = []

    claim_type = claim.get("type")
    if claim_type == "parameter" and claim.get("concept_id"):
        source["concept"] = claim["concept_id"]
    if claim_type == "measurement" and claim.get("concept_id") and not claim.get("target_concept"):
        source["target_concept"] = claim["concept_id"]
    if claim_type == "algorithm" and claim.get("concept_id"):
        source["concept"] = claim["concept_id"]
    if claim_type == "algorithm" and claim.get("variables_json"):
        source["variables"] = json.loads(claim["variables_json"])
    return source


def _recomputed_conflicts(world, claims: list[dict]) -> list[dict]:
    from propstore.conflict_detector import detect_conflicts
    from propstore.validate_claims import LoadedClaimFile

    if len(claims) < 2:
        return []

    synthetic = LoadedClaimFile(
        filename="<render>",
        filepath=Path("<render>"),
        data={"claims": [_claim_row_to_source_claim(claim) for claim in claims]},
    )
    concept_registry = _concept_registry_for_store(world)
    context_hierarchy = (
        world._load_context_hierarchy()
        if isinstance(world, _ContextHierarchyLoader)
        else None
    )
    records = detect_conflicts(
        [synthetic],
        concept_registry,
        context_hierarchy=context_hierarchy,
    )
    return [
        {
            "concept_id": record.concept_id,
            "claim_a_id": record.claim_a_id,
            "claim_b_id": record.claim_b_id,
            "warning_class": record.warning_class.value,
            "conditions_a": record.conditions_a,
            "conditions_b": record.conditions_b,
            "value_a": record.value_a,
            "value_b": record.value_b,
            "derivation_chain": record.derivation_chain,
        }
        for record in records
    ]


class BoundWorld(BeliefSpace):
    """The world under specific condition bindings, optionally scoped to a context."""

    def __init__(
        self,
        world: ArtifactStore,
        bindings: dict[str, Any] | None = None,
        context_id: str | None = None,
        context_hierarchy: ContextHierarchy | None = None,
        *,
        environment: Environment | None = None,
        policy: RenderPolicy | None = None,
        active_graph: ActiveWorldGraph | None = None,
    ) -> None:
        self._store = world
        if environment is None:
            environment = Environment(
                bindings=bindings or {},
                context_id=(None if context_id is None else to_context_id(context_id)),
            )
        self._environment = environment
        self._policy = policy
        self._active_graph = active_graph
        self._active_claim_id_set = (
            set(active_graph.active_claim_ids) if active_graph is not None else None
        )
        self._inactive_claim_id_set = (
            set(active_graph.inactive_claim_ids) if active_graph is not None else None
        )
        self._atms_engine: ATMSEngine | None = None
        self._bindings = dict(environment.bindings)
        self._binding_conds = self._bindings_to_cel(self._bindings)
        self._assumptions_by_cel: dict[str, list[AssumptionRef]] = {}
        for assumption in environment.assumptions:
            self._assumptions_by_cel.setdefault(assumption.cel, []).append(assumption)
        for assumption in environment.effective_assumptions:
            if assumption not in self._binding_conds:
                self._binding_conds.append(assumption)
        self._context_id = environment.context_id
        self._context_hierarchy = context_hierarchy
        # Pre-compute ancestor set for fast lookups
        if self._context_id and context_hierarchy is not None:
            self._context_visible: set[str] | None = {self._context_id}
            for ancestor in context_hierarchy.ancestors(self._context_id):
                self._context_visible.add(ancestor)
        else:
            self._context_visible = None  # no context filtering
        self._conflicts_cache: dict[str | None, list[dict]] = {}
        self._resolver = ActiveClaimResolver(
            parameterizations_for=lambda concept_id: [
                coerce_parameterization_row(row)
                for row in self._store.parameterizations_for(concept_id)
            ],
            is_param_compatible=self.is_param_compatible,
            value_of=self.value_of,
            extract_variable_concepts=self.extract_variable_concepts,
            collect_known_values=self.collect_known_values,
            extract_bindings=self.extract_bindings,
        )

    @staticmethod
    def _bindings_to_cel(bindings: dict[str, Any]) -> list[str]:
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
            context_hierarchy=self._context_hierarchy,
            policy=policy,
        )

    def is_active(self, claim: dict) -> bool:
        """Check if a claim is active under the current bindings and context."""
        claim_id = claim.get("id")
        if claim_id is not None and self._active_claim_id_set is not None:
            if claim_id in self._active_claim_id_set:
                return True
            if claim_id in self._inactive_claim_id_set:
                return False

        try:
            solver = self._store.condition_solver()
        except AttributeError:
            solver = None

        return is_claim_mapping_active(
            claim,
            environment=self._environment,
            solver=solver,
            context_hierarchy=self._context_hierarchy,
        )

    def is_param_compatible(self, conditions_cel: str | None) -> bool:
        """Check if parameterization conditions are compatible with bindings."""
        if not conditions_cel:
            return True
        conds = json.loads(conditions_cel)
        if not conds:
            return True
        if not self._binding_conds:
            return True
        solver = self._store.condition_solver()
        return not solver.are_disjoint(self._binding_conds, conds)

    def active_claims(self, concept_id: str | None = None) -> list[dict]:
        if self._active_claim_id_set is not None:
            all_claims = self._store.claims_for(concept_id)
            return [
                claim for claim in all_claims
                if claim.get("id") in self._active_claim_id_set
            ]
        all_claims = self._store.claims_for(concept_id)
        return [c for c in all_claims if self.is_active(c)]

    def inactive_claims(self, concept_id: str | None = None) -> list[dict]:
        if self._inactive_claim_id_set is not None:
            all_claims = self._store.claims_for(concept_id)
            return [
                claim for claim in all_claims
                if claim.get("id") in self._inactive_claim_id_set
            ]
        all_claims = self._store.claims_for(concept_id)
        return [c for c in all_claims if not self.is_active(c)]

    def algorithm_for(self, concept_id: str) -> list[dict]:
        """Return all active algorithm claims relevant to the given concept."""
        active = self.active_claims(concept_id)
        return [c for c in active if c.get("type") == "algorithm"]

    def collect_known_values(
        self,
        variable_concepts: Sequence[ConceptId | str],
    ) -> dict[ConceptId, Any]:
        """Resolve numeric values for a list of concept IDs."""
        return collect_known_values(variable_concepts, self.value_of)

    def extract_variable_concepts(self, claim: dict) -> list[str]:
        """Extract concept IDs referenced by an algorithm claim's variables."""
        variables_json = claim.get("variables_json")
        if not variables_json:
            return []
        variables = json.loads(variables_json)
        concepts: list[str] = []
        if isinstance(variables, list):
            for var in variables:
                if isinstance(var, dict):
                    concept = var.get("concept")
                    if concept:
                        concepts.append(concept)
        elif isinstance(variables, dict):
            concepts.extend(variables.values())
        return concepts

    def extract_bindings(self, claim: dict) -> dict[str, str]:
        """Extract variable name -> concept mapping from an algorithm claim."""
        variables_json = claim.get("variables_json")
        if not variables_json:
            return {}
        variables = json.loads(variables_json)
        bindings: dict[str, str] = {}
        if isinstance(variables, list):
            for var in variables:
                if isinstance(var, dict):
                    name = var.get("name") or var.get("symbol")
                    concept = var.get("concept")
                    if name and concept:
                        bindings[name] = concept
        elif isinstance(variables, dict):
            bindings = dict(variables)
        return bindings

    def value_of(self, concept_id: str) -> ValueResult:
        active = self.active_claims(concept_id)
        if self._reasoning_backend() == "atms":
            supported_ids = self.atms_engine().supported_claim_ids(concept_id)
            active = [
                claim for claim in active
                if claim.get("id") in supported_ids
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
        result = self._resolver.derived_value(
            concept_id,
            override_values=override_values,
        )
        if self._reasoning_backend() == "atms":
            return self._attach_atms_derived_label(result)
        return self._attach_derived_label(result, override_values=override_values)

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
        from propstore.revision.projection import project_belief_base

        return project_belief_base(self)

    def revision_entrenchment(self, *, overrides: Mapping[str, Mapping[str, Any]] | None = None):
        """Compute the current revision-facing entrenchment ordering."""
        from propstore.revision.entrenchment import compute_entrenchment

        return compute_entrenchment(self, self.revision_base(), overrides=overrides)

    def expand(self, atom):
        """Expand the scoped revision belief base without mutating source storage."""
        from propstore.revision.operators import expand as expand_revision_base

        return expand_revision_base(self.revision_base(), atom)

    def contract(
        self,
        targets,
        *,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
    ):
        """Contract the scoped revision belief base using the current entrenchment."""
        from propstore.revision.operators import contract as contract_revision_base

        return contract_revision_base(
            self.revision_base(),
            targets,
            entrenchment=self.revision_entrenchment(overrides=overrides),
        )

    def revise(
        self,
        atom,
        *,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
        conflicts: Mapping[str, tuple[str, ...] | list[str]] | None = None,
    ):
        """Revise the scoped belief base by delegating to the revision package."""
        from propstore.revision.operators import revise as revise_revision_base

        return revise_revision_base(
            self.revision_base(),
            atom,
            entrenchment=self.revision_entrenchment(overrides=overrides),
            conflicts=conflicts,
        )

    def revision_explain(
        self,
        result,
        *,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Render the default explanation payload for a revision result."""
        from propstore.revision.explain import build_revision_explanation

        return build_revision_explanation(
            result,
            entrenchment=self.revision_entrenchment(overrides=overrides),
        )

    def epistemic_state(
        self,
        *,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
    ):
        """Build the explicit iterated revision state for this scoped world."""
        from propstore.revision.iterated import make_epistemic_state

        return make_epistemic_state(
            self.revision_base(),
            self.revision_entrenchment(overrides=overrides),
        )

    def iterated_revise(
        self,
        atom,
        *,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
        conflicts: Mapping[str, tuple[str, ...] | list[str]] | None = None,
        operator: str = "restrained",
        state=None,
    ):
        """Revise an explicit epistemic state using the selected iterated operator."""
        from propstore.revision.iterated import iterated_revise as iterated_revise_state

        current_state = state or self.epistemic_state(overrides=overrides)
        return iterated_revise_state(
            current_state,
            atom,
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
        queryables: Sequence[QueryableInput],
        limit: int = 8,
    ) -> ATMSFutureStatusReport:
        """Return bounded future-environment status changes for one claim."""
        self._require_atms_backend()
        return self.atms_engine().claim_future_statuses(
            claim_id,
            coerce_queryable_assumptions(queryables),
            limit=limit,
        )

    def concept_future_statuses(
        self,
        concept_id: str,
        queryables: Sequence[QueryableInput],
        limit: int = 8,
    ) -> dict[str, ATMSFutureStatusReport]:
        """Return bounded future-environment status changes for active claims of a concept."""
        self._require_atms_backend()
        normalized_queryables = coerce_queryable_assumptions(queryables)
        return {
            claim["id"]: self.atms_engine().claim_future_statuses(
                claim["id"],
                normalized_queryables,
                limit=limit,
            )
            for claim in sorted(self.active_claims(concept_id), key=lambda row: row["id"])
            if claim.get("id")
        }

    def claim_stability(
        self,
        claim_id: str,
        queryables: Sequence[QueryableInput],
        limit: int = 8,
    ) -> ATMSNodeStabilityReport:
        """Return bounded ATMS stability for one claim over replayed future worlds."""
        self._require_atms_backend()
        return self.atms_engine().claim_stability(
            claim_id,
            coerce_queryable_assumptions(queryables),
            limit=limit,
        )

    def claim_is_stable(
        self,
        claim_id: str,
        queryables: Sequence[QueryableInput],
        limit: int = 8,
    ) -> bool:
        """Whether a claim keeps the same ATMS status in all bounded consistent futures."""
        self._require_atms_backend()
        return self.atms_engine().claim_is_stable(
            claim_id,
            coerce_queryable_assumptions(queryables),
            limit=limit,
        )

    def concept_stability(
        self,
        concept_id: str,
        queryables: Sequence[QueryableInput],
        limit: int = 8,
    ) -> ATMSConceptStabilityReport:
        """Return bounded value-status stability for one concept over replayed future worlds."""
        self._require_atms_backend()
        return self.atms_engine().concept_stability(
            concept_id,
            coerce_queryable_assumptions(queryables),
            limit=limit,
        )

    def concept_is_stable(
        self,
        concept_id: str,
        queryables: Sequence[QueryableInput],
        limit: int = 8,
    ) -> bool:
        """Whether a concept keeps the same value status in all bounded consistent futures."""
        self._require_atms_backend()
        return self.atms_engine().concept_is_stable(
            concept_id,
            coerce_queryable_assumptions(queryables),
            limit=limit,
        )

    def claim_relevance(
        self,
        claim_id: str,
        queryables: Sequence[QueryableInput],
        limit: int = 8,
    ) -> ATMSNodeRelevanceReport:
        """Return which bounded queryables can flip a claim's ATMS status."""
        self._require_atms_backend()
        return self.atms_engine().claim_relevance(
            claim_id,
            coerce_queryable_assumptions(queryables),
            limit=limit,
        )

    def claim_relevant_queryables(
        self,
        claim_id: str,
        queryables: Sequence[QueryableInput],
        limit: int = 8,
    ) -> list[str]:
        """Return the bounded queryables that matter to a claim's ATMS status."""
        self._require_atms_backend()
        return self.atms_engine().claim_relevant_queryables(
            claim_id,
            coerce_queryable_assumptions(queryables),
            limit=limit,
        )

    def concept_relevance(
        self,
        concept_id: str,
        queryables: Sequence[QueryableInput],
        limit: int = 8,
    ) -> ATMSConceptRelevanceReport:
        """Return which bounded queryables can flip a concept's value status."""
        self._require_atms_backend()
        return self.atms_engine().concept_relevance(
            concept_id,
            coerce_queryable_assumptions(queryables),
            limit=limit,
        )

    def concept_relevant_queryables(
        self,
        concept_id: str,
        queryables: Sequence[QueryableInput],
        limit: int = 8,
    ) -> list[str]:
        """Return the bounded queryables that matter to a concept's value status."""
        self._require_atms_backend()
        return self.atms_engine().concept_relevant_queryables(
            concept_id,
            coerce_queryable_assumptions(queryables),
            limit=limit,
        )

    def claim_interventions(
        self,
        claim_id: str,
        queryables: Sequence[QueryableInput],
        target_status: str,
        limit: int = 8,
        max_plans: int | None = None,
    ) -> list[ATMSNodeInterventionPlan]:
        """Return bounded additive intervention plans for one claim."""
        self._require_atms_backend()
        return self.atms_engine().claim_interventions(
            claim_id,
            coerce_queryable_assumptions(queryables),
            target_status,
            limit=limit,
            max_plans=max_plans,
        )

    def concept_interventions(
        self,
        concept_id: str,
        queryables: Sequence[QueryableInput],
        target_value_status: str,
        limit: int = 8,
        max_plans: int | None = None,
    ) -> list[ATMSConceptInterventionPlan]:
        """Return bounded additive intervention plans for one concept."""
        self._require_atms_backend()
        return self.atms_engine().concept_interventions(
            concept_id,
            coerce_queryable_assumptions(queryables),
            target_value_status,
            limit=limit,
            max_plans=max_plans,
        )

    def claim_next_queryables(
        self,
        claim_id: str,
        queryables: Sequence[QueryableInput],
        target_status: str,
        limit: int = 8,
        max_suggestions: int | None = None,
    ) -> list[ATMSNextQuerySuggestion]:
        """Return bounded next-query suggestions derived from claim intervention plans."""
        self._require_atms_backend()
        return self.atms_engine().next_queryables_for_claim(
            claim_id,
            coerce_queryable_assumptions(queryables),
            target_status,
            limit=limit,
            max_suggestions=max_suggestions,
        )

    def concept_next_queryables(
        self,
        concept_id: str,
        queryables: Sequence[QueryableInput],
        target_value_status: str,
        limit: int = 8,
        max_suggestions: int | None = None,
    ) -> list[ATMSNextQuerySuggestion]:
        """Return bounded next-query suggestions derived from concept intervention plans."""
        self._require_atms_backend()
        return self.atms_engine().next_queryables_for_concept(
            concept_id,
            coerce_queryable_assumptions(queryables),
            target_value_status,
            limit=limit,
            max_suggestions=max_suggestions,
        )

    def fragility(
        self,
        *,
        concept_id: str | None = None,
        queryables: list | None = None,
        top_k: int = 20,
        include_parametric: bool = True,
        include_epistemic: bool = True,
        include_conflict: bool = True,
        combination: str = "top2",
        atms_limit: int = 8,
    ) -> "FragilityReport":
        """Rank epistemic targets by fragility — what to learn next."""
        from propstore.fragility import rank_fragility
        return rank_fragility(
            self,
            concept_id=concept_id,
            queryables=queryables,
            top_k=top_k,
            include_parametric=include_parametric,
            include_epistemic=include_epistemic,
            include_conflict=include_conflict,
            combination=combination,
            atms_limit=atms_limit,
        )

    def why_concept_out(
        self,
        concept_id: str,
        queryables: Sequence[QueryableInput] | None = None,
        limit: int = 8,
    ) -> dict[str, Any]:
        """Explain why a concept currently lacks exact ATMS support."""
        self._require_atms_backend()
        normalized_queryables = (
            None
            if queryables is None
            else coerce_queryable_assumptions(queryables)
        )
        supported_ids = self.atms_engine().supported_claim_ids(concept_id)
        claim_reasons = {
            claim["id"]: self.atms_engine().why_out(
                f"claim:{claim['id']}",
                queryables=normalized_queryables,
                limit=limit,
            )
            for claim in sorted(self.active_claims(concept_id), key=lambda row: row["id"])
            if claim.get("id")
        }
        return {
            "concept_id": concept_id,
            "value_status": self.value_of(concept_id).status,
            "supported_claim_ids": sorted(supported_ids),
            "claim_reasons": claim_reasons,
        }

    def explain_nogood(
        self,
        environment: EnvironmentKey | tuple[str, ...] | list[str],
    ) -> ATMSNogoodDetail | None:
        return self.atms_engine().explain_nogood(environment)

    def verify_atms_labels(self) -> ATMSLabelVerificationReport:
        self._require_atms_backend()
        return self.atms_engine().verify_labels()

    def claims_in_environment(
        self,
        environment: EnvironmentKey | tuple[str, ...] | list[str],
    ) -> list[str]:
        """Return claim IDs whose exact ATMS support is visible inside the environment."""
        return [
            node_id.partition(":")[2]
            for node_id in self.atms_engine().nodes_in_environment(environment)
            if node_id.startswith("claim:")
        ]

    def explain_claim_support(self, claim_id: str) -> ATMSNodeExplanation:
        """Return the ATMS justification trace and support metadata for a claim."""
        return self.atms_engine().explain_node(self.claim_status(claim_id).node_id)

    def claim_support(self, claim: dict) -> tuple[Label | None, SupportQuality]:
        """Return exact label support when reconstructible, plus honesty metadata."""
        label = self._claim_support_label(claim)
        if label is not None:
            return label, SupportQuality.EXACT
        return None, self._support_quality(claim)

    def is_determined(self, concept_id: str) -> bool:
        return self.value_of(concept_id).status == "determined"

    def conflicts(self, concept_id: str | None = None) -> list[dict]:
        """Return active conflicts, revalidated against the current belief space."""
        if concept_id in self._conflicts_cache:
            return self._conflicts_cache[concept_id]
        active_claims = self.active_claims(concept_id)
        active_ids = {c["id"] for c in active_claims}

        result: list[dict] = []
        all_conflicts = [
            coerce_conflict_row(conflict)
            for conflict in self._store.conflicts()
        ]
        for conflict in all_conflicts:
            if conflict.claim_a_id in active_ids and conflict.claim_b_id in active_ids:
                if concept_id is None or conflict.concept_id == concept_id:
                    result.append(conflict.to_dict())
        seen = {(c["claim_a_id"], c["claim_b_id"], c.get("concept_id")) for c in result}
        for conflict in _recomputed_conflicts(self._store, active_claims):
            key = (conflict["claim_a_id"], conflict["claim_b_id"], conflict.get("concept_id"))
            reverse_key = (conflict["claim_b_id"], conflict["claim_a_id"], conflict.get("concept_id"))
            if key not in seen and reverse_key not in seen:
                result.append(conflict)
                seen.add(key)
        self._conflicts_cache[concept_id] = result
        return result

    def explain(self, claim_id: str) -> list[dict]:
        """Stance walk filtered to active claims."""
        claim = self._store.get_claim(claim_id)
        if claim is None or not self.is_active(claim):
            return []

        full_chain = self._store.explain(claim_id)
        result = []
        for s in full_chain:
            target = self._store.get_claim(s["target_claim_id"])
            if target is not None and self.is_active(target):
                result.append(s)
        return result

    def _attach_value_label(self, result: ValueResult) -> ValueResult:
        if result.status != "determined" or not result.claims:
            return result

        claim_labels: list[Label] = []
        for claim in result.claims:
            claim_label = self._claim_support_label(claim)
            if claim_label is None:
                return result
            claim_labels.append(claim_label)
        return replace(result, label=merge_labels(claim_labels))

    def _attach_atms_value_label(self, result: ValueResult) -> ValueResult:
        if result.status != "determined" or not result.claims:
            return result

        engine = self.atms_engine()
        claim_labels: list[Label] = []
        for claim in result.claims:
            claim_id = claim.get("id")
            if not claim_id:
                return result
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
        if result.status != "derived":
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
        if result.status != "derived" or result.value is None:
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
        if result.status == "determined":
            return replace(result, label=self.value_of(concept_id).label)

        if result.status != "resolved" or not result.winning_claim_id:
            return result

        winning_claim = next(
            (claim for claim in result.claims if claim.get("id") == result.winning_claim_id),
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
        if result.status == "determined":
            return replace(result, label=self.value_of(concept_id).label)

        if result.status != "resolved" or not result.winning_claim_id:
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
        if value_result.status == "determined":
            return value_result.label

        if concept_id in seen:
            return None

        seen.add(concept_id)
        try:
            derived = self.derived_value(concept_id, override_values=override_values)
        finally:
            seen.discard(concept_id)
        if derived.status == "derived":
            return derived.label
        return None

    def _claim_support_label(self, claim: dict) -> Label | None:
        # Labels are only attached when the active support can be reconstructed
        # exactly from compiled assumptions. Context visibility is enforced
        # separately from CEL activation, so a context-scoped claim is not an
        # unconditional fact even if it has no explicit conditions.
        if claim.get("context_id") is not None:
            return None

        conds_json = claim.get("conditions_cel")
        if not conds_json:
            return Label.empty()

        conditions = json.loads(conds_json)
        if not conditions:
            return Label.empty()

        condition_labels: list[Label] = []
        for condition in conditions:
            matches = self._assumptions_by_cel.get(condition)
            if not matches:
                return None
            condition_labels.append(
                Label(
                    tuple(
                        EnvironmentKey((assumption.assumption_id,))
                        for assumption in matches
                    )
                )
            )
        return combine_labels(*condition_labels)

    def _support_quality(self, claim: dict) -> SupportQuality:
        conds_json = claim.get("conditions_cel")
        has_conditions = False
        if conds_json:
            try:
                has_conditions = bool(json.loads(conds_json))
            except (TypeError, json.JSONDecodeError):
                has_conditions = True

        has_context = claim.get("context_id") is not None
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
