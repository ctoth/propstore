"""Core label types and helpers for the ATMS-style belief-space kernel."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from propstore.cel_types import CelExpr, to_cel_expr, to_cel_exprs
from propstore.core.id_types import (
    AssumptionId,
    ContextId,
    to_assumption_id,
    to_assumption_ids,
    to_context_id,
)
from propstore.provenance.polynomial import ProvenancePolynomial
from propstore.provenance import Provenance, ProvenanceStatus
from propstore.provenance.nogoods import NogoodWitness, ProvenanceNogood, live
from propstore.provenance.support import SupportEvidence, SupportQuality
from propstore.provenance.variables import SourceVariableId

SupportMetadata = Mapping[str, tuple["Label | None", SupportQuality]]


@dataclass(frozen=True, order=True)
class AssumptionRef:
    """Compiled assumption with stable identity for in-memory label use."""

    assumption_id: AssumptionId
    kind: str
    source: str
    cel: CelExpr

    def __post_init__(self) -> None:
        object.__setattr__(self, "cel", to_cel_expr(self.cel))


@dataclass(frozen=True, order=True)
class EnvironmentKey:
    """Immutable set of supporting assumption and context IDs."""

    assumption_ids: tuple[AssumptionId, ...] = ()
    context_ids: tuple[ContextId, ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(sorted(dict.fromkeys(to_assumption_ids(self.assumption_ids))))
        object.__setattr__(self, "assumption_ids", normalized)
        normalized_contexts = tuple(
            sorted(dict.fromkeys(to_context_id(value) for value in self.context_ids))
        )
        object.__setattr__(self, "context_ids", normalized_contexts)

    def union(self, other: EnvironmentKey) -> EnvironmentKey:
        return EnvironmentKey(
            self.assumption_ids + other.assumption_ids,
            context_ids=self.context_ids + other.context_ids,
        )

    def subsumes(self, other: EnvironmentKey) -> bool:
        return (
            set(self.assumption_ids).issubset(other.assumption_ids)
            and set(self.context_ids).issubset(other.context_ids)
        )


@dataclass(frozen=True, init=False)
class NogoodSet:
    """Minimal inconsistent environments projected from provenance nogoods."""

    provenance_nogoods: tuple[ProvenanceNogood, ...]

    def __init__(
        self,
        environments: Iterable[EnvironmentKey] = (),
        *,
        provenance_nogoods: Iterable[ProvenanceNogood] | None = None,
    ) -> None:
        if provenance_nogoods is None:
            provenance_nogoods = tuple(
                _environment_to_provenance_nogood(environment)
                for environment in normalize_environments(environments)
            )
        object.__setattr__(
            self,
            "provenance_nogoods",
            tuple(provenance_nogoods),
        )

    @property
    def environments(self) -> tuple[EnvironmentKey, ...]:
        return normalize_environments(
            _provenance_nogood_to_environment(nogood)
            for nogood in self.provenance_nogoods
        )

    def excludes(self, environment: EnvironmentKey) -> bool:
        support = _environment_to_polynomial(environment)
        return not live(support, self.provenance_nogoods).terms


def normalize_environments(
    environments: Iterable[EnvironmentKey],
    *,
    nogoods: NogoodSet | None = None,
) -> tuple[EnvironmentKey, ...]:
    """Deduplicate, prune supersets, and drop known-nogood environments."""
    unique = {
        (env.assumption_ids, env.context_ids): env
        for env in environments
        if nogoods is None or not nogoods.excludes(env)
    }
    ordered = sorted(
        unique.values(),
        key=lambda env: (
            len(env.assumption_ids) + len(env.context_ids),
            env.assumption_ids,
            env.context_ids,
        ),
    )
    minimal: list[EnvironmentKey] = []
    for candidate in ordered:
        if any(existing.subsumes(candidate) for existing in minimal):
            continue
        minimal.append(candidate)
    return tuple(minimal)


@dataclass(frozen=True, init=False, eq=False)
class Label:
    """Minimal antichain of supporting environments projected from support."""

    support: SupportEvidence

    def __init__(
        self,
        environments: Iterable[EnvironmentKey] = (),
        *,
        support: SupportEvidence | None = None,
    ) -> None:
        if support is None:
            normalized = normalize_environments(environments)
            support = SupportEvidence(
                _environments_to_polynomial(normalized),
                SupportQuality.EXACT,
            )
        object.__setattr__(self, "support", support)

    @property
    def environments(self) -> tuple[EnvironmentKey, ...]:
        return _polynomial_to_environments(self.support.polynomial)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Label):
            return NotImplemented
        return self.environments == other.environments

    def __hash__(self) -> int:
        return hash(self.environments)

    @classmethod
    def empty(cls) -> Label:
        """Unconditional support: the empty environment."""
        return cls((EnvironmentKey(()),))

    @classmethod
    def singleton(cls, assumption: AssumptionRef) -> Label:
        return cls((EnvironmentKey((assumption.assumption_id,)),))

    @classmethod
    def context(cls, context_id: ContextId | str) -> Label:
        return cls((EnvironmentKey((), context_ids=(to_context_id(context_id),)),))


def binding_condition_to_cel(key: str, value: Any) -> CelExpr:
    """Render a query binding into the CEL string used elsewhere in the world model."""
    if isinstance(value, str):
        return to_cel_expr(f"{key} == '{value}'")
    if isinstance(value, bool):
        return to_cel_expr(f"{key} == {'true' if value else 'false'}")
    return to_cel_expr(f"{key} == {value}")


@dataclass(frozen=True)
class JustificationRecord:
    """Compiled justification result for a conclusion."""

    conclusion: str
    antecedents: tuple[Label, ...]
    label: Label

    @classmethod
    def from_antecedents(
        cls,
        conclusion: str,
        antecedents: Sequence[Label],
        *,
        nogoods: NogoodSet | None = None,
    ) -> JustificationRecord:
        return cls(
            conclusion=conclusion,
            antecedents=tuple(antecedents),
            label=combine_labels(*antecedents, nogoods=nogoods),
        )


def cel_to_binding(cel: str | CelExpr) -> tuple[str, Any] | None:
    """Reverse of binding_condition_to_cel: parse 'key == value' back to (key, value)."""
    parts = str(cel).split(" == ", 1)
    if len(parts) != 2:
        return None
    key, raw = parts[0].strip(), parts[1].strip()
    if not key:
        return None
    if raw.startswith("'") and raw.endswith("'"):
        return (key, raw[1:-1])
    if raw == "true":
        return (key, True)
    if raw == "false":
        return (key, False)
    try:
        if "." in raw:
            return (key, float(raw))
        return (key, int(raw))
    except ValueError:
        return None


def compile_environment_assumptions(
    *,
    bindings: Mapping[str, Any],
    effective_assumptions: Sequence[str | CelExpr] = (),
    context_id: ContextId | str | None = None,
) -> tuple[AssumptionRef, ...]:
    """Compile bindings and inherited context assumptions into stable refs."""
    compiled: list[AssumptionRef] = []

    for key in sorted(bindings):
        value = bindings[key]
        rendered_value = json.dumps(value, sort_keys=True, default=str)
        compiled.append(
            AssumptionRef(
                assumption_id=_stable_id("binding", key, rendered_value),
                kind="binding",
                source=key,
                cel=binding_condition_to_cel(key, value),
            )
        )

    normalized_context_id = None if context_id is None else to_context_id(context_id)
    context_source = normalized_context_id or "<context>"
    for cel in sorted(dict.fromkeys(to_cel_exprs(effective_assumptions))):
        compiled.append(
            AssumptionRef(
                assumption_id=_stable_id("context", str(context_source), str(cel)),
                kind="context",
                source=str(context_source),
                cel=cel,
            )
        )

    return tuple(sorted(compiled, key=lambda ref: ref.assumption_id))


def combine_labels(
    *labels: Label,
    nogoods: NogoodSet | None = None,
) -> Label:
    """Combine antecedent labels by cross-product union."""
    if not labels:
        return Label.empty()

    support = ProvenancePolynomial.one()
    for label in labels:
        if label.support.polynomial.is_zero():
            return Label(())
        support = support * label.support.polynomial
        if nogoods is not None:
            support = live(support, nogoods.provenance_nogoods)
        if support.is_zero():
            return Label(())
    return Label(support=SupportEvidence(support, SupportQuality.EXACT))


def merge_labels(
    labels: Iterable[Label],
    *,
    nogoods: NogoodSet | None = None,
) -> Label:
    """Merge alternative supports for the same datum into one normalized label."""
    support = ProvenancePolynomial.zero()
    for label in labels:
        support = support + label.support.polynomial
    environments = normalize_environments(_polynomial_to_environments(support), nogoods=nogoods)
    return Label(support=SupportEvidence(_environments_to_polynomial(environments), SupportQuality.EXACT))


_ASSUMPTION_VAR_PREFIX = "ps:source:assumption:"
_CONTEXT_VAR_PREFIX = "ps:source:context:"


def label_to_polynomial(label: Label) -> ProvenancePolynomial:
    return label.support.polynomial


def polynomial_to_label(poly: ProvenancePolynomial) -> Label:
    return Label(support=SupportEvidence(poly, SupportQuality.EXACT))


def _environment_to_provenance_nogood(environment: EnvironmentKey) -> ProvenanceNogood:
    variables = frozenset(
        power.variable
        for term in _environment_to_polynomial(environment).terms
        for power in term.powers
    )
    return ProvenanceNogood(
        variables=variables,
        witness=NogoodWitness(
            source="core.labels.NogoodSet",
            detail="ATMS inconsistent environment projected to provenance nogood",
        ),
        provenance=Provenance(
            status=ProvenanceStatus.VACUOUS,
            witnesses=(),
            operations=("atms-nogood-projection",),
        ),
    )


def _provenance_nogood_to_environment(nogood: ProvenanceNogood) -> EnvironmentKey:
    assumptions: list[AssumptionId] = []
    contexts: list[ContextId] = []
    for variable in sorted(nogood.variables, key=str):
        assumption, context = _variable_to_environment_piece(variable)
        if assumption is not None:
            assumptions.append(assumption)
        if context is not None:
            contexts.append(context)
    return EnvironmentKey(tuple(assumptions), context_ids=tuple(contexts))


def _assumption_variable(assumption_id: AssumptionId) -> SourceVariableId:
    return SourceVariableId(f"{_ASSUMPTION_VAR_PREFIX}{assumption_id}")


def _context_variable(context_id: ContextId) -> SourceVariableId:
    return SourceVariableId(f"{_CONTEXT_VAR_PREFIX}{context_id}")


def _variable_to_environment_piece(variable: SourceVariableId) -> tuple[AssumptionId | None, ContextId | None]:
    value = str(variable)
    if value.startswith(_ASSUMPTION_VAR_PREFIX):
        return to_assumption_id(value.removeprefix(_ASSUMPTION_VAR_PREFIX)), None
    if value.startswith(_CONTEXT_VAR_PREFIX):
        return None, to_context_id(value.removeprefix(_CONTEXT_VAR_PREFIX))
    return to_assumption_id(value), None


def _environment_to_polynomial(environment: EnvironmentKey) -> ProvenancePolynomial:
    support = ProvenancePolynomial.one()
    for assumption_id in environment.assumption_ids:
        support = support * ProvenancePolynomial.variable(_assumption_variable(assumption_id))
    for context_id in environment.context_ids:
        support = support * ProvenancePolynomial.variable(_context_variable(context_id))
    return support


def _environments_to_polynomial(environments: Iterable[EnvironmentKey]) -> ProvenancePolynomial:
    support = ProvenancePolynomial.zero()
    for environment in environments:
        support = support + _environment_to_polynomial(environment)
    return support


def _polynomial_to_environments(poly: ProvenancePolynomial) -> tuple[EnvironmentKey, ...]:
    environments: list[EnvironmentKey] = []
    for term in poly.terms:
        assumptions: list[AssumptionId] = []
        contexts: list[ContextId] = []
        for power in term.powers:
            assumption, context = _variable_to_environment_piece(power.variable)
            if assumption is not None:
                assumptions.append(assumption)
            if context is not None:
                contexts.append(context)
        environments.append(EnvironmentKey(tuple(assumptions), context_ids=tuple(contexts)))
    return normalize_environments(environments)


def _stable_id(kind: str, source: str, body: str) -> AssumptionId:
    digest = hashlib.sha256(f"{kind}\0{source}\0{body}".encode("utf-8")).hexdigest()
    return to_assumption_id(f"{kind}:{source}:{digest}")
