"""Charter-native in-memory feed for the ATMS engine + BoundWorld tests.

Phase 7a-world-B2 exercises ``BoundWorld`` and ``ATMSEngine`` over the
``WorldStore`` protocol; the concrete repo-backed store is Phase 9. This module
stands in for one: :func:`build_bound` lowers lightweight claim/parameterization
specs into ``Claim`` / ``ParameterizationEdge`` / ``ConflictRecord`` charters,
compiles the world graph, activates it under an environment, and returns a
``BoundWorld``. Condition reasoning uses a condition-ir registry inferred from the
referenced CEL identifiers.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from condition_ir import (
    ConceptInfo,
    ConditionSolver,
    KindType,
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_from_json,
    checked_condition_set_to_json,
    with_standard_synthetic_bindings,
)

from propstore.conflict_detector.models import ConflictClass, ConflictRecord
from propstore.core.activation import activate_compiled_world_graph
from propstore.core.environment import Environment
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.graph_types import ParameterizationEdge, RelationEdge
from propstore.core.labels import (
    binding_condition_to_cel,
    compile_environment_assumptions,
)
from propstore.core.scalars import ScalarValue
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.families.micropublications import Micropublication
from propstore.families.relations import Stance
from propstore.world.bound import BoundWorld
from propstore.world.types import ReasoningBackend, RenderPolicy

_NAME_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b\s*(?:==|!=|<=|>=|<|>|in\b)")


def registry_for_sources(sources: Sequence[str]) -> dict[str, ConceptInfo]:
    """Infer a condition-ir registry from the identifiers used in CEL sources."""

    names: dict[str, KindType] = {}
    for source in sources:
        for name in _NAME_RE.findall(source):
            quoted = (
                f"{name} == '" in source
                or f'{name} == "' in source
                or f"{name} != '" in source
                or f'{name} != "' in source
            )
            names[name] = (
                KindType.CATEGORY if quoted else names.get(name, KindType.QUANTITY)
            )
    return with_standard_synthetic_bindings(
        {
            name: ConceptInfo(
                id=name,
                canonical_name=name,
                kind=kind,
                category_extensible=True,
            )
            for name, kind in names.items()
        }
    )


def _conditions_ir(
    conditions: Sequence[str], registry: dict[str, ConceptInfo]
) -> str | None:
    if not conditions:
        return None
    return json.dumps(
        checked_condition_set_to_json(
            checked_condition_set(
                check_condition_ir(source, registry) for source in conditions
            )
        ),
        sort_keys=True,
    )


@dataclass(frozen=True)
class ClaimSpec:
    claim_id: str
    concept_id: str
    value: ScalarValue | None = None
    claim_type: ClaimType = ClaimType.PARAMETER
    conditions: tuple[str, ...] = ()
    context_id: str | None = None
    body: str | None = None
    sample_size: int | None = None


@dataclass(frozen=True)
class ParamSpec:
    output: str
    inputs: tuple[str, ...]
    sympy: str
    formula: str | None = None
    conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConflictSpec:
    concept_id: str
    claim_a_id: str
    claim_b_id: str
    warning_class: ConflictClass = ConflictClass.CONFLICT
    value_a: str = ""
    value_b: str = ""


@dataclass(frozen=True)
class MicropubSpec:
    artifact_id: str
    context_id: str
    claim_ids: tuple[str, ...]


@dataclass
class InMemoryWorldStore:
    """A minimal charter-backed ``WorldStore`` for world-layer tests."""

    concepts: tuple[Concept, ...] = ()
    claims: tuple[Claim, ...] = ()
    parameterizations: tuple[ParameterizationEdge, ...] = ()
    conflict_records: tuple[ConflictRecord, ...] = ()
    stances: tuple[Stance, ...] = ()
    micropublications: tuple[Micropublication, ...] = ()
    forms: tuple[FormDefinition, ...] = ()
    solver: ConditionSolver = field(default_factory=lambda: ConditionSolver({}))

    def all_concepts(self) -> Sequence[Concept]:
        return self.concepts

    def all_forms(self) -> Sequence[FormDefinition]:
        return self.forms

    def claims_for(self, concept_id: str | None) -> Sequence[Claim]:
        if concept_id is None:
            return self.claims
        return [
            claim
            for claim in self.claims
            if concept_id
            in (claim.output_concept, claim.target_concept, *claim.concepts)
        ]

    def get_claim(self, claim_id: str) -> Claim | None:
        return next(
            (claim for claim in self.claims if claim.claim_id == claim_id), None
        )

    def get_concept(self, concept_id: str) -> Concept | None:
        return next(
            (
                concept
                for concept in self.concepts
                if str(concept.concept_id) == concept_id
            ),
            None,
        )

    def resolve_claim(self, name: str) -> str | None:
        return name if self.get_claim(name) is not None else None

    def resolve_concept(self, name: str) -> str | None:
        return name if self.get_concept(name) is not None else name

    def all_parameterizations(self) -> Sequence[ParameterizationEdge]:
        return self.parameterizations

    def all_relationships(self) -> Sequence[RelationEdge]:
        return ()

    def parameterizations_for(self, concept_id: str) -> Sequence[ParameterizationEdge]:
        return [
            edge
            for edge in self.parameterizations
            if str(edge.output_concept_id) == concept_id
        ]

    def group_members(self, concept_id: str) -> list[str]:
        """Concepts reachable from ``concept_id`` through parameterization edges.

        Walks each edge as connecting its output to its inputs in both
        directions, returning the connected component (the chain-query group).
        """

        adjacency: dict[str, set[str]] = {}
        for edge in self.parameterizations:
            output = str(edge.output_concept_id)
            for raw_input in edge.input_concept_ids:
                neighbour = str(raw_input)
                adjacency.setdefault(output, set()).add(neighbour)
                adjacency.setdefault(neighbour, set()).add(output)
        seen: set[str] = {concept_id}
        frontier = [concept_id]
        while frontier:
            current = frontier.pop()
            for neighbour in adjacency.get(current, set()):
                if neighbour not in seen:
                    seen.add(neighbour)
                    frontier.append(neighbour)
        return sorted(seen)

    def conflicts(self) -> Sequence[ConflictRecord]:
        return self.conflict_records

    def all_claim_stances(self) -> Sequence[Stance]:
        return self.stances

    def stances_between(self, claim_ids: set[str]) -> Sequence[Stance]:
        return [
            stance
            for stance in self.stances
            if stance.source_claim_id in claim_ids
            and stance.target_claim_id in claim_ids
        ]

    def all_micropublications(self) -> Sequence[Micropublication]:
        return self.micropublications

    def explain(self, claim_id: str) -> Sequence[Stance]:
        return [
            stance for stance in self.stances if str(stance.target_claim_id) == claim_id
        ]

    def condition_solver(self) -> ConditionSolver:
        return self.solver


def build_bound(
    *,
    claims: Sequence[ClaimSpec],
    parameterizations: Sequence[ParamSpec] = (),
    conflicts: Sequence[ConflictSpec] = (),
    micropublications: Sequence[MicropubSpec] = (),
    bindings: dict[str, object] | None = None,
    context_id: str | None = None,
    effective_assumptions: Sequence[str] = (),
    policy: RenderPolicy | None = None,
    backend: ReasoningBackend = ReasoningBackend.ATMS,
) -> BoundWorld:
    """Build a ``BoundWorld`` from lightweight specs under an environment."""

    bindings = dict(bindings or {})
    binding_sources = [
        binding_condition_to_cel(key, value) for key, value in bindings.items()
    ]
    all_sources: list[str] = [str(source) for source in binding_sources]
    all_sources.extend(str(source) for source in effective_assumptions)
    for claim in claims:
        all_sources.extend(claim.conditions)
    for param in parameterizations:
        all_sources.extend(param.conditions)
    registry = registry_for_sources(all_sources)
    solver = ConditionSolver(registry)

    concept_ids: set[str] = set()
    for claim in claims:
        concept_ids.add(claim.concept_id)
    for param in parameterizations:
        concept_ids.add(param.output)
        concept_ids.update(param.inputs)
    concept_objs = tuple(
        Concept(concept_id=concept_id, canonical_name=concept_id)
        for concept_id in sorted(concept_ids)
    )

    claim_objs = tuple(
        Claim(
            claim_id=spec.claim_id,
            claim_type=spec.claim_type,
            output_concept=spec.concept_id,
            value=spec.value,
            body=spec.body,
            sample_size=spec.sample_size,
            context_id=spec.context_id,
            conditions=tuple(spec.conditions),
            conditions_ir=_conditions_ir(spec.conditions, registry),
        )
        for spec in claims
    )

    param_objs = tuple(
        ParameterizationEdge(
            output_concept_id=param.output,
            input_concept_ids=tuple(param.inputs),
            sympy=param.sympy,
            formula=param.formula,
            checked_conditions=(
                None
                if not param.conditions
                else checked_condition_set_from_json(
                    json.loads(_conditions_ir(param.conditions, registry) or "{}")
                )
            ),
        )
        for param in parameterizations
    )

    conflict_objs = tuple(
        ConflictRecord(
            concept_id=spec.concept_id,
            claim_a_id=spec.claim_a_id,
            claim_b_id=spec.claim_b_id,
            warning_class=spec.warning_class,
            conditions_a=[],
            conditions_b=[],
            value_a=spec.value_a,
            value_b=spec.value_b,
        )
        for spec in conflicts
    )

    micropub_objs = tuple(
        Micropublication(
            artifact_id=spec.artifact_id,
            context_id=spec.context_id,
            claims=tuple(spec.claim_ids),
            source="src:test",
        )
        for spec in micropublications
    )

    store = InMemoryWorldStore(
        concepts=concept_objs,
        claims=claim_objs,
        parameterizations=param_objs,
        conflict_records=conflict_objs,
        micropublications=micropub_objs,
        solver=solver,
    )
    environment = Environment(
        bindings=bindings,
        context_id=context_id,
        effective_assumptions=tuple(effective_assumptions),
        assumptions=compile_environment_assumptions(
            bindings=bindings,
            effective_assumptions=effective_assumptions,
            context_id=context_id,
        ),
    )
    compiled = build_compiled_world_graph(store)
    active = activate_compiled_world_graph(
        compiled, environment=environment, solver=solver
    )
    effective_policy = policy or RenderPolicy(reasoning_backend=backend)
    return BoundWorld(
        store, environment=environment, policy=effective_policy, active_graph=active
    )


def assumption_id_for(bound: BoundWorld, cel: str) -> str:
    """The compiled assumption id whose CEL is ``cel`` (test convenience)."""

    for assumption in bound.environment.assumptions:
        if str(assumption.cel) == cel:
            return str(assumption.assumption_id)
    raise KeyError(f"no environment assumption with cel {cel!r}")
