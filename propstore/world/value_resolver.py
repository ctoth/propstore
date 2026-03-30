"""Shared value and derivation resolution for belief-space views."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable

from ast_equiv import compare as ast_compare

from propstore.core.id_types import ConceptId, to_concept_id
from propstore.core.row_types import ParameterizationRow
from propstore.world.types import DerivedResult, ValueResult, ValueStatus


@dataclass(frozen=True)
class _ActiveClaimView:
    raw: dict[str, object]
    claim_id: str | None
    claim_type: str | None
    value: float | str | None
    body: str | None


def _claim_string(claim: dict[str, object], key: str) -> str | None:
    value = claim.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _claim_value(claim: dict[str, object]) -> float | str | None:
    value = claim.get("value")
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        return value
    return None


def _active_claim_view(claim: dict[str, object]) -> _ActiveClaimView:
    return _ActiveClaimView(
        raw=claim,
        claim_id=_claim_string(claim, "id"),
        claim_type=_claim_string(claim, "type"),
        value=_claim_value(claim),
        body=_claim_string(claim, "body"),
    )


def _parameterization_concept_ids(param: ParameterizationRow) -> tuple[ConceptId, ...]:
    try:
        decoded = json.loads(param.concept_ids)
    except json.JSONDecodeError:
        return ()
    if not isinstance(decoded, list):
        return ()
    return tuple(to_concept_id(item) for item in decoded if isinstance(item, str))


def collect_known_values(
    variable_concepts: list[str],
    value_of: Callable[[str], ValueResult],
) -> dict[str, Any]:
    """Resolve numeric values for a list of concept IDs.

    Shared implementation used by BoundWorld and HypotheticalWorld.
    """
    known: dict[str, Any] = {}
    for cid in variable_concepts:
        vr = value_of(cid)
        if vr.status == "determined" and vr.claims:
            val = _claim_value(vr.claims[0])
            if val is not None:
                try:
                    known[cid] = float(val)
                except (TypeError, ValueError):
                    pass
    return known


class ActiveClaimResolver:
    """Resolve values and derived values for a belief-space view."""

    def __init__(
        self,
        *,
        parameterizations_for: Callable[[str], list[ParameterizationRow]],
        is_param_compatible: Callable[[str | None], bool],
        value_of: Callable[[str], ValueResult],
        extract_variable_concepts: Callable[[dict], list[str]],
        collect_known_values: Callable[[list[str]], dict[str, Any]],
        extract_bindings: Callable[[dict], dict[str, str]],
    ) -> None:
        self._parameterizations_for = parameterizations_for
        self._is_param_compatible = is_param_compatible
        self._value_of = value_of
        self._extract_variable_concepts = extract_variable_concepts
        self._collect_known_values = collect_known_values
        self._extract_bindings = extract_bindings

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: dict[str, float | str | None] | None = None,
        _derivation_stack: set[str] | None = None,
    ) -> DerivedResult:
        from propstore.propagation import evaluate_parameterization

        typed_concept_id = to_concept_id(concept_id)
        if _derivation_stack is None:
            _derivation_stack = set()

        params = self._parameterizations_for(concept_id)
        if not params:
            return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.NO_RELATIONSHIP)

        saw_compatible_candidate = False
        saw_conflicted_candidate = False
        saw_underspecified_candidate = False

        for param in params:
            if not self._is_param_compatible(param.conditions_cel):
                continue
            saw_compatible_candidate = True

            candidate = self._derive_from_parameterization(
                concept_id,
                param,
                override_values=override_values,
                derivation_stack=_derivation_stack,
            )
            if candidate.status == "derived":
                return candidate
            if candidate.status == "conflicted":
                saw_conflicted_candidate = True
            elif candidate.status == "underspecified":
                saw_underspecified_candidate = True

        if not saw_compatible_candidate:
            return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.NO_RELATIONSHIP)

        if saw_conflicted_candidate:
            return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.CONFLICTED)
        if saw_underspecified_candidate:
            return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.UNDERSPECIFIED)
        return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.UNDERSPECIFIED)

    def value_of_from_active(self, active: list[dict], concept_id: str) -> ValueResult:
        typed_concept_id = to_concept_id(concept_id)
        if not active:
            return ValueResult(concept_id=typed_concept_id, status=ValueStatus.NO_CLAIMS)

        active_views = tuple(_active_claim_view(claim) for claim in active)
        algo_claims = [claim for claim in active_views if claim.claim_type == "algorithm"]
        value_claims = [claim for claim in active_views if claim.claim_type != "algorithm"]

        if value_claims and algo_claims:
            direct_values = {
                self._normalize_value(claim.value)
                for claim in value_claims
                if claim.value is not None
            }
            if not direct_values:
                status = ValueStatus.NO_CLAIMS if not active else ValueStatus.NO_VALUES
                return ValueResult(concept_id=typed_concept_id, status=status, claims=active)
            if len(direct_values) != 1:
                return ValueResult(concept_id=typed_concept_id, status=ValueStatus.CONFLICTED, claims=active)

            direct_value = next(iter(direct_values))
            unevaluable_algorithm_present = False
            for claim in algo_claims:
                matches_direct = self._algorithm_matches_direct_value(
                    claim,
                    direct_value,
                )
                if matches_direct is None:
                    unevaluable_algorithm_present = True
                    continue
                if not matches_direct:
                    return ValueResult(concept_id=typed_concept_id, status=ValueStatus.CONFLICTED, claims=active)
            if unevaluable_algorithm_present:
                return ValueResult(concept_id=typed_concept_id, status=ValueStatus.CONFLICTED, claims=active)
            return ValueResult(concept_id=typed_concept_id, status=ValueStatus.DETERMINED, claims=active)

        if algo_claims and not value_claims:
            if len(algo_claims) == 1:
                return ValueResult(
                    concept_id=typed_concept_id,
                    status=ValueStatus.DETERMINED,
                    claims=[claim.raw for claim in algo_claims],
                )

            all_var_concepts: set[str] = set()
            for claim in algo_claims:
                all_var_concepts.update(self._extract_variable_concepts(claim.raw))
            all_var_concepts.discard(concept_id)

            known_values = self._collect_known_values(list(all_var_concepts))
            if self._all_algorithms_equivalent(algo_claims, known_values):
                return ValueResult(
                    concept_id=typed_concept_id,
                    status=ValueStatus.DETERMINED,
                    claims=[claim.raw for claim in algo_claims],
                )
            return ValueResult(
                concept_id=typed_concept_id,
                status=ValueStatus.CONFLICTED,
                claims=[claim.raw for claim in algo_claims],
            )

        values = {claim.value for claim in active_views if claim.value is not None}
        if not values:
            status = ValueStatus.NO_CLAIMS if not active else ValueStatus.NO_VALUES
            return ValueResult(concept_id=typed_concept_id, status=status, claims=active)
        if len(values) == 1:
            return ValueResult(concept_id=typed_concept_id, status=ValueStatus.DETERMINED, claims=active)
        return ValueResult(concept_id=typed_concept_id, status=ValueStatus.CONFLICTED, claims=active)

    def _derive_from_parameterization(
        self,
        concept_id: str,
        param: ParameterizationRow,
        *,
        override_values: dict[str, float | str | None] | None,
        derivation_stack: set[str],
    ) -> DerivedResult:
        from propstore.propagation import evaluate_parameterization

        typed_concept_id = to_concept_id(concept_id)
        sympy_expr = param.sympy
        if not sympy_expr:
            return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.UNDERSPECIFIED)

        effective_inputs = [iid for iid in _parameterization_concept_ids(param) if iid != concept_id]

        input_values: dict[str, float] = {}
        for input_id in effective_inputs:
            override_value = self._coerce_override_value(override_values, input_id)
            if override_value is not None:
                input_values[input_id] = override_value
                continue

            value_result = self._value_of(input_id)
            if value_result.status == "determined":
                value = _claim_value(value_result.claims[0]) if value_result.claims else None
                if value is None:
                    return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.UNDERSPECIFIED)
                input_values[input_id] = float(value)
                continue

            if value_result.status == "conflicted":
                return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.CONFLICTED)

            if input_id in derivation_stack:
                return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.UNDERSPECIFIED)

            derivation_stack.add(input_id)
            try:
                derived = self.derived_value(
                    input_id,
                    override_values=override_values,
                    _derivation_stack=derivation_stack,
                )
            finally:
                derivation_stack.discard(input_id)

            if derived.status == "derived" and derived.value is not None:
                input_values[input_id] = float(derived.value)
                continue
            if derived.status == "conflicted":
                return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.CONFLICTED)
            return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.UNDERSPECIFIED)

        result = evaluate_parameterization(sympy_expr, input_values, concept_id)
        if result is None:
            return DerivedResult(concept_id=typed_concept_id, status=ValueStatus.UNDERSPECIFIED)

        return DerivedResult(
            concept_id=typed_concept_id,
            status=ValueStatus.DERIVED,
            value=result,
            formula=param.formula,
            input_values=input_values,
            exactness=param.exactness,
        )

    @staticmethod
    def _coerce_override_value(
        override_values: dict[str, float | str | None] | None,
        input_id: str,
    ) -> float | None:
        if not override_values or input_id not in override_values:
            return None
        override_value = override_values[input_id]
        if override_value is None:
            return None
        try:
            return float(override_value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_value(value: float | str | None) -> float | str | None:
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value)
        return value

    def _algorithm_matches_direct_value(
        self,
        claim: _ActiveClaimView,
        direct_value: float | str | None,
    ) -> bool | None:
        body = claim.body
        if not body:
            return None

        bindings = self._extract_bindings(claim.raw)
        if not bindings:
            return None

        constant_body = _constant_algorithm_body(direct_value)
        if constant_body is None:
            return None

        concept_ids = list(dict.fromkeys(bindings.values()))
        known_values = self._collect_known_values(concept_ids)
        if any(concept_id not in known_values for concept_id in concept_ids):
            return None

        try:
            result = ast_compare(
                body,
                bindings,
                constant_body,
                {},
                known_values=known_values,
            )
        except (ValueError, SyntaxError) as exc:
            logging.warning(
                "ast_compare failed for algorithm-vs-direct comparison %s: %s",
                claim.claim_id,
                exc,
            )
            return None

        return result.equivalent

    def _all_algorithms_equivalent(
        self,
        algo_claims: list[_ActiveClaimView],
        known_values: dict[str, Any],
    ) -> bool:
        for i in range(len(algo_claims)):
            for j in range(i + 1, len(algo_claims)):
                body_a = algo_claims[i].body or ""
                body_b = algo_claims[j].body or ""
                if not body_a or not body_b:
                    return False
                bindings_a = self._extract_bindings(algo_claims[i].raw)
                bindings_b = self._extract_bindings(algo_claims[j].raw)
                try:
                    result = ast_compare(
                        body_a,
                        bindings_a,
                        body_b,
                        bindings_b,
                        known_values=known_values if known_values else None,
                    )
                except (ValueError, SyntaxError) as exc:
                    logging.warning("ast_compare failed in algorithm equivalence check: %s", exc)
                    return False
                if not result.equivalent:
                    return False
        return True


def _constant_algorithm_body(value: float | str | None) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return f"def compute():\n    return {float(value)!r}\n"
