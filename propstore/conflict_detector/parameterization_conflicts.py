"""Parameterization-derived conflict detection.

A concept may carry authored ``parameterization_relationships`` — a SymPy
expression deriving its value from input concepts. When direct claims exist both
for an input and for the output, the output's derived value can disagree with its
directly-claimed value; that disagreement is a :attr:`ConflictClass.PARAM_CONFLICT`
(or a context φ-node when the contexts do not lift into one another).

Two passes share the same single-hop derivation/comparison machinery:

* :func:`_detect_parameterization_conflicts` — single-hop: derive each output from
  its direct inputs and compare against the output's direct claims.
* :func:`detect_transitive_conflicts` — multi-hop: within each parameterization
  connected component, iterate derivations to a fixpoint and compare only the
  genuinely transitive (``hop_count >= 2``) derivations against direct claims.

Numeric evaluation of the SymPy strings is delegated to the ``human-to-sympy``
substrate (``evaluate_numeric``); SymPy is never imported here. Authored symbol
spellings in the expression are rewritten to safe placeholders before evaluation
so caller-stored concept ids and authored handles both resolve.
"""

from __future__ import annotations

import enum
import re
import warnings
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from typing import TYPE_CHECKING, Any

from condition_ir import CelExpr, to_cel_exprs
from human_to_sympy import (
    NumericEvaluation,
    NumericEvaluationStatus,
    evaluate_numeric,
)

from propstore.dimensions import normalize_to_si
from propstore.parameterization import build_parameterization_groups
from propstore.value_comparison import (
    DEFAULT_TOLERANCE,
    extract_interval,
    value_str,
    values_compatible,
)

from .collectors import collect_parameter_claims
from .context import claim_context, classify_pair_context
from .models import ConflictClass, ConflictClaim, ConflictRecord, payload_get

if TYPE_CHECKING:
    from propstore.families.forms import FormDefinition
    from propstore.context_lifting import LiftingSystem


# The concept registry is a genuinely untyped stored JSON/YAML payload; ``Any``
# is the codebase's sanctioned boundary spelling for it (cf. ``models.py`` /
# ``orchestrator.py``). Every value read out of it is narrowed before use.
ConceptRegistry = Mapping[str, Mapping[str, Any]]
_RecordKey = tuple[
    str, str, tuple[str, ...], str, tuple[CelExpr, ...], str | None, str
]
_StateKey = tuple[str, str, tuple[str, ...], tuple[CelExpr, ...], str | None, int]


@dataclass(frozen=True)
class DerivedConflictValue:
    concept_id: str
    value: float
    source_claim_ids: tuple[str, ...]
    conditions: tuple[CelExpr, ...]
    context_id: str | None
    derivation_chain: str
    hop_count: int
    unit: str | None = None


@dataclass(frozen=True)
class _ParameterizationEdge:
    inputs: tuple[str, ...]
    sympy: str
    conditions: tuple[str, ...]
    exactness: str


class _Sentinel(enum.Enum):
    INCOHERENT_CONTEXT = "INCOHERENT_CONTEXT"


_INCOHERENT_CONTEXT = _Sentinel.INCOHERENT_CONTEXT
_SAFE_SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_KNOWN_EVALUATION_ERRORS = (
    TypeError,
    ValueError,
    ZeroDivisionError,
    AssertionError,
)


# --- Concept-registry narrowing ------------------------------------------------
# The concept registry is a genuinely untyped stored payload. These helpers are
# the single narrowing points that read concept fields and return concrete types.


def _string_sequence(value: Any) -> tuple[str, ...]:
    """Coerce an untyped stored list field to a tuple of strings.

    The value flows from an untyped concept-registry ``.get``; ``or ()``
    guards a missing field.
    """

    return tuple(str(item) for item in (value or ()))


def _iter_unique_concepts(
    concept_registry: ConceptRegistry,
) -> list[tuple[str, Mapping[str, Any]]]:
    unique: list[tuple[str, Mapping[str, Any]]] = []
    seen_ids: set[str] = set()
    for concept_data in concept_registry.values():
        raw_id = concept_data.get("artifact_id") or concept_data.get("id")
        if not isinstance(raw_id, str) or not raw_id or raw_id in seen_ids:
            continue
        seen_ids.add(raw_id)
        unique.append((raw_id, concept_data))
    return unique


def _concept_symbol_candidates(concept_data: Mapping[str, Any]) -> tuple[str, ...]:
    candidates: list[str] = []
    seen: set[str] = set()

    def add(candidate: object) -> None:
        if not isinstance(candidate, str) or not candidate or candidate in seen:
            return
        if not _SAFE_SYMBOL_RE.match(candidate):
            return
        seen.add(candidate)
        candidates.append(candidate)

    add(concept_data.get("canonical_name"))
    for logical_id in concept_data.get("logical_ids") or ():
        add(payload_get(logical_id, "value"))
    return tuple(candidates)


def _concept_aliases(concept_registry: ConceptRegistry, concept_id: str) -> tuple[str, ...]:
    entry = concept_registry.get(concept_id)
    return _concept_symbol_candidates(entry) if isinstance(entry, Mapping) else ()


def _registry_form_name(concept_registry: ConceptRegistry, concept_id: str) -> str | None:
    entry = concept_registry.get(concept_id)
    if not isinstance(entry, Mapping):
        return None
    form = entry.get("form")
    return form if isinstance(form, str) else None


def _concept_edges(
    concept_data: Mapping[str, Any], *, exactness_filter: frozenset[str] | None
) -> list[_ParameterizationEdge]:
    edges: list[_ParameterizationEdge] = []
    for relationship in concept_data.get("parameterization_relationships") or ():
        raw_exactness = payload_get(relationship, "exactness")
        exactness = raw_exactness if isinstance(raw_exactness, str) else ""
        if exactness_filter is not None and exactness not in exactness_filter:
            continue
        inputs = _string_sequence(payload_get(relationship, "inputs"))
        sympy_expr = payload_get(relationship, "sympy")
        if not inputs or not isinstance(sympy_expr, str):
            continue
        edges.append(
            _ParameterizationEdge(
                inputs=inputs,
                sympy=sympy_expr,
                conditions=_string_sequence(payload_get(relationship, "conditions")),
                exactness=exactness,
            )
        )
    return edges


def _parameterization_edges(
    concept_registry: ConceptRegistry, *, exactness_filter: frozenset[str] | None
) -> dict[str, list[_ParameterizationEdge]]:
    edges: dict[str, list[_ParameterizationEdge]] = {}
    for concept_id, concept_data in _iter_unique_concepts(concept_registry):
        concept_edges = _concept_edges(concept_data, exactness_filter=exactness_filter)
        if concept_edges:
            edges[concept_id] = concept_edges
    return edges


# --- Numeric derivation --------------------------------------------------------


def _normalize_claim_value(
    value: float,
    claim: ConflictClaim,
    concept_id: str,
    concept_registry: ConceptRegistry,
    forms: Mapping[str, FormDefinition] | None,
) -> float:
    if forms is None:
        return value
    unit = claim.unit
    if unit is None:
        return value
    form_name = _registry_form_name(concept_registry, concept_id)
    if form_name is None or form_name not in forms:
        return value
    form_def = forms[form_name]
    if unit == form_def.unit_symbol:
        return value
    return normalize_to_si(value, unit, form_def)


def _value_or_none(evaluation: NumericEvaluation) -> float | None:
    if evaluation.status is NumericEvaluationStatus.VALUE:
        return evaluation.value
    return None


def _evaluate_parameterization_with_registry(
    sympy_expr: str,
    input_values: dict[str, float],
    output_concept_id: str,
    concept_registry: ConceptRegistry,
) -> float | None:
    rewritten = sympy_expr
    for alias in _concept_aliases(concept_registry, output_concept_id):
        rewritten = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])",
            "__out__",
            rewritten,
        )

    safe_values: dict[str, float] = {}
    for index, (concept_id, value) in enumerate(input_values.items()):
        safe_symbol = f"__in_{index}__"
        safe_values[safe_symbol] = value
        for alias in _concept_aliases(concept_registry, concept_id):
            rewritten = re.sub(
                rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])",
                safe_symbol,
                rewritten,
            )

    if rewritten == sympy_expr:
        return _value_or_none(
            evaluate_numeric(sympy_expr, input_values, output_concept_id)
        )
    return _value_or_none(evaluate_numeric(rewritten, safe_values, "__out__"))


def _merge_contexts_for_derivation(
    context_sources: Sequence[tuple[str | None, tuple[str, ...]]],
    lifting_system: LiftingSystem | None,
) -> str | None | _Sentinel:
    concrete = [
        (context, claim_ids)
        for context, claim_ids in context_sources
        if context is not None
    ]
    if not concrete:
        return None
    contexts = [context for context, _claim_ids in concrete]
    if lifting_system is None:
        return contexts[0] if len(set(contexts)) == 1 else None

    from propstore.families.contexts import LiftingDecisionStatus

    candidates = [
        candidate
        for candidate in contexts
        if all(
            candidate == other
            or any(
                decision.status is LiftingDecisionStatus.LIFTED
                for claim_id in claim_ids
                for decision in lifting_system.lift_decisions_between(
                    other,
                    candidate,
                    claim_id,
                )
            )
            for other, claim_ids in concrete
        )
    ]
    if not candidates:
        return _INCOHERENT_CONTEXT
    return sorted(candidates)[0]


def _merge_conditions(*groups: Iterable[CelExpr]) -> tuple[CelExpr, ...]:
    merged = {
        str(condition)
        for group in groups
        for condition in group
        if str(condition)
    }
    return to_cel_exprs(sorted(merged))


def _direct_state_for_claim(
    concept_id: str,
    claim: ConflictClaim,
    concept_registry: ConceptRegistry,
    forms: Mapping[str, FormDefinition] | None,
) -> DerivedConflictValue | None:
    interval = extract_interval(claim)
    if interval is None:
        return None
    center, lo, hi = interval
    if abs(hi - lo) >= DEFAULT_TOLERANCE:
        return None
    normalized = _normalize_claim_value(center, claim, concept_id, concept_registry, forms)
    return DerivedConflictValue(
        concept_id=concept_id,
        value=normalized,
        source_claim_ids=(claim.claim_id,),
        conditions=to_cel_exprs(sorted(str(condition) for condition in claim.conditions)),
        context_id=claim_context(claim),
        derivation_chain=f"{concept_id}={normalized}(claim:{claim.claim_id})",
        hop_count=0,
    )


def _direct_states_for_concept(
    concept_id: str,
    claims: Sequence[ConflictClaim],
    concept_registry: ConceptRegistry,
    forms: Mapping[str, FormDefinition] | None,
) -> list[DerivedConflictValue]:
    states: list[DerivedConflictValue] = []
    seen: set[tuple[str, str, tuple[CelExpr, ...], str | None]] = set()
    for claim in claims:
        state = _direct_state_for_claim(concept_id, claim, concept_registry, forms)
        if state is None:
            continue
        key = (
            state.source_claim_ids[0],
            str(round(state.value, 12)),
            state.conditions,
            state.context_id,
        )
        if key in seen:
            continue
        seen.add(key)
        states.append(state)
    return states


def _quantity_inputs_only(
    inputs: Sequence[str], concept_registry: ConceptRegistry
) -> bool:
    for concept_id in inputs:
        form = _registry_form_name(concept_registry, concept_id)
        if form in (None, "", "category", "structural", "boolean"):
            return False
    return True


def _derive_state(
    concept_id: str,
    sympy_expr: str,
    input_states: Sequence[DerivedConflictValue],
    edge_conditions: Sequence[CelExpr],
    concept_registry: ConceptRegistry,
    lifting_system: LiftingSystem | None,
    *,
    warn_on_known_failure: bool,
) -> DerivedConflictValue | None:
    input_values = {state.concept_id: state.value for state in input_states}
    try:
        derived_value = _evaluate_parameterization_with_registry(
            sympy_expr,
            input_values,
            concept_id,
            concept_registry,
        )
        if derived_value is None:
            raise ValueError("parameterization evaluation returned no result")
    except _KNOWN_EVALUATION_ERRORS:
        if warn_on_known_failure:
            warnings.warn(
                f"Could not evaluate parameterization for {concept_id}: {sympy_expr}",
                stacklevel=2,
            )
        return None

    merged_context = _merge_contexts_for_derivation(
        [(state.context_id, state.source_claim_ids) for state in input_states],
        lifting_system,
    )
    if isinstance(merged_context, _Sentinel):
        return None

    source_claim_ids = tuple(
        sorted(
            {
                claim_id
                for state in input_states
                for claim_id in state.source_claim_ids
            }
        )
    )
    merged_conditions = _merge_conditions(
        *(state.conditions for state in input_states),
        edge_conditions,
    )
    chain_parts = " + ".join(state.derivation_chain for state in input_states)
    return DerivedConflictValue(
        concept_id=concept_id,
        value=derived_value,
        source_claim_ids=source_claim_ids,
        conditions=merged_conditions,
        context_id=merged_context,
        derivation_chain=f"{chain_parts} -> {sympy_expr} -> {concept_id}={derived_value}",
        hop_count=max(state.hop_count for state in input_states) + 1,
    )


# --- Comparison and record emission --------------------------------------------


def _representative_source_claim_id(source_ids: Sequence[str]) -> str:
    return source_ids[0]


def _record_key(
    concept_id: str,
    direct_claim_id: str,
    derived_state: DerivedConflictValue,
    warning_class: ConflictClass,
) -> _RecordKey:
    return (
        concept_id,
        direct_claim_id,
        derived_state.source_claim_ids,
        str(round(derived_state.value, 12)),
        derived_state.conditions,
        derived_state.context_id,
        warning_class.value,
    )


def _append_parameterization_record(
    records: list[ConflictRecord],
    seen_record_keys: set[_RecordKey],
    *,
    concept_id: str,
    direct_claim: ConflictClaim,
    derived_state: DerivedConflictValue,
    warning_class: ConflictClass,
) -> None:
    key = _record_key(concept_id, direct_claim.claim_id, derived_state, warning_class)
    if key in seen_record_keys:
        return
    seen_record_keys.add(key)
    records.append(
        ConflictRecord(
            concept_id=concept_id,
            claim_a_id=direct_claim.claim_id,
            claim_b_id=_representative_source_claim_id(derived_state.source_claim_ids),
            warning_class=warning_class,
            conditions_a=sorted(direct_claim.conditions),
            conditions_b=list(derived_state.conditions),
            value_a=value_str(direct_claim.value, claim=direct_claim),
            value_b=str(derived_state.value),
            derivation_chain=derived_state.derivation_chain,
        )
    )


def _compare_direct_claim_against_derived(
    records: list[ConflictRecord],
    seen_record_keys: set[_RecordKey],
    *,
    concept_id: str,
    direct_claim: ConflictClaim,
    derived_state: DerivedConflictValue,
    lifting_system: LiftingSystem | None,
    forms: Mapping[str, FormDefinition] | None,
    concept_registry: ConceptRegistry,
) -> None:
    concept_form = _registry_form_name(concept_registry, concept_id)
    if values_compatible(
        direct_claim.value,
        derived_state.value,
        claim_a=direct_claim,
        claim_b=derived_state,
        forms=forms,
        concept_form=concept_form,
    ):
        return

    context_class = classify_pair_context(
        claim_context(direct_claim),
        derived_state.context_id,
        lifting_system,
        claim_a_id=direct_claim.claim_id,
        claim_b_id=_representative_source_claim_id(derived_state.source_claim_ids),
    )
    _append_parameterization_record(
        records,
        seen_record_keys,
        concept_id=concept_id,
        direct_claim=direct_claim,
        derived_state=derived_state,
        warning_class=context_class
        if context_class is not None
        else ConflictClass.PARAM_CONFLICT,
    )


# --- Single-hop detector -------------------------------------------------------


def detect_parameterization_conflicts(
    by_concept: dict[str, list[ConflictClaim]],
    concept_registry: ConceptRegistry,
    claims: Sequence[ConflictClaim],
    *,
    lifting_system: LiftingSystem | None = None,
    forms: Mapping[str, FormDefinition] | None = None,
) -> list[ConflictRecord]:
    records: list[ConflictRecord] = []
    all_param_claims = by_concept or collect_parameter_claims(claims)
    seen_record_keys: set[_RecordKey] = set()
    edges = _parameterization_edges(concept_registry, exactness_filter=frozenset({"exact"}))

    for concept_id, _concept_data in _iter_unique_concepts(concept_registry):
        concept_edges = edges.get(concept_id)
        if not concept_edges:
            continue
        direct_claims = all_param_claims.get(concept_id, [])
        if not direct_claims:
            continue

        for edge in concept_edges:
            if not _quantity_inputs_only(edge.inputs, concept_registry):
                continue
            input_state_lists = [
                _direct_states_for_concept(
                    input_id,
                    all_param_claims.get(input_id, []),
                    concept_registry,
                    forms,
                )
                for input_id in edge.inputs
            ]
            if any(not states for states in input_state_lists):
                continue

            edge_conditions = to_cel_exprs(sorted(edge.conditions))
            for input_states in product(*input_state_lists):
                derived_state = _derive_state(
                    concept_id,
                    edge.sympy,
                    input_states,
                    edge_conditions,
                    concept_registry,
                    lifting_system,
                    warn_on_known_failure=True,
                )
                if derived_state is None:
                    continue
                for direct_claim in direct_claims:
                    _compare_direct_claim_against_derived(
                        records,
                        seen_record_keys,
                        concept_id=concept_id,
                        direct_claim=direct_claim,
                        derived_state=derived_state,
                        lifting_system=lifting_system,
                        forms=forms,
                        concept_registry=concept_registry,
                    )
    return records


# --- Transitive detector -------------------------------------------------------


def _state_key(state: DerivedConflictValue) -> _StateKey:
    return (
        state.concept_id,
        str(round(state.value, 12)),
        state.source_claim_ids,
        state.conditions,
        state.context_id,
        state.hop_count,
    )


def _detect_transitive_conflicts_for_claims(
    claims: Sequence[ConflictClaim],
    concept_registry: ConceptRegistry,
    by_concept: dict[str, list[ConflictClaim]],
    *,
    lifting_system: LiftingSystem | None = None,
    forms: Mapping[str, FormDefinition] | None = None,
) -> list[ConflictRecord]:
    records: list[ConflictRecord] = []
    seen_record_keys: set[_RecordKey] = set()

    param_edges = _parameterization_edges(
        concept_registry, exactness_filter=frozenset({"exact", "approximate"})
    )
    group_edges: dict[str, Iterable[str]] = {
        concept_id: [
            input_id for edge in concept_edges for input_id in edge.inputs
        ]
        for concept_id, concept_edges in param_edges.items()
    }
    for concept_id, _concept_data in _iter_unique_concepts(concept_registry):
        group_edges.setdefault(concept_id, ())
    groups = build_parameterization_groups(group_edges)

    for group in groups:
        if len(group) < 3:
            continue

        resolved: dict[str, list[DerivedConflictValue]] = {}
        seen_states: dict[str, set[_StateKey]] = {}
        for concept_id in group:
            states = _direct_states_for_concept(
                concept_id, by_concept.get(concept_id, []), concept_registry, forms
            )
            if states:
                resolved[concept_id] = list(states)
                seen_states[concept_id] = {_state_key(state) for state in states}

        changed = True
        max_iterations = len(group) * 4
        iteration = 0
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            for concept_id in sorted(group):
                for edge in param_edges.get(concept_id, []):
                    if not _quantity_inputs_only(edge.inputs, concept_registry):
                        continue
                    if any(input_id not in resolved for input_id in edge.inputs):
                        continue
                    edge_conditions = to_cel_exprs(sorted(edge.conditions))
                    ordered_input_states = [resolved[input_id] for input_id in edge.inputs]
                    for input_states in product(*ordered_input_states):
                        derived_state = _derive_state(
                            concept_id,
                            edge.sympy,
                            input_states,
                            edge_conditions,
                            concept_registry,
                            lifting_system,
                            warn_on_known_failure=False,
                        )
                        if derived_state is None:
                            continue
                        state_key = _state_key(derived_state)
                        concept_seen = seen_states.setdefault(concept_id, set())
                        if state_key in concept_seen:
                            continue
                        concept_seen.add(state_key)
                        resolved.setdefault(concept_id, []).append(derived_state)
                        changed = True

        for concept_id in group:
            direct_claims = by_concept.get(concept_id, [])
            derived_states = resolved.get(concept_id, [])
            if not direct_claims or not derived_states:
                continue
            for derived_state in derived_states:
                if derived_state.hop_count < 2:
                    continue
                for direct_claim in direct_claims:
                    _compare_direct_claim_against_derived(
                        records,
                        seen_record_keys,
                        concept_id=concept_id,
                        direct_claim=direct_claim,
                        derived_state=derived_state,
                        lifting_system=lifting_system,
                        forms=forms,
                        concept_registry=concept_registry,
                    )

    return records


def detect_transitive_conflicts(
    claims: Sequence[ConflictClaim],
    concept_registry: ConceptRegistry,
    *,
    lifting_system: LiftingSystem | None = None,
    forms: Mapping[str, FormDefinition] | None = None,
) -> list[ConflictRecord]:
    """Detect multi-hop parameterization-derivation conflicts.

    Within each parameterization connected component, direct claims are
    propagated forward through ``exact``/``approximate`` edges to a fixpoint; any
    transitively-derived value (``hop_count >= 2``) that disagrees with a direct
    claim for the same concept becomes a conflict record.
    """

    by_concept = collect_parameter_claims(claims)
    return _detect_transitive_conflicts_for_claims(
        claims,
        concept_registry,
        by_concept,
        lifting_system=lifting_system,
        forms=forms,
    )
