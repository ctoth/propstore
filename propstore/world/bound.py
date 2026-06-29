"""BoundWorld — condition-bound belief-space view over a charter WorldStore.

A :class:`BoundWorld` renders one :class:`~propstore.core.environment.Environment`
(bindings + context + compiled assumptions) over a
:class:`~propstore.core.environment.WorldStore`. It answers the
:class:`~propstore.world.types.BeliefSpace` surface — which claims are active, a
concept's value/derived/resolved value, conflicts, and the stance explanation —
and exposes the ATMS-native inspection surface by lazily constructing an
:class:`~propstore.world.atms.ATMSEngine` over itself.

Substrate boundary: claims are the canonical
:class:`~propstore.core.graph_types.ClaimNode` (rich, condition-bearing) for label
and condition reasoning, projected to the thin
:class:`~propstore.core.active_claims.ActiveClaim` the value resolver and
argumentation bridge consume; conditions are condition-ir's solver used directly;
the label algebra is the carved ``core.labels`` algebra (no mirror types). The
belief-revision surface (expand/contract/revise/iterated/epistemic state) is
owned by ``propstore.support_revision`` and re-attaches in a later phase — see the
"revision surface" seam below.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from condition_ir import (
    CelExpr,
    ConceptInfo,
    check_condition_ir,
    checked_condition_set,
    to_cel_expr,
)

from propstore.conflict_detector import ConflictRecord, detect_conflicts
from propstore.conflict_detector.models import ConflictClaim
from propstore.core.activation import is_claim_node_active
from propstore.core.active_claims import ActiveClaim, ActiveClaimInput
from propstore.core.environment import AssumptionRef, Environment, WorldStore
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.graph_types import ActiveWorldGraph, ClaimNode, ParameterizationEdge
from propstore.core.id_types import ConceptId, to_context_id
from propstore.core.labels import (
    EnvironmentKey,
    Label,
    SupportQuality,
    binding_condition_to_cel,
    combine_labels,
    context_label,
    make_environment_key,
    merge_labels,
)
from propstore.families.claims import Claim, ClaimType
from propstore.families.relations import Stance
from propstore.world.types import (
    ATMSConceptInterventionPlan,
    ATMSConceptRelevanceReport,
    ATMSConceptStabilityReport,
    ATMSFutureStatusReport,
    ATMSInspection,
    ATMSLabelVerificationReport,
    ATMSNextQuerySuggestion,
    ATMSNodeExplanation,
    ATMSNodeInterventionPlan,
    ATMSNodeRelevanceReport,
    ATMSNodeStabilityReport,
    ATMSNodeStatus,
    ATMSNogoodDetail,
    BeliefSpace,
    DerivedResult,
    QueryableInput,
    RenderPolicy,
    ResolutionStrategy,
    ResolvedResult,
    ValueResult,
    ValueStatus,
    coerce_queryable_assumptions,
)
from propstore.support_revision.belief_set_adapter import (
    DEFAULT_ITERATED_OPERATOR,
    DEFAULT_MAX_ALPHABET_SIZE,
    decide_contract,
    decide_expand,
    decide_revise,
)
from propstore.support_revision.input_normalization import normalize_revision_input
from propstore.support_revision.realization import realize_formal_decision
from propstore.support_revision.state import AssertionAtom, AssumptionAtom
from propstore.world.value_resolver import ActiveClaimResolver, collect_known_values

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem
    from propstore.support_revision.entrenchment import EntrenchmentReport
    from propstore.support_revision.explanation_types import RevisionExplanation
    from propstore.support_revision.history import EpistemicSnapshot
    from propstore.support_revision.state import (
        BeliefAtom,
        BeliefBase,
        EpistemicState,
        RevisionResult,
    )
    from propstore.world.atms import ATMSEngine


def _value_concept_id(claim: Claim) -> str | None:
    """The concept a claim's value is about: output, else target, else first ref."""

    for candidate in (claim.output_concept, claim.target_concept, *claim.concepts):
        if candidate:
            return str(candidate)
    return None


def _active_claim_from_claim(claim: Claim) -> ActiveClaim:
    """Project a stored :class:`Claim` charter into the thin bridge view.

    The resolver and argumentation bridge read the claim's scalar value,
    algorithm body, and claim type through ``attribute_value``; they ride in
    ``attributes`` here so the canonical thin :class:`ActiveClaim` stays free of
    storage-shaped fields.
    """

    attributes: list[tuple[str, Any]] = [
        ("claim_type", (claim.claim_type or ClaimType.UNKNOWN).value),
    ]
    if claim.value is not None:
        attributes.append(("value", claim.value))
    if claim.body is not None:
        attributes.append(("body", claim.body))
    return ActiveClaim(
        claim_id=str(claim.claim_id),
        context_id=claim.context_id,
        concept_id=_value_concept_id(claim),
        canonical_name=claim.name,
        statement=claim.statement,
        sample_size=None if claim.sample_size is None else float(claim.sample_size),
        uncertainty=claim.uncertainty,
        confidence=claim.confidence,
        attributes=tuple(sorted(attributes)),
    )


def _claim_id_of(claim: ActiveClaimInput | Claim) -> str | None:
    if isinstance(claim, Mapping):
        identity = claim.get("id")
        if identity is None:
            identity = claim.get("claim_id")
        return None if identity is None else str(identity)
    return str(claim.claim_id)


@dataclass(frozen=True)
class _ConflictInputs:
    """Per-instance memo of the concept + CEL registry for conflict revalidation.

    Invariant for the lifetime of a ``BoundWorld`` (the store is set once and
    never rebound), so it is built lazily on the first ``.conflicts()`` miss and
    reused. OverlayWorld overlays construct their own ``BoundWorld`` and so get
    their own cache (see the overlay-safety note in the conflicts-cache test).
    """

    concept_registry: dict[str, dict[str, Any]]
    cel_registry: dict[str, ConceptInfo]


def conflict_inputs_for_store(
    store: WorldStore,
) -> tuple[dict[str, dict[str, Any]], dict[str, ConceptInfo]]:
    """Build the concept + CEL registry the conflict detector reads."""

    registry: dict[str, dict[str, Any]] = {}
    for concept in store.all_concepts():
        concept_id = str(concept.concept_id)
        entry: dict[str, Any] = {
            "id": concept_id,
            "artifact_id": concept_id,
            "canonical_name": concept.canonical_name,
            "status": concept.status.value,
        }
        relationships = [
            {
                "inputs": [str(input_id) for input_id in edge.input_concept_ids],
                "sympy": edge.sympy,
                "exactness": None if edge.exactness is None else edge.exactness.value,
                "conditions": [str(condition) for condition in edge.conditions],
            }
            for edge in store.parameterizations_for(concept_id)
        ]
        if relationships:
            entry["parameterization_relationships"] = relationships
        registry[concept_id] = entry
    cel_registry = dict(store.condition_solver().registry)
    return registry, cel_registry


def conflict_claim_from_node(node: ClaimNode) -> ConflictClaim | None:
    """Build a :class:`ConflictClaim` payload view from a compiled claim node."""

    payload: dict[str, Any] = dict(node.attribute_mapping())
    payload["id"] = str(node.claim_id)
    payload["artifact_id"] = str(node.claim_id)
    payload["type"] = node.claim_type.value
    if node.value_concept_id is not None:
        payload["output_concept"] = str(node.value_concept_id)
    payload["value"] = node.scalar_value
    if node.checked_conditions is not None:
        payload["conditions"] = [str(source) for source in node.checked_conditions.sources]
    return ConflictClaim.from_payload(payload)


def recomputed_conflicts(
    store: WorldStore,
    claim_nodes: Sequence[ClaimNode],
    *,
    lifting_system: LiftingSystem | None = None,
    precomputed_inputs: _ConflictInputs | None = None,
) -> list[ConflictRecord]:
    """Revalidate active conflicts against the live belief space."""

    if len(claim_nodes) < 2:
        return []
    conflict_claims = [
        conflict_claim
        for node in claim_nodes
        if (conflict_claim := conflict_claim_from_node(node)) is not None
    ]
    if precomputed_inputs is None:
        concept_registry, cel_registry = conflict_inputs_for_store(store)
    else:
        concept_registry = precomputed_inputs.concept_registry
        cel_registry = precomputed_inputs.cel_registry
    return detect_conflicts(
        conflict_claims,
        concept_registry,
        cel_registry,
        lifting_system=lifting_system,
    )


class BoundWorld(BeliefSpace):
    """The world under specific condition bindings, optionally scoped to a context."""

    def __init__(
        self,
        world: WorldStore,
        bindings: dict[str, Any] | None = None,
        context_id: str | None = None,
        lifting_system: LiftingSystem | None = None,
        *,
        environment: Environment | None = None,
        policy: RenderPolicy | None = None,
        active_graph: ActiveWorldGraph | None = None,
    ) -> None:
        self._store = world
        if environment is None:
            environment = Environment(
                bindings={} if bindings is None else bindings,
                context_id=(None if context_id is None else to_context_id(context_id)),
            )
        self._environment = environment
        self._policy = policy
        self._active_graph = active_graph
        self._active_claim_id_set = (
            {str(claim_id) for claim_id in active_graph.active_claim_ids}
            if active_graph is not None
            else None
        )
        self._inactive_claim_id_set = (
            {str(claim_id) for claim_id in active_graph.inactive_claim_ids}
            if active_graph is not None
            else None
        )
        self._atms_engine: ATMSEngine | None = None
        self._bindings = dict(environment.bindings)
        self._binding_conds = [
            binding_condition_to_cel(key, value) for key, value in self._bindings.items()
        ]
        self._assumptions_by_cel: dict[CelExpr, list[AssumptionRef]] = {}
        for assumption in environment.assumptions:
            self._assumptions_by_cel.setdefault(assumption.cel, []).append(assumption)
        for assumption_cel in environment.effective_assumptions:
            if assumption_cel not in self._binding_conds:
                self._binding_conds.append(assumption_cel)
        self._context_id = environment.context_id
        self._lifting_system = lifting_system
        self._conflicts_cache: dict[str | None, list[ConflictRecord]] = {}
        self._conflict_inputs_cache: _ConflictInputs | None = None
        self._claim_node_index_cache: dict[str, ClaimNode] | None = None
        self._resolver = ActiveClaimResolver(
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

    # -- public accessors (the structural surface the ATMS engine reads) ----

    @property
    def environment(self) -> Environment:
        return self._environment

    @property
    def active_graph(self) -> ActiveWorldGraph | None:
        return self._active_graph

    @property
    def store(self) -> WorldStore:
        return self._store

    @property
    def lifting_system(self) -> LiftingSystem | None:
        return self._lifting_system

    @property
    def policy(self) -> RenderPolicy | None:
        return self._policy

    # -- claim-node index ---------------------------------------------------

    def _claim_node_index(self) -> dict[str, ClaimNode]:
        if self._claim_node_index_cache is None:
            claims = (
                self._active_graph.compiled.claims
                if self._active_graph is not None
                else build_compiled_world_graph(self._store).claims
            )
            self._claim_node_index_cache = {str(node.claim_id): node for node in claims}
        return self._claim_node_index_cache

    def _claim_node(self, claim_id: str) -> ClaimNode | None:
        return self._claim_node_index().get(str(claim_id))

    def _resolve_claim_lookup_id(self, claim_id: str) -> str:
        return self._store.resolve_claim(claim_id) or claim_id

    # -- construction helpers ----------------------------------------------

    def rebind(
        self,
        environment: Environment,
        *,
        policy: RenderPolicy | None = None,
    ) -> BoundWorld:
        """Return the same bound-world view over a new environment."""

        return self.__class__(
            self._store,
            environment=environment,
            lifting_system=self._lifting_system,
            policy=policy,
        )

    # -- activation ---------------------------------------------------------

    def is_active(self, claim: ActiveClaimInput | Claim) -> bool:
        """Whether a claim is active under the current bindings and context."""

        claim_id = _claim_id_of(claim)
        if claim_id is not None and self._active_claim_id_set is not None:
            if claim_id in self._active_claim_id_set:
                return True
            if claim_id in (self._inactive_claim_id_set or set()):
                return False

        if claim_id is None:
            return True
        node = self._claim_node(claim_id)
        if node is None:
            return True
        return is_claim_node_active(
            node,
            environment=self._environment,
            solver=self._store.condition_solver(),
            lifting_system=self._lifting_system,
        )

    def is_param_compatible(self, parameterization: ParameterizationEdge) -> bool:
        return self.is_parameterization_compatible(parameterization)

    def is_parameterization_compatible(self, parameterization: ParameterizationEdge) -> bool:
        """Whether a parameterization's conditions are compatible with the bindings."""

        condition_set = parameterization.checked_conditions
        if condition_set is None or not condition_set.conditions:
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

    def active_claims(self, concept_id: str | None = None) -> list[ActiveClaim]:
        all_claims = [
            _active_claim_from_claim(claim)
            for claim in self._store.claims_for(concept_id)
        ]
        if self._active_claim_id_set is not None:
            return [
                claim
                for claim in all_claims
                if str(claim.claim_id) in self._active_claim_id_set
            ]
        return [claim for claim in all_claims if self.is_active(claim)]

    def inactive_claims(self, concept_id: str | None = None) -> list[ActiveClaim]:
        all_claims = [
            _active_claim_from_claim(claim)
            for claim in self._store.claims_for(concept_id)
        ]
        if self._inactive_claim_id_set is not None:
            return [
                claim
                for claim in all_claims
                if str(claim.claim_id) in self._inactive_claim_id_set
            ]
        return [claim for claim in all_claims if not self.is_active(claim)]

    def algorithm_for(self, concept_id: str) -> list[ActiveClaim]:
        """Return all active algorithm claims relevant to the given concept."""

        return [
            claim
            for claim in self.active_claims(concept_id)
            if claim.attribute_value("claim_type") == ClaimType.ALGORITHM.value
        ]

    # -- resolver callbacks -------------------------------------------------

    def _concept_symbol_candidates(self, concept_id: ConceptId | str) -> list[str]:
        candidates: list[str] = []
        seen: set[str] = set()

        def add(candidate: object) -> None:
            if not isinstance(candidate, str) or not candidate or candidate in seen:
                return
            seen.add(candidate)
            candidates.append(candidate)

        concept = self._store.get_concept(str(concept_id))
        if concept is None:
            for entry in self._store.all_concepts():
                if str(entry.concept_id) == str(concept_id) or entry.canonical_name == str(
                    concept_id
                ):
                    concept = entry
                    break
        if concept is None:
            return candidates
        add(concept.canonical_name)
        return candidates

    def collect_known_values(
        self,
        variable_concepts: Sequence[ConceptId | str],
    ) -> dict[ConceptId, Any]:
        return collect_known_values(variable_concepts, self.value_of)

    def extract_variable_concepts(self, claim: ActiveClaimInput) -> list[str]:
        # Algorithm variable bindings (symbol -> concept) are not carried on the
        # provenance-free Claim charter or its lowered ClaimNode, so the
        # multi-algorithm-equivalence path has no per-variable concepts to read
        # here (docs/gaps.md: algorithm variable bindings are not graph-native).
        _ = claim
        return []

    def extract_bindings(self, claim: ActiveClaimInput) -> dict[str, str]:
        _ = claim
        return {}

    # -- value / derived / resolved ----------------------------------------

    def value_of(self, concept_id: str) -> ValueResult:
        active = self.active_claims(concept_id)
        if self._reasoning_backend() == "atms":
            supported_ids = self.atms_engine().supported_claim_ids(concept_id)
            active = [claim for claim in active if str(claim.claim_id) in supported_ids]
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
            self,
            concept_id,
            strategy=strategy,
            policy=effective_policy,
            world=self._store,
        )
        if result.status is ValueStatus.RESOLVED and result.winning_claim_id:
            resolved_winner_id = (
                self._store.resolve_claim(str(result.winning_claim_id))
                or result.winning_claim_id
            )
            result = replace(result, winning_claim_id=resolved_winner_id)
        if self._reasoning_backend() == "atms":
            return self._attach_atms_resolved_label(concept_id, result)
        return self._attach_resolved_label(concept_id, result)

    def is_determined(self, concept_id: str) -> bool:
        return self.value_of(concept_id).status is ValueStatus.DETERMINED

    # -- conflicts / explanation -------------------------------------------

    def _get_or_build_conflict_inputs(self) -> _ConflictInputs:
        if self._conflict_inputs_cache is None:
            concept_registry, cel_registry = conflict_inputs_for_store(self._store)
            self._conflict_inputs_cache = _ConflictInputs(
                concept_registry=concept_registry,
                cel_registry=cel_registry,
            )
        return self._conflict_inputs_cache

    def conflicts(self, concept_id: str | None = None) -> list[ConflictRecord]:
        """Return active conflicts, revalidated against the current belief space."""

        resolved_concept_id = (
            self._store.resolve_concept(concept_id) or concept_id
            if concept_id is not None
            else None
        )
        if resolved_concept_id in self._conflicts_cache:
            return self._conflicts_cache[resolved_concept_id]

        active_claims = self.active_claims(resolved_concept_id)
        if len(active_claims) < 2:
            self._conflicts_cache[resolved_concept_id] = []
            return []
        active_ids = {str(claim.claim_id) for claim in active_claims}

        result: list[ConflictRecord] = [
            conflict
            for conflict in self._store.conflicts()
            if str(conflict.claim_a_id) in active_ids
            and str(conflict.claim_b_id) in active_ids
            and (resolved_concept_id is None or str(conflict.concept_id) == resolved_concept_id)
        ]
        seen = {
            (str(conflict.claim_a_id), str(conflict.claim_b_id), str(conflict.concept_id))
            for conflict in result
        }
        active_nodes = [
            node
            for claim in active_claims
            if (node := self._claim_node(str(claim.claim_id))) is not None
        ]
        precomputed = self._get_or_build_conflict_inputs()
        for conflict in recomputed_conflicts(
            self._store,
            active_nodes,
            lifting_system=self._lifting_system,
            precomputed_inputs=precomputed,
        ):
            key = (str(conflict.claim_a_id), str(conflict.claim_b_id), str(conflict.concept_id))
            reverse_key = (
                str(conflict.claim_b_id),
                str(conflict.claim_a_id),
                str(conflict.concept_id),
            )
            if key not in seen and reverse_key not in seen:
                result.append(conflict)
                seen.add(key)
        self._conflicts_cache[resolved_concept_id] = result
        return result

    def explain(self, claim_id: str) -> list[Stance]:
        """Stance walk filtered to active claims."""

        resolved_claim_id = self._store.resolve_claim(claim_id) or claim_id
        claim = self._store.get_claim(resolved_claim_id)
        if claim is None or not self.is_active(claim):
            return []
        result: list[Stance] = []
        for stance in self._store.explain(resolved_claim_id):
            if stance.target_claim_id is None:
                continue
            target = self._store.get_claim(str(stance.target_claim_id))
            if target is not None and self.is_active(target):
                result.append(stance)
        return result

    # -- exact-support labels ----------------------------------------------

    def claim_support(self, claim: ActiveClaim) -> tuple[Label | None, SupportQuality]:
        """Return exact label support when reconstructible, plus honesty metadata."""

        label = self._claim_support_label(claim)
        if label is not None:
            return label, SupportQuality.EXACT
        return None, self._support_quality(claim)

    def _claim_support_label(self, claim: ActiveClaim) -> Label | None:
        node = self._claim_node(str(claim.claim_id))
        labels: list[Label] = []
        context_id = self._claim_context_id(claim, node)
        if context_id is not None:
            labels.append(context_label(context_id))

        conditions = (
            node.checked_conditions.sources
            if node is not None and node.checked_conditions is not None
            else ()
        )
        if not conditions:
            return combine_labels(*labels) if labels else Label.empty()

        for condition in conditions:
            matches = self._assumptions_by_cel.get(to_cel_expr(condition))
            if not matches:
                return None
            labels.append(
                Label(
                    tuple(
                        make_environment_key(assumption_ids=(assumption.assumption_id,))
                        for assumption in matches
                    )
                )
            )
        return combine_labels(*labels)

    def _support_quality(self, claim: ActiveClaim) -> SupportQuality:
        node = self._claim_node(str(claim.claim_id))
        has_conditions = bool(
            node is not None
            and node.checked_conditions is not None
            and node.checked_conditions.conditions
        )
        has_context = self._claim_context_id(claim, node) is not None
        if has_context and has_conditions:
            return SupportQuality.MIXED
        if has_context:
            return SupportQuality.CONTEXT_VISIBLE_ONLY
        return SupportQuality.SEMANTIC_COMPATIBLE

    @staticmethod
    def _claim_context_id(claim: ActiveClaim, node: ClaimNode | None) -> str | None:
        if claim.context_id is not None:
            return str(claim.context_id)
        if node is not None:
            context_id = node.attribute_value("context_id")
            if context_id is not None:
                return str(context_id)
        return None

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

    def _attach_atms_value_label(self, result: ValueResult) -> ValueResult:
        if result.status is not ValueStatus.DETERMINED or not result.claims:
            return result
        engine = self.atms_engine()
        claim_labels: list[Label] = []
        for claim in result.claims:
            claim_label = engine.claim_label(str(claim.claim_id))
            if claim_label is None:
                return result
            claim_labels.append(claim_label)
        return replace(result, label=merge_labels(claim_labels, nogoods=engine.nogoods))

    def _normalize_override_values(
        self,
        override_values: Mapping[str, float | str | None] | None,
    ) -> Mapping[str, float | str | None] | None:
        if override_values is None:
            return None
        normalized: dict[str, float | str | None] = {}
        for key, value in override_values.items():
            normalized[self._store.resolve_concept(key) or key] = value
        return normalized

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
                str(input_id),
                override_values=override_values,
                seen={str(result.concept_id)},
            )
            if input_label is None:
                return result
            input_labels.append(input_label)
        return replace(result, label=combine_labels(*input_labels))

    def _attach_atms_derived_label(self, result: DerivedResult) -> DerivedResult:
        if result.status is not ValueStatus.DERIVED or result.value is None:
            return result
        label = self.atms_engine().derived_label(str(result.concept_id), result.value)
        if label is None:
            return result
        return replace(result, label=label)

    def _attach_resolved_label(self, concept_id: str, result: ResolvedResult) -> ResolvedResult:
        if result.status is ValueStatus.DETERMINED:
            return replace(result, label=self.value_of(concept_id).label)
        if result.status is not ValueStatus.RESOLVED or not result.winning_claim_id:
            return result
        resolved_winner_id = (
            self._store.resolve_claim(str(result.winning_claim_id)) or str(result.winning_claim_id)
        )
        winning_claim = next(
            (claim for claim in result.claims if str(claim.claim_id) == resolved_winner_id),
            None,
        )
        if winning_claim is None:
            return result
        claim_label = self._claim_support_label(winning_claim)
        if claim_label is None:
            return result
        return replace(result, label=claim_label)

    def _attach_atms_resolved_label(self, concept_id: str, result: ResolvedResult) -> ResolvedResult:
        if result.status is ValueStatus.DETERMINED:
            return replace(result, label=self.value_of(concept_id).label)
        if result.status is not ValueStatus.RESOLVED or not result.winning_claim_id:
            return result
        resolved_winner_id = (
            self._store.resolve_claim(str(result.winning_claim_id)) or str(result.winning_claim_id)
        )
        label = self.atms_engine().claim_label(resolved_winner_id)
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

    # -- reasoning backend gates -------------------------------------------

    def _reasoning_backend(self) -> str:
        if self._policy is None:
            return "claim_graph"
        return self._policy.reasoning_backend.value

    def _require_atms_backend(self) -> None:
        if self._reasoning_backend() != "atms":
            raise ValueError("Future ATMS analysis requires backend='atms'")

    # -- ATMS pass-through surface ------------------------------------------

    def atms_engine(self) -> ATMSEngine:
        if self._atms_engine is None:
            from propstore.world.atms import ATMSEngine

            self._atms_engine = ATMSEngine(self)
        return self._atms_engine

    def claim_status(self, claim_id: str) -> ATMSInspection:
        return self.atms_engine().claim_status(self._resolve_claim_lookup_id(claim_id))

    def claim_essential_support(self, claim_id: str) -> EnvironmentKey | None:
        return self.claim_status(claim_id).essential_support

    def claim_future_statuses(
        self,
        claim_id: str,
        queryables: Sequence[QueryableInput],
        *,
        limit: int | None,
    ) -> ATMSFutureStatusReport:
        self._require_atms_backend()
        return self.atms_engine().claim_future_statuses(
            self._resolve_claim_lookup_id(claim_id),
            coerce_queryable_assumptions(queryables),
            limit=limit,
        )

    def concept_future_statuses(
        self,
        concept_id: str,
        queryables: Sequence[QueryableInput],
        *,
        limit: int | None,
    ) -> dict[str, ATMSFutureStatusReport]:
        self._require_atms_backend()
        normalized_queryables = coerce_queryable_assumptions(queryables)
        return {
            str(claim.claim_id): self.atms_engine().claim_future_statuses(
                str(claim.claim_id),
                normalized_queryables,
                limit=limit,
            )
            for claim in sorted(self.active_claims(concept_id), key=lambda row: str(row.claim_id))
        }

    def claim_stability(
        self,
        claim_id: str,
        queryables: Sequence[QueryableInput],
        *,
        limit: int | None,
    ) -> ATMSNodeStabilityReport:
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
        *,
        limit: int | None,
    ) -> bool:
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
        *,
        limit: int | None,
    ) -> ATMSConceptStabilityReport:
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
        *,
        limit: int | None,
    ) -> bool:
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
        *,
        limit: int | None,
    ) -> ATMSNodeRelevanceReport:
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
        *,
        limit: int | None,
    ) -> list[str]:
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
        *,
        limit: int | None,
    ) -> ATMSConceptRelevanceReport:
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
        *,
        limit: int | None,
    ) -> list[str]:
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
        target_status: ATMSNodeStatus,
        *,
        limit: int | None,
        max_plans: int | None = None,
    ) -> list[ATMSNodeInterventionPlan]:
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
        target_value_status: ValueStatus,
        *,
        limit: int | None,
        max_plans: int | None = None,
    ) -> list[ATMSConceptInterventionPlan]:
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
        target_status: ATMSNodeStatus,
        *,
        limit: int | None,
        max_suggestions: int | None = None,
    ) -> list[ATMSNextQuerySuggestion]:
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
        target_value_status: ValueStatus,
        *,
        limit: int | None,
        max_suggestions: int | None = None,
    ) -> list[ATMSNextQuerySuggestion]:
        self._require_atms_backend()
        return self.atms_engine().next_queryables_for_concept(
            concept_id,
            coerce_queryable_assumptions(queryables),
            target_value_status,
            limit=limit,
            max_suggestions=max_suggestions,
        )

    def why_concept_out(
        self,
        concept_id: str,
        queryables: Sequence[QueryableInput] | None = None,
        *,
        limit: int | None,
    ) -> dict[str, Any]:
        self._require_atms_backend()
        normalized_queryables = (
            None if queryables is None else coerce_queryable_assumptions(queryables)
        )
        supported_ids = self.atms_engine().supported_claim_ids(concept_id)
        claim_reasons = {
            str(claim.claim_id): self.atms_engine().why_out(
                self.claim_status(str(claim.claim_id)).node_id,
                queryables=normalized_queryables,
                limit=limit,
            )
            for claim in sorted(self.active_claims(concept_id), key=lambda row: str(row.claim_id))
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
        """Return assertion ids whose exact ATMS support is visible in the environment."""

        return [
            node_id
            for node_id in self.atms_engine().nodes_in_environment(environment)
            if node_id.startswith("ps:assertion:")
        ]

    def explain_claim_support(self, claim_id: str) -> ATMSNodeExplanation:
        return self.atms_engine().explain_node(self.claim_status(claim_id).node_id)

    # -- revision surface (owned by propstore.support_revision) -------------
    # The AGM / Darwiche-Pearl revision surface projects this bound world into a
    # scoped belief base and delegates the formal decision to
    # ``propstore.support_revision``. The projection/entrenchment/explanation/
    # iterated/history modules are imported lazily inside the method bodies to keep
    # the eager import graph acyclic (those modules read a BoundWorld back).

    def revision_base(self) -> BeliefBase:
        """Project this bound world into a revision-facing belief base."""

        from propstore.support_revision.projection import project_belief_base

        return project_belief_base(self)

    def revision_entrenchment(
        self,
        *,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> EntrenchmentReport:
        """Compute the current revision-facing entrenchment ordering."""

        from propstore.support_revision.entrenchment import compute_entrenchment

        return compute_entrenchment(self, self.revision_base(), overrides=overrides)

    def expand(self, atom: BeliefAtom | str | Mapping[str, Any]) -> RevisionResult:
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
        targets: BeliefAtom | str | Mapping[str, Any] | Sequence[BeliefAtom | str | Mapping[str, Any]],
        *,
        max_candidates: int,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> RevisionResult:
        """Contract the scoped revision belief base using the current entrenchment."""

        base = self.revision_base()
        target_ids = _normalize_revision_targets(base, targets)
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
        atom: BeliefAtom | str | Mapping[str, Any],
        *,
        max_candidates: int,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
        conflicts: Mapping[str, tuple[str, ...] | list[str]] | None = None,
    ) -> RevisionResult:
        """Revise the scoped belief base by delegating to the revision package."""

        base = self.revision_base()
        normalized = normalize_revision_input(base, atom)
        decision = decide_revise(
            base,
            normalized,
            conflicts=_conflicts_for_revision_atom(normalized.atom_id, conflicts),
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
        result: RevisionResult,
        *,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> RevisionExplanation:
        """Render the default explanation payload for a revision result."""

        from propstore.support_revision.explain import build_revision_explanation

        return build_revision_explanation(
            result,
            entrenchment=self.revision_entrenchment(overrides=overrides),
        )

    def epistemic_state(
        self,
        *,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> EpistemicState:
        """Build the explicit iterated revision state for this scoped world."""

        from propstore.support_revision.iterated import make_epistemic_state

        return make_epistemic_state(
            self.revision_base(),
            self.revision_entrenchment(overrides=overrides),
        )

    def revision_state_snapshot(self, state: EpistemicState) -> EpistemicSnapshot:
        """Render an iterated revision state as the worldline persistence payload."""

        from propstore.support_revision.history import EpistemicSnapshot

        return EpistemicSnapshot.from_state(state)

    def iterated_revise(
        self,
        atom: BeliefAtom | str | Mapping[str, Any],
        *,
        max_candidates: int,
        overrides: Mapping[str, Mapping[str, Any]] | None = None,
        conflicts: Mapping[str, tuple[str, ...] | list[str]] | None = None,
        operator: str = DEFAULT_ITERATED_OPERATOR,
        state: EpistemicState | None = None,
    ) -> tuple[RevisionResult, EpistemicState]:
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


def _normalize_revision_targets(
    base: BeliefBase,
    targets: BeliefAtom
    | str
    | Mapping[str, Any]
    | Sequence[BeliefAtom | str | Mapping[str, Any]],
) -> tuple[str, ...]:
    """Normalize one-or-many contract targets to their belief-atom ids."""

    if isinstance(targets, AssertionAtom | AssumptionAtom | str | Mapping):
        return (normalize_revision_input(base, targets).atom_id,)
    return tuple(normalize_revision_input(base, target).atom_id for target in targets)


def _conflicts_for_revision_atom(
    atom_id: str,
    conflicts: Mapping[str, Sequence[str]] | None,
) -> tuple[str, ...]:
    """Resolve the conflicting atom ids declared for one revision input atom."""

    if conflicts is None:
        return ()
    return tuple(str(conflict) for conflict in conflicts.get(atom_id, ()))
