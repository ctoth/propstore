"""Parameterization-derived conflict detection."""

from __future__ import annotations

import enum
import re
import warnings
from dataclasses import dataclass
from itertools import product
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.value_comparison import (
    DEFAULT_TOLERANCE,
    extract_interval as _extract_interval,
    value_str as _value_str,
    values_compatible as _values_compatible,
)

from .collectors import _collect_parameter_claims
from .context import _classify_pair_context, _claim_context
from .models import ConflictClass, ConflictClaim, ConflictRecord

if TYPE_CHECKING:
    from propstore.form_utils import FormDefinition
    from propstore.context_lifting import LiftingSystem


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


class _Sentinel(enum.Enum):
    INCOHERENT_CONTEXT = "INCOHERENT_CONTEXT"


_INCOHERENT_CONTEXT = _Sentinel.INCOHERENT_CONTEXT
_SAFE_SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_KNOWN_EVALUATION_ERRORS = (
    TypeError,
    ValueError,
    ZeroDivisionError,
    AssertionError,
    ImportError,
)


def _normalize_claim_value(
    value: float,
    claim: ConflictClaim,
    concept_id: str,
    concept_registry: dict[str, dict],
    forms: dict[str, FormDefinition] | None,
) -> float:
    if forms is None:
        return value
    unit = claim.unit
    if unit is None:
        return value
    form_name = concept_registry.get(concept_id, {}).get("form")
    if form_name is None or form_name not in forms:
        return value
    from propstore.dimensions import normalize_to_si

    form_def = forms[form_name]
    if unit == form_def.unit_symbol:
        return value
    return normalize_to_si(value, unit, form_def)


def _representative_source_claim_id(source_ids: Sequence[str]) -> str:
    return source_ids[0]


def _iter_unique_concepts(concept_registry: dict[str, dict]) -> list[tuple[str, dict]]:
    unique: list[tuple[str, dict]] = []
    seen_ids: set[str] = set()
    for concept_data in concept_registry.values():
        if not isinstance(concept_data, dict):
            continue
        concept_id = concept_data.get("artifact_id") or concept_data.get("id")
        if not isinstance(concept_id, str) or not concept_id or concept_id in seen_ids:
            continue
        seen_ids.add(concept_id)
        unique.append((concept_id, concept_data))
    return unique


def _concept_symbol_candidates(concept_data: dict) -> tuple[str, ...]:
    candidates: list[str] = []
    seen: set[str] = set()

    def add(candidate: object) -> None:
        if not isinstance(candidate, str) or not candidate:
            return
        if not _SAFE_SYMBOL_RE.match(candidate):
            return
        if candidate in seen:
            return
        seen.add(candidate)
        candidates.append(candidate)

    add(concept_data.get("canonical_name"))
    for logical_id in concept_data.get("logical_ids", []) or []:
        if not isinstance(logical_id, dict):
            continue
        add(logical_id.get("value"))
    return tuple(candidates)


def _evaluate_parameterization_with_registry(
    sympy_expr: str,
    input_values: dict[str, float],
    output_concept_id: str,
    concept_registry: dict[str, dict],
) -> float | None:
    from propstore.propagation import evaluate_parameterization

    output_data = concept_registry.get(output_concept_id, {})
    input_aliases = {
        concept_id: _concept_symbol_candidates(concept_registry.get(concept_id, {}))
        for concept_id in input_values
    }
    output_aliases = _concept_symbol_candidates(output_data)

    rewritten = sympy_expr
    for alias in output_aliases:
        rewritten = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])",
            "__out__",
            rewritten,
        )

    safe_values: dict[str, float] = {}
    for index, (concept_id, value) in enumerate(input_values.items()):
        safe_symbol = f"__in_{index}__"
        safe_values[safe_symbol] = value
        for alias in input_aliases.get(concept_id, ()):
            rewritten = re.sub(
                rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])",
                safe_symbol,
                rewritten,
            )

    if rewritten == sympy_expr:
        return evaluate_parameterization(sympy_expr, input_values, output_concept_id)
    return evaluate_parameterization(rewritten, safe_values, "__out__")


def _merge_contexts_for_derivation(
    contexts: Sequence[str | None],
    lifting_system: LiftingSystem | None,
) -> str | None | _Sentinel:
    concrete = [context for context in contexts if context]
    if not concrete:
        return None
    if lifting_system is None:
        return concrete[0] if len(set(concrete)) == 1 else None

    candidates = [
        candidate
        for candidate in concrete
        if all(
            candidate == other or lifting_system.can_lift(other, candidate)
            for other in concrete
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
        if isinstance(condition, str) and condition
    }
    return to_cel_exprs(sorted(merged))


def _direct_state_for_claim(
    concept_id: str,
    claim: ConflictClaim,
    concept_registry: dict[str, dict],
    forms: dict[str, FormDefinition] | None,
) -> DerivedConflictValue | None:
    interval = _extract_interval(claim)
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
        conditions=to_cel_exprs(sorted(claim.conditions)),
        context_id=_claim_context(claim),
        derivation_chain=f"{concept_id}={normalized}(claim:{claim.claim_id})",
        hop_count=0,
    )


def _direct_states_for_concept(
    concept_id: str,
    claims: Sequence[ConflictClaim],
    concept_registry: dict[str, dict],
    forms: dict[str, FormDefinition] | None,
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


def _quantity_inputs_only(inputs: Sequence[str], concept_registry: dict[str, dict]) -> bool:
    for concept_id in inputs:
        inp_form = concept_registry.get(concept_id, {}).get("form", "")
        if inp_form in ("category", "structural", "boolean", ""):
            return False
    return True


def _derive_state(
    concept_id: str,
    sympy_expr: str,
    input_states: Sequence[DerivedConflictValue],
    edge_conditions: Sequence[CelExpr],
    concept_registry: dict[str, dict],
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
        [state.context_id for state in input_states],
        lifting_system,
    )
    if merged_context is _INCOHERENT_CONTEXT:
        return None
    assert not isinstance(merged_context, _Sentinel)

    source_claim_ids = tuple(sorted({
        claim_id
        for state in input_states
        for claim_id in state.source_claim_ids
    }))
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


def _record_key(
    concept_id: str,
    direct_claim_id: str,
    derived_state: DerivedConflictValue,
    warning_class: ConflictClass,
) -> tuple[str, str, tuple[str, ...], str, tuple[str, ...], str | None, str]:
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
    seen_record_keys: set[tuple[str, str, tuple[str, ...], str, tuple[str, ...], str | None, str]],
    *,
    concept_id: str,
    direct_claim: ConflictClaim,
    derived_state: DerivedConflictValue,
    warning_class: ConflictClass,
) -> None:
    key = _record_key(
        concept_id,
        direct_claim.claim_id,
        derived_state,
        warning_class,
    )
    if key in seen_record_keys:
        return
    seen_record_keys.add(key)
    records.append(ConflictRecord(
        concept_id=concept_id,
        claim_a_id=direct_claim.claim_id,
        claim_b_id=_representative_source_claim_id(derived_state.source_claim_ids),
        warning_class=warning_class,
        conditions_a=sorted(direct_claim.conditions),
        conditions_b=list(derived_state.conditions),
        value_a=_value_str(direct_claim.value, claim=direct_claim),
        value_b=str(derived_state.value),
        derivation_chain=derived_state.derivation_chain,
    ))


def _compare_direct_claim_against_derived(
    records: list[ConflictRecord],
    seen_record_keys: set[tuple[str, str, tuple[str, ...], str, tuple[str, ...], str | None, str]],
    *,
    concept_id: str,
    direct_claim: ConflictClaim,
    derived_state: DerivedConflictValue,
    lifting_system: LiftingSystem | None,
    forms: dict[str, FormDefinition] | None,
    concept_registry: dict[str, dict],
) -> None:
    concept_form = concept_registry.get(concept_id, {}).get("form")
    if _values_compatible(
        direct_claim.value,
        derived_state.value,
        claim_a=direct_claim,
        claim_b=derived_state,
        forms=forms,
        concept_form=concept_form if isinstance(concept_form, str) else None,
    ):
        return

    context_class = _classify_pair_context(
        _claim_context(direct_claim),
        derived_state.context_id,
        lifting_system,
    )
    if context_class is not None:
        _append_parameterization_record(
            records,
            seen_record_keys,
            concept_id=concept_id,
            direct_claim=direct_claim,
            derived_state=derived_state,
            warning_class=context_class,
        )
        return

    _append_parameterization_record(
        records,
        seen_record_keys,
        concept_id=concept_id,
        direct_claim=direct_claim,
        derived_state=derived_state,
        warning_class=ConflictClass.PARAM_CONFLICT,
    )


def _detect_parameterization_conflicts(
    records: list[ConflictRecord],
    by_concept: dict[str, list[ConflictClaim]],
    concept_registry: dict[str, dict],
    claims: Sequence[ConflictClaim],
    *,
    lifting_system: LiftingSystem | None = None,
    forms: dict[str, FormDefinition] | None = None,
) -> None:
    all_param_claims = by_concept or _collect_parameter_claims(claims)
    seen_record_keys: set[tuple[str, str, tuple[str, ...], str, tuple[str, ...], str | None, str]] = set()

    for concept_id, concept_data in _iter_unique_concepts(concept_registry):
        param_rels = concept_data.get("parameterization_relationships", [])
        if not param_rels:
            continue

        direct_claims = all_param_claims.get(concept_id, [])
        if not direct_claims:
            continue

        for rel in param_rels:
            if rel.get("exactness") != "exact":
                continue

            inputs = rel.get("inputs", [])
            sympy_expr = rel.get("sympy")
            if not inputs or not isinstance(sympy_expr, str):
                continue
            if not _quantity_inputs_only(inputs, concept_registry):
                continue

            input_state_lists = [
                _direct_states_for_concept(
                    input_id,
                    all_param_claims.get(input_id, []),
                    concept_registry,
                    forms,
                )
                for input_id in inputs
            ]
            if any(not states for states in input_state_lists):
                continue

            edge_conditions = to_cel_exprs(sorted(str(condition) for condition in rel.get("conditions", []) or []))
            for input_states in product(*input_state_lists):
                derived_state = _derive_state(
                    concept_id,
                    sympy_expr,
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


def _state_key(state: DerivedConflictValue) -> tuple[str, str, tuple[str, ...], tuple[str, ...], str | None, int]:
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
    concept_registry: dict[str, dict],
    by_concept: dict[str, list[ConflictClaim]],
    *,
    lifting_system: LiftingSystem | None = None,
    forms: dict[str, FormDefinition] | None = None,
) -> list[ConflictRecord]:
    from propstore.parameterization_groups import build_groups
    from propstore.parameterization_walk import parameterization_edges_from_registry

    records: list[ConflictRecord] = []
    seen_record_keys: set[tuple[str, str, tuple[str, ...], str, tuple[str, ...], str | None, str]] = set()
    unique_registry = {
        concept_id: concept_data
        for concept_id, concept_data in _iter_unique_concepts(concept_registry)
    }

    concept_list: list[dict] = []
    for concept_id, concept_data in unique_registry.items():
        entry = dict(concept_data)
        entry.setdefault("id", concept_id)
        concept_list.append(entry)

    groups = build_groups(concept_list)
    param_edges = parameterization_edges_from_registry(
        unique_registry,
        exactness_filter={"exact", "approximate"},
    )

    for group in groups:
        if len(group) < 3:
            continue

        direct_states_by_concept = {
            concept_id: _direct_states_for_concept(
                concept_id,
                by_concept.get(concept_id, []),
                unique_registry,
                forms,
            )
            for concept_id in group
        }
        resolved = {
            concept_id: list(states)
            for concept_id, states in direct_states_by_concept.items()
            if states
        }
        seen_states = {
            concept_id: {_state_key(state) for state in states}
            for concept_id, states in resolved.items()
        }

        changed = True
        max_iterations = len(group) * 4
        iteration = 0
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            for concept_id in sorted(group):
                for edge in param_edges.get(concept_id, []):
                    inputs = edge["inputs"]
                    sympy_expr = edge["sympy"]
                    if not _quantity_inputs_only(inputs, unique_registry):
                        continue
                    if any(input_id not in resolved for input_id in inputs):
                        continue

                    edge_conditions = to_cel_exprs(sorted(str(condition) for condition in edge.get("conditions", []) or []))
                    ordered_input_states = [resolved[input_id] for input_id in inputs]
                    for input_states in product(*ordered_input_states):
                        derived_state = _derive_state(
                            concept_id,
                            sympy_expr,
                            input_states,
                            edge_conditions,
                            unique_registry,
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
                        concept_registry=unique_registry,
                    )

    return records


def detect_transitive_conflicts(
    claims: Sequence[ConflictClaim],
    concept_registry: dict[str, dict],
    *,
    lifting_system: LiftingSystem | None = None,
    forms: dict[str, FormDefinition] | None = None,
) -> list[ConflictRecord]:
    by_concept = _collect_parameter_claims(claims)
    return _detect_transitive_conflicts_for_claims(
        claims,
        concept_registry,
        by_concept,
        lifting_system=lifting_system,
        forms=forms,
    )
