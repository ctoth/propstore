"""Shared value and derivation resolution for belief-space views."""

from __future__ import annotations

import ast
import json
import logging
from typing import Any, Callable

from ast_equiv import compare as ast_compare, parse_algorithm

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
        _derivation_stack: set[str] | None = None,
    ) -> DerivedResult:
        from propstore.propagation import evaluate_parameterization

        if _derivation_stack is None:
            _derivation_stack = set()

        params = self._parameterizations_for(concept_id)
        if not params:
            return DerivedResult(concept_id=concept_id, status="no_relationship")

        saw_compatible_candidate = False
        saw_conflicted_candidate = False
        saw_underspecified_candidate = False

        for param in params:
            if not self._is_param_compatible(param.get("conditions_cel")):
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
            return DerivedResult(concept_id=concept_id, status="no_relationship")

        if saw_conflicted_candidate:
            return DerivedResult(concept_id=concept_id, status="conflicted")
        if saw_underspecified_candidate:
            return DerivedResult(concept_id=concept_id, status="underspecified")
        return DerivedResult(concept_id=concept_id, status="underspecified")

    def value_of_from_active(self, active: list[dict], concept_id: str) -> ValueResult:
        if not active:
            return ValueResult(concept_id=concept_id, status="no_claims")

        algo_claims = [claim for claim in active if claim.get("type") == "algorithm"]
        value_claims = [claim for claim in active if claim.get("type") != "algorithm"]

        if value_claims and algo_claims:
            direct_values = {
                self._normalize_value(claim.get("value"))
                for claim in value_claims
                if claim.get("value") is not None
            }
            if not direct_values:
                return ValueResult(concept_id=concept_id, status="no_claims", claims=active)
            if len(direct_values) != 1:
                return ValueResult(concept_id=concept_id, status="conflicted", claims=active)

            direct_value = next(iter(direct_values))
            algorithm_values: set[float | str] = set()
            unevaluable_algorithm_present = False
            for claim in algo_claims:
                evaluated = self._evaluate_algorithm_claim_value(claim)
                if evaluated is None:
                    unevaluable_algorithm_present = True
                    continue
                algorithm_values.add(self._normalize_value(evaluated))

            if any(value != direct_value for value in algorithm_values):
                return ValueResult(concept_id=concept_id, status="conflicted", claims=active)
            if len(algorithm_values) > 1:
                return ValueResult(concept_id=concept_id, status="conflicted", claims=active)
            if unevaluable_algorithm_present:
                return ValueResult(concept_id=concept_id, status="conflicted", claims=active)
            return ValueResult(concept_id=concept_id, status="determined", claims=active)

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

    def _derive_from_parameterization(
        self,
        concept_id: str,
        param: dict,
        *,
        override_values: dict[str, float | str | None] | None,
        derivation_stack: set[str],
    ) -> DerivedResult:
        from propstore.propagation import evaluate_parameterization

        sympy_expr = param.get("sympy")
        if not sympy_expr:
            return DerivedResult(concept_id=concept_id, status="underspecified")

        input_ids = json.loads(param["concept_ids"])
        effective_inputs = [iid for iid in input_ids if iid != concept_id]

        input_values: dict[str, float] = {}
        for input_id in effective_inputs:
            override_value = self._coerce_override_value(override_values, input_id)
            if override_value is not None:
                input_values[input_id] = override_value
                continue

            value_result = self._value_of(input_id)
            if value_result.status == "determined":
                value = value_result.claims[0].get("value") if value_result.claims else None
                if value is None:
                    return DerivedResult(concept_id=concept_id, status="underspecified")
                input_values[input_id] = float(value)
                continue

            if value_result.status == "conflicted":
                return DerivedResult(concept_id=concept_id, status="conflicted")

            if input_id in derivation_stack:
                return DerivedResult(concept_id=concept_id, status="underspecified")

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
                return DerivedResult(concept_id=concept_id, status="conflicted")
            return DerivedResult(concept_id=concept_id, status="underspecified")

        result = evaluate_parameterization(sympy_expr, input_values, concept_id)
        if result is None:
            return DerivedResult(concept_id=concept_id, status="underspecified")

        return DerivedResult(
            concept_id=concept_id,
            status="derived",
            value=result,
            formula=param.get("formula"),
            input_values=input_values,
            exactness=param.get("exactness"),
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

    def _evaluate_algorithm_claim_value(self, claim: dict) -> float | None:
        body = claim.get("body")
        if not body:
            return None

        bindings = self._extract_bindings(claim)
        if not bindings:
            return None

        known_values = self._collect_known_values(list(dict.fromkeys(bindings.values())))
        local_env: dict[str, Any] = {}
        for name, concept_id in bindings.items():
            if concept_id not in known_values:
                return None
            local_env[name] = known_values[concept_id]

        try:
            tree = parse_algorithm(body)
        except ValueError:
            return None

        function_node = next(
            (
                node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ),
            None,
        )
        if function_node is None or len(function_node.body) != 1:
            return None

        statement = function_node.body[0]
        if not isinstance(statement, ast.Return) or statement.value is None:
            return None
        if not _is_safe_algorithm_expression(statement.value):
            return None

        expression = ast.fix_missing_locations(ast.Expression(body=statement.value))
        try:
            result = eval(compile(expression, "<algorithm-claim>", "eval"), {"__builtins__": {}}, local_env)
        except Exception as exc:
            logging.warning("algorithm evaluation failed for %s: %s", claim.get("id"), exc)
            return None

        try:
            return float(result)
        except (TypeError, ValueError):
            return None

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
                except (ValueError, SyntaxError) as exc:
                    logging.warning("ast_compare failed in algorithm equivalence check: %s", exc)
                    return False
                if not result.equivalent:
                    return False
        return True


_SAFE_ALGORITHM_EXPR_NODES = (
    ast.BinOp,
    ast.Constant,
    ast.Div,
    ast.Expression,
    ast.FloorDiv,
    ast.Load,
    ast.Mod,
    ast.Mult,
    ast.Name,
    ast.Pow,
    ast.Return,
    ast.Sub,
    ast.UnaryOp,
    ast.UAdd,
    ast.USub,
    ast.Add,
)


def _is_safe_algorithm_expression(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, _SAFE_ALGORITHM_EXPR_NODES):
            return False
    return True
