"""Shared value and derivation resolution for belief-space views."""

from __future__ import annotations

import json
from typing import Any, Callable

from ast_equiv import compare as ast_compare

from propstore.world.types import DerivedResult, ValueResult


class ActiveClaimResolver:
    """Resolve values and derived values for a belief-space view."""

    def __init__(
        self,
        *,
        parameterizations_for: Callable[[str], list[dict]],
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
    ) -> DerivedResult:
        from propstore.propagation import evaluate_parameterization

        params = self._parameterizations_for(concept_id)
        if not params:
            return DerivedResult(concept_id=concept_id, status="no_relationship")

        for param in params:
            if not self._is_param_compatible(param.get("conditions_cel")):
                continue

            sympy_expr = param.get("sympy")
            if not sympy_expr:
                continue

            input_ids = json.loads(param["concept_ids"])
            effective_inputs = [iid for iid in input_ids if iid != concept_id]

            input_values: dict[str, float] = {}
            all_determined = True
            any_conflicted = False

            for input_id in effective_inputs:
                if override_values and input_id in override_values:
                    override_value = override_values[input_id]
                    if override_value is not None:
                        try:
                            input_values[input_id] = float(override_value)
                            continue
                        except (TypeError, ValueError):
                            pass

                value_result = self._value_of(input_id)
                if value_result.status == "determined":
                    value = value_result.claims[0].get("value") if value_result.claims else None
                    if value is not None:
                        input_values[input_id] = float(value)
                    else:
                        all_determined = False
                elif value_result.status == "conflicted":
                    any_conflicted = True
                    all_determined = False
                else:
                    all_determined = False

            if any_conflicted:
                return DerivedResult(concept_id=concept_id, status="conflicted")

            if not all_determined or len(input_values) != len(effective_inputs):
                continue

            result = evaluate_parameterization(sympy_expr, input_values, concept_id)
            if result is not None:
                return DerivedResult(
                    concept_id=concept_id,
                    status="derived",
                    value=result,
                    formula=param.get("formula"),
                    input_values=input_values,
                    exactness=param.get("exactness"),
                )

        if any(not self._is_param_compatible(param.get("conditions_cel")) for param in params):
            return DerivedResult(concept_id=concept_id, status="no_relationship")

        return DerivedResult(concept_id=concept_id, status="underspecified")

    def value_of_from_active(self, active: list[dict], concept_id: str) -> ValueResult:
        if not active:
            return ValueResult(concept_id=concept_id, status="no_claims")

        algo_claims = [claim for claim in active if claim.get("type") == "algorithm"]
        value_claims = [claim for claim in active if claim.get("type") != "algorithm"]

        if value_claims and algo_claims:
            values = {claim.get("value") for claim in value_claims if claim.get("value") is not None}
            if not values:
                return ValueResult(concept_id=concept_id, status="no_claims", claims=active)
            if len(values) == 1:
                return ValueResult(concept_id=concept_id, status="determined", claims=active)
            return ValueResult(concept_id=concept_id, status="conflicted", claims=active)

        if algo_claims and not value_claims:
            if len(algo_claims) == 1:
                return ValueResult(concept_id=concept_id, status="determined", claims=algo_claims)

            all_var_concepts: set[str] = set()
            for claim in algo_claims:
                all_var_concepts.update(self._extract_variable_concepts(claim))
            all_var_concepts.discard(concept_id)

            known_values = self._collect_known_values(list(all_var_concepts))
            if self._all_algorithms_equivalent(algo_claims, known_values):
                return ValueResult(concept_id=concept_id, status="determined", claims=algo_claims)
            return ValueResult(concept_id=concept_id, status="conflicted", claims=algo_claims)

        values = {claim.get("value") for claim in active if claim.get("value") is not None}
        if not values:
            return ValueResult(concept_id=concept_id, status="no_claims", claims=active)
        if len(values) == 1:
            return ValueResult(concept_id=concept_id, status="determined", claims=active)
        return ValueResult(concept_id=concept_id, status="conflicted", claims=active)

    def _all_algorithms_equivalent(
        self,
        algo_claims: list[dict],
        known_values: dict[str, Any],
    ) -> bool:
        for i in range(len(algo_claims)):
            for j in range(i + 1, len(algo_claims)):
                body_a = algo_claims[i].get("body", "")
                body_b = algo_claims[j].get("body", "")
                if not body_a or not body_b:
                    return False
                bindings_a = self._extract_bindings(algo_claims[i])
                bindings_b = self._extract_bindings(algo_claims[j])
                try:
                    result = ast_compare(
                        body_a,
                        bindings_a,
                        body_b,
                        bindings_b,
                        known_values=known_values if known_values else None,
                    )
                except Exception:
                    return False
                if not result.equivalent:
                    return False
        return True
