"""Shared conflict detector models."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, cast

from propstore.cel_types import CelExpr, to_cel_expr, to_cel_exprs


@dataclass(frozen=True)
class ConflictClaimVariable:
    concept_id: str
    symbol: str | None = None
    role: str | None = None
    name: str | None = None


@dataclass(frozen=True)
class ConflictClaim:
    claim_id: str
    claim_type: str | None = None
    artifact_id: str | None = None
    output_concept_id: str | None = None
    target_concept_id: str | None = None
    measure: str | None = None
    value: Any = None
    lower_bound: float | int | None = None
    upper_bound: float | int | None = None
    unit: str | None = None
    expression: str | None = None
    sympy: str | None = None
    body: str | None = None
    listener_population: str | None = None
    source_paper: str | None = None
    context_id: str | None = None
    conditions: tuple[CelExpr, ...] = field(default_factory=tuple)
    variables: tuple[ConflictClaimVariable, ...] = field(default_factory=tuple)

    def with_source_condition(self) -> ConflictClaim:
        if not self.source_paper:
            return self
        source_cond = f"source == '{self.source_paper}'"
        if source_cond in self.conditions:
            return self
        return replace(
            self, conditions=tuple((*self.conditions, to_cel_expr(source_cond)))
        )


@dataclass(frozen=True)
class ConflictParameterization:
    inputs: tuple[str, ...]
    sympy: str | None
    exactness: str | None
    conditions: tuple[CelExpr, ...] = ()


@dataclass(frozen=True)
class ConflictConcept:
    concept_id: str
    canonical_name: str | None
    form_name: str | None
    reference_keys: tuple[str, ...] = ()
    form_definition: object | None = None
    parameterizations: tuple[ConflictParameterization, ...] = ()

    def __post_init__(self) -> None:
        if not self.concept_id:
            raise ValueError("conflict concept requires concept_id")
        keys: list[str] = []
        seen: set[str] = set()

        def add(candidate: object) -> None:
            if not isinstance(candidate, str) or not candidate or candidate in seen:
                return
            seen.add(candidate)
            keys.append(candidate)

        add(self.concept_id)
        add(self.canonical_name)
        for key in self.reference_keys:
            add(key)
        object.__setattr__(self, "reference_keys", tuple(keys))

    def symbol_candidates(self) -> tuple[str, ...]:
        return self.reference_keys


@dataclass(frozen=True)
class ConflictConceptRegistry:
    concepts: tuple[ConflictConcept, ...]
    _by_id: dict[str, ConflictConcept] = field(init=False, repr=False, compare=False)
    _by_key: dict[str, ConflictConcept] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        by_id: dict[str, ConflictConcept] = {}
        by_key: dict[str, ConflictConcept] = {}
        for concept in self.concepts:
            existing = by_id.get(concept.concept_id)
            if existing is not None:
                raise ValueError(
                    f"conflicting concept registry entries for concept id '{concept.concept_id}'"
                )
            by_id[concept.concept_id] = concept
            for key in concept.reference_keys:
                by_key.setdefault(key, concept)
        object.__setattr__(self, "_by_id", by_id)
        object.__setattr__(self, "_by_key", by_key)

    def get(self, concept_ref: str) -> ConflictConcept | None:
        return self._by_key.get(concept_ref)

    def unique_concepts(self) -> tuple[ConflictConcept, ...]:
        return self.concepts

    def form_definitions(self) -> dict[str, object]:
        forms: dict[str, object] = {}
        for concept in self.concepts:
            if concept.form_name is not None and concept.form_definition is not None:
                forms.setdefault(concept.form_name, concept.form_definition)
        return forms

    def concept_forms(self) -> dict[str, str]:
        concept_forms: dict[str, str] = {}
        for concept in self.concepts:
            if concept.form_name is None:
                continue
            for key in concept.reference_keys:
                concept_forms.setdefault(key, concept.form_name)
        return concept_forms

    def form_name(self, concept_ref: str) -> str | None:
        concept = self.get(concept_ref)
        return None if concept is None else concept.form_name

    def parameterization_edges(
        self,
        *,
        exactness_filter: set[str] | None = None,
    ) -> dict[str, tuple[ConflictParameterization, ...]]:
        edges: dict[str, tuple[ConflictParameterization, ...]] = {}
        for concept in self.concepts:
            kept: list[ConflictParameterization] = []
            for parameterization in concept.parameterizations:
                exactness = parameterization.exactness or ""
                if exactness_filter is not None and exactness not in exactness_filter:
                    continue
                if not parameterization.inputs or not parameterization.sympy:
                    continue
                kept.append(parameterization)
            if kept:
                edges[concept.concept_id] = tuple(kept)
        return edges

    def parameterization_groups(self) -> list[set[str]]:
        if not self.concepts:
            return []

        all_ids = {concept.concept_id for concept in self.concepts}
        alias_to_id = {
            key: concept.concept_id
            for concept in self.concepts
            for key in concept.reference_keys
        }
        parent: dict[str, str] = {concept_id: concept_id for concept_id in all_ids}
        rank: dict[str, int] = {concept_id: 0 for concept_id in all_ids}

        def find(value: str) -> str:
            while parent[value] != value:
                parent[value] = parent[parent[value]]
                value = parent[value]
            return value

        def union(left: str, right: str) -> None:
            left_root, right_root = find(left), find(right)
            if left_root == right_root:
                return
            if rank[left_root] < rank[right_root]:
                left_root, right_root = right_root, left_root
            parent[right_root] = left_root
            if rank[left_root] == rank[right_root]:
                rank[left_root] += 1

        for concept in self.concepts:
            for parameterization in concept.parameterizations:
                for input_id in parameterization.inputs:
                    resolved_input_id = alias_to_id.get(input_id, input_id)
                    if resolved_input_id in all_ids:
                        union(concept.concept_id, resolved_input_id)

        components: dict[str, set[str]] = {}
        for concept_id in all_ids:
            root = find(concept_id)
            components.setdefault(root, set()).add(concept_id)
        return list(components.values())


class ConflictClass(Enum):
    COMPATIBLE = "COMPATIBLE"
    UNKNOWN = "UNKNOWN"
    PHI_NODE = "PHI_NODE"
    CONFLICT = "CONFLICT"
    OVERLAP = "OVERLAP"
    PARAM_CONFLICT = "PARAM_CONFLICT"
    CONTEXT_PHI_NODE = "CONTEXT_PHI_NODE"


@dataclass
class ConflictRecord:
    concept_id: str
    claim_a_id: str
    claim_b_id: str
    warning_class: ConflictClass
    conditions_a: list[CelExpr]
    conditions_b: list[CelExpr]
    value_a: str
    value_b: str
    derivation_chain: str | None = None
