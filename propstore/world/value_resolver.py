"""Shared value and derivation resolution for belief-space views.

:class:`ActiveClaimResolver` is the pure value/derived-value compute kernel the
bound world (and overlay world) delegate to. It computes a concept's value from
a set of active claims — direct value claims versus algorithm- and
parameterization-derived values — and classifies the outcome as
``DETERMINED``/``CONFLICTED``/``DERIVED``/``UNDERSPECIFIED`` etc. on
:class:`~propstore.world.types.ValueResult` / ``DerivedResult``.

The kernel is deliberately pure: it never touches the ATMS engine, resolution
strategies, or the bound world. Everything it needs from the surrounding world
(which parameterizations bind a concept, whether one is compatible, how to read
another concept's value, how to read an algorithm claim's variable bindings) is
supplied as a callable at construction. Parameterization evaluation goes through
:func:`propstore.propagation.evaluate_parameterization` (which lowers to the
``human_to_sympy`` substrate — no raw sympy here); algorithm comparison goes
through ``ast_equiv.compare``. Claims are read as the canonical
:class:`~propstore.core.active_claims.ActiveClaim` and
parameterizations as the canonical
:class:`~propstore.core.graph_types.ParameterizationEdge` (CLAUDE.md substrate
discipline: one spelling per thing, no mirror types, no row DTOs).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

import ast_equiv
from ast_equiv import AlgorithmParseError, ComparisonResult

from propstore.core.active_claims import ActiveClaim
from propstore.core.graph_types import ParameterizationEdge
from propstore.core.id_types import ConceptId, to_concept_id
from propstore.core.scalars import ScalarValue
from propstore.families.claims import ClaimType
from propstore.propagation import (
    ParameterizationEvaluation,
    ParameterizationEvaluationStatus,
    evaluate_parameterization,
    rewrite_parameterization_symbols,
)
from propstore.world.types import (
    DerivedResult,
    ValueResult,
    ValueResultReason,
    ValueStatus,
)


class _AstCompare(Protocol):
    """Fully-typed surface for ``ast_equiv.compare``.

    ``ast_equiv`` annotates the two ``bindings`` arguments as a bare ``dict``,
    leaving the imported function partially unknown. We own the call site, not
    the pinned package git rev, so the canonical function is narrowed here to a
    fully-typed Protocol (the dispatch's single documented Protocol-narrowing —
    no mirror type, no ``cast``, no ignore). Tests patch the ``ast_compare``
    module attribute to inject comparison behavior.
    """

    def __call__(
        self,
        body_a: str,
        bindings_a: dict[str, str],
        body_b: str,
        bindings_b: dict[str, str],
        known_values: dict[str, Any] | None = None,
    ) -> ComparisonResult: ...


ast_compare: _AstCompare = getattr(ast_equiv, "compare")


@dataclass(frozen=True)
class _AlgorithmComparison:
    """Typed result of an ``ast_compare``-driven algorithm comparison.

    ``equivalent`` is ``None`` when the comparison could not be decided for
    a **benign** reason (empty body, missing bindings, non-constant direct
    value, incomplete known values). ``parse_failed`` is ``True`` only when
    ``ast_compare`` raised ``ValueError``/``SyntaxError``; benign inconclusive
    cases leave it ``False``. The two fields are inspected independently by
    the caller — a parse failure distinguishes "algorithm body could not be
    parsed" from "algorithm evaluation is simply undecidable here".
    """

    equivalent: bool | None
    parse_failed: bool = False


_BENIGN_INCONCLUSIVE = _AlgorithmComparison(equivalent=None, parse_failed=False)
_PARSE_FAILED = _AlgorithmComparison(equivalent=None, parse_failed=True)


def _comparison_from_equivalence(equivalent: object) -> _AlgorithmComparison:
    if equivalent is True:
        return _AlgorithmComparison(equivalent=True)
    if equivalent is False:
        return _AlgorithmComparison(equivalent=False)
    return _BENIGN_INCONCLUSIVE


_SAFE_SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _no_symbol_candidates(_concept_id: ConceptId | str) -> Sequence[str]:
    return ()


def collect_known_values(
    variable_concepts: Sequence[ConceptId | str],
    value_of: Callable[[ConceptId | str], ValueResult],
) -> dict[ConceptId, Any]:
    """Resolve numeric values for a list of concept IDs.

    Shared implementation used by BoundWorld and OverlayWorld.
    """
    known: dict[ConceptId, Any] = {}
    for cid in variable_concepts:
        normalized_cid = to_concept_id(cid)
        vr = value_of(normalized_cid)
        if vr.status is ValueStatus.DETERMINED and vr.claims:
            value = vr.claims[0].value
            if not isinstance(value, bool) and isinstance(value, int | float):
                known[normalized_cid] = float(value)
    return known


class ActiveClaimResolver:
    """Resolve values and derived values for a belief-space view."""

    def __init__(
        self,
        *,
        parameterizations_for: Callable[[ConceptId | str], list[ParameterizationEdge]],
        is_param_compatible: Callable[[ParameterizationEdge], bool],
        value_of: Callable[[ConceptId | str], ValueResult],
        extract_variable_concepts: Callable[[ActiveClaim], list[str]],
        collect_known_values: Callable[
            [Sequence[ConceptId | str]], dict[ConceptId, Any]
        ],
        extract_bindings: Callable[[ActiveClaim], dict[str, str]],
        concept_symbol_candidates: Callable[[ConceptId | str], Sequence[str]]
        | None = None,
    ) -> None:
        self._parameterizations_for = parameterizations_for
        self._is_param_compatible = is_param_compatible
        self._value_of = value_of
        self._extract_variable_concepts = extract_variable_concepts
        self._collect_known_values = collect_known_values
        self._extract_bindings = extract_bindings
        self._concept_symbol_candidates = (
            concept_symbol_candidates or _no_symbol_candidates
        )

    def derived_value(
        self,
        concept_id: ConceptId | str,
        *,
        override_values: Mapping[str, ScalarValue | None] | None = None,
        _derivation_stack: set[ConceptId] | None = None,
    ) -> DerivedResult:
        typed_concept_id = to_concept_id(concept_id)
        if _derivation_stack is None:
            _derivation_stack = set()

        params = self._parameterizations_for(typed_concept_id)
        if not params:
            return DerivedResult(
                concept_id=typed_concept_id, status=ValueStatus.NO_RELATIONSHIP
            )

        saw_compatible_candidate = False
        saw_conflicted_candidate = False
        saw_underspecified_candidate = False
        derived_candidates: list[DerivedResult] = []

        for param in params:
            if not self._is_param_compatible(param):
                continue
            saw_compatible_candidate = True

            candidate = self._derive_from_parameterization(
                typed_concept_id,
                param,
                override_values=override_values,
                derivation_stack=_derivation_stack,
            )
            if candidate.status is ValueStatus.DERIVED:
                derived_candidates.append(candidate)
                continue
            if candidate.status is ValueStatus.CONFLICTED:
                saw_conflicted_candidate = True
            elif candidate.status is ValueStatus.UNDERSPECIFIED:
                saw_underspecified_candidate = True

        if not saw_compatible_candidate:
            return DerivedResult(
                concept_id=typed_concept_id, status=ValueStatus.NO_RELATIONSHIP
            )

        if derived_candidates:
            derived_values = {candidate.value for candidate in derived_candidates}
            if len(derived_values) != 1:
                return DerivedResult(
                    concept_id=typed_concept_id, status=ValueStatus.CONFLICTED
                )
            return derived_candidates[0]

        if saw_conflicted_candidate:
            return DerivedResult(
                concept_id=typed_concept_id, status=ValueStatus.CONFLICTED
            )
        if saw_underspecified_candidate:
            return DerivedResult(
                concept_id=typed_concept_id, status=ValueStatus.UNDERSPECIFIED
            )
        return DerivedResult(
            concept_id=typed_concept_id, status=ValueStatus.UNDERSPECIFIED
        )

    def value_of_from_active(
        self,
        active: Sequence[ActiveClaim],
        concept_id: ConceptId | str,
    ) -> ValueResult:
        typed_concept_id = to_concept_id(concept_id)
        active_claims = tuple(active)
        if not active_claims:
            return ValueResult(
                concept_id=typed_concept_id, status=ValueStatus.NO_CLAIMS
            )

        algo_claims = [
            claim for claim in active_claims if claim.claim_type is ClaimType.ALGORITHM
        ]
        value_claims = [
            claim
            for claim in active_claims
            if claim.claim_type is not ClaimType.ALGORITHM
        ]

        if value_claims and algo_claims:
            direct_values: dict[tuple[type[object], ScalarValue], ScalarValue] = {}
            for claim in value_claims:
                value = claim.value
                if value is not None:
                    direct_values[(type(value), value)] = value
            if not direct_values:
                return ValueResult(
                    concept_id=typed_concept_id,
                    status=ValueStatus.NO_VALUES,
                    claims=active_claims,
                )
            if len(direct_values) != 1:
                return ValueResult(
                    concept_id=typed_concept_id,
                    status=ValueStatus.CONFLICTED,
                    claims=active_claims,
                )

            direct_value = next(iter(direct_values.values()))
            unevaluable_parse_failed = False
            unevaluable_benign = False
            for claim in algo_claims:
                comparison = self._algorithm_matches_direct_value(claim, direct_value)
                if comparison.parse_failed:
                    unevaluable_parse_failed = True
                    continue
                if comparison.equivalent is None:
                    unevaluable_benign = True
                    continue
                if not comparison.equivalent:
                    return ValueResult(
                        concept_id=typed_concept_id,
                        status=ValueStatus.CONFLICTED,
                        claims=active_claims,
                    )
            # No parseable algorithm disagreed. Classify the remaining
            # unevaluable cases:
            #   * parse-failed only       → abstention, consensus stands
            #     (DETERMINED + ALGORITHM_UNPARSEABLE annotation).
            #   * benign-inconclusive present → preserve existing
            #     CONFLICTED semantics (benign inconclusive is out of scope
            #     for the Commit 5 abstention rule).
            #   * neither                 → clean DETERMINED.
            if unevaluable_benign:
                return ValueResult(
                    concept_id=typed_concept_id,
                    status=ValueStatus.CONFLICTED,
                    claims=active_claims,
                    reason=(
                        ValueResultReason.ALGORITHM_UNPARSEABLE
                        if unevaluable_parse_failed
                        else None
                    ),
                )
            if unevaluable_parse_failed:
                return ValueResult(
                    concept_id=typed_concept_id,
                    status=ValueStatus.DETERMINED,
                    claims=active_claims,
                    reason=ValueResultReason.ALGORITHM_UNPARSEABLE,
                )
            return ValueResult(
                concept_id=typed_concept_id,
                status=ValueStatus.DETERMINED,
                claims=active_claims,
            )

        if algo_claims and not value_claims:
            if len(algo_claims) == 1:
                return ValueResult(
                    concept_id=typed_concept_id,
                    status=ValueStatus.DETERMINED,
                    claims=active_claims,
                )

            all_var_concepts: set[ConceptId] = set()
            for claim in algo_claims:
                all_var_concepts.update(
                    to_concept_id(variable_concept_id)
                    for variable_concept_id in self._extract_variable_concepts(claim)
                )
            all_var_concepts.discard(typed_concept_id)

            known_values = self._collect_known_values(tuple(all_var_concepts))
            comparison = self._all_algorithms_equivalent(algo_claims, known_values)
            if comparison.equivalent is True:
                return ValueResult(
                    concept_id=typed_concept_id,
                    status=ValueStatus.DETERMINED,
                    claims=active_claims,
                )
            return ValueResult(
                concept_id=typed_concept_id,
                status=ValueStatus.CONFLICTED,
                claims=active_claims,
                reason=(
                    ValueResultReason.ALGORITHM_UNPARSEABLE
                    if comparison.parse_failed
                    else None
                ),
            )

        values: set[tuple[type[object], ScalarValue]] = set()
        for claim in active_claims:
            value = claim.value
            if value is not None:
                values.add((type(value), value))
        if not values:
            return ValueResult(
                concept_id=typed_concept_id,
                status=ValueStatus.NO_VALUES,
                claims=active_claims,
            )
        if len(values) == 1:
            return ValueResult(
                concept_id=typed_concept_id,
                status=ValueStatus.DETERMINED,
                claims=active_claims,
            )
        return ValueResult(
            concept_id=typed_concept_id,
            status=ValueStatus.CONFLICTED,
            claims=active_claims,
        )

    def _derive_from_parameterization(
        self,
        concept_id: ConceptId,
        param: ParameterizationEdge,
        *,
        override_values: Mapping[str, ScalarValue | None] | None,
        derivation_stack: set[ConceptId],
    ) -> DerivedResult:
        if not param.sympy:
            return DerivedResult(
                concept_id=concept_id, status=ValueStatus.UNDERSPECIFIED
            )

        effective_inputs = [iid for iid in param.input_concept_ids if iid != concept_id]

        input_values: dict[ConceptId, float] = {}
        for input_id in effective_inputs:
            override_value = self._coerce_override_value(override_values, input_id)
            if override_value is not None:
                input_values[input_id] = override_value
                continue

            value_result = self._value_of(input_id)
            if value_result.status is ValueStatus.DETERMINED:
                value = value_result.claims[0].value if value_result.claims else None
                if isinstance(value, bool) or not isinstance(value, int | float):
                    return DerivedResult(
                        concept_id=concept_id, status=ValueStatus.UNDERSPECIFIED
                    )
                input_values[input_id] = float(value)
                continue

            if value_result.status is ValueStatus.CONFLICTED:
                return DerivedResult(
                    concept_id=concept_id, status=ValueStatus.CONFLICTED
                )

            if input_id in derivation_stack:
                return DerivedResult(
                    concept_id=concept_id, status=ValueStatus.UNDERSPECIFIED
                )

            derivation_stack.add(input_id)
            try:
                derived = self.derived_value(
                    input_id,
                    override_values=override_values,
                    _derivation_stack=derivation_stack,
                )
            finally:
                derivation_stack.discard(input_id)

            if derived.status is ValueStatus.DERIVED and derived.value is not None:
                input_values[input_id] = float(derived.value)
                continue
            if derived.status is ValueStatus.CONFLICTED:
                return DerivedResult(
                    concept_id=concept_id, status=ValueStatus.CONFLICTED
                )
            return DerivedResult(
                concept_id=concept_id, status=ValueStatus.UNDERSPECIFIED
            )

        result = self._evaluate_parameterization(
            param,
            input_values=input_values,
            output_concept_id=concept_id,
        )
        if result is None:
            return DerivedResult(
                concept_id=concept_id, status=ValueStatus.UNDERSPECIFIED
            )

        return DerivedResult(
            concept_id=concept_id,
            status=ValueStatus.DERIVED,
            value=result,
            formula=param.formula,
            input_values=input_values,
            exactness=param.exactness,
        )

    def _evaluate_parameterization(
        self,
        param: ParameterizationEdge,
        *,
        input_values: Mapping[ConceptId, float],
        output_concept_id: ConceptId,
    ) -> float | None:
        def _value_or_none(evaluation: ParameterizationEvaluation) -> float | None:
            if evaluation.status is ParameterizationEvaluationStatus.VALUE:
                return evaluation.value
            return None

        sympy_expr = param.sympy
        if not sympy_expr:
            return None

        output_key = "__out__"
        alias_map = self._parameterization_symbol_aliases(
            param, output_concept_id=output_concept_id
        )
        if not alias_map:
            return _value_or_none(
                evaluate_parameterization(
                    sympy_expr,
                    {str(input_id): value for input_id, value in input_values.items()},
                    str(output_concept_id),
                )
            )

        replacement_candidates: list[tuple[str, str]] = []
        symbol_targets: dict[str, str] = {}
        input_index = 0
        for alias_concept_id in alias_map:
            if alias_concept_id == output_concept_id:
                target_symbol = output_key
            else:
                target_symbol = f"__in_{input_index}__"
                input_index += 1
            replacement_candidates.append((str(alias_concept_id), target_symbol))
            symbol_targets[str(alias_concept_id)] = target_symbol

        rewritten = rewrite_parameterization_symbols(
            sympy_expr,
            symbol_aliases={
                str(alias_concept_id): aliases
                for alias_concept_id, aliases in alias_map.items()
            },
            symbol_targets=symbol_targets,
        )

        if rewritten == sympy_expr:
            return _value_or_none(
                evaluate_parameterization(
                    sympy_expr,
                    {str(input_id): value for input_id, value in input_values.items()},
                    str(output_concept_id),
                )
            )

        safe_values: dict[str, float] = {}
        for candidate_concept_id, target_symbol in replacement_candidates:
            if candidate_concept_id == str(output_concept_id):
                continue
            value = input_values.get(to_concept_id(candidate_concept_id))
            if value is not None:
                safe_values[target_symbol] = value
        return _value_or_none(
            evaluate_parameterization(rewritten, safe_values, output_key)
        )

    def _parameterization_symbol_aliases(
        self,
        param: ParameterizationEdge,
        *,
        output_concept_id: ConceptId,
    ) -> dict[ConceptId, tuple[str, ...]]:
        concept_ids = (output_concept_id, *param.input_concept_ids)
        aliases: dict[ConceptId, tuple[str, ...]] = {}
        for concept_id in concept_ids:
            candidates = [
                candidate
                for candidate in self._concept_symbol_candidates(concept_id)
                if _SAFE_SYMBOL_RE.match(candidate)
            ]
            if candidates:
                aliases[concept_id] = tuple(dict.fromkeys(candidates))
        return aliases

    @staticmethod
    def _coerce_override_value(
        override_values: Mapping[str, ScalarValue | None] | None,
        input_id: ConceptId,
    ) -> float | None:
        override_key = str(input_id)
        if not override_values or override_key not in override_values:
            return None
        override_value = override_values[override_key]
        if override_value is None:
            return None
        if isinstance(override_value, bool) or not isinstance(
            override_value, int | float
        ):
            raise ValueError(
                f"Invalid override value for {override_key!r}: {override_value!r}"
            )
        return float(override_value)

    def _algorithm_matches_direct_value(
        self,
        claim: ActiveClaim,
        direct_value: ScalarValue | None,
    ) -> _AlgorithmComparison:
        body = claim.body
        if not body:
            return _BENIGN_INCONCLUSIVE

        bindings = self._extract_bindings(claim)
        if not bindings:
            return _BENIGN_INCONCLUSIVE

        constant_body = _constant_algorithm_body(direct_value)
        if constant_body is None:
            return _BENIGN_INCONCLUSIVE

        concept_ids = [
            to_concept_id(concept_id) for concept_id in dict.fromkeys(bindings.values())
        ]
        known_values = self._collect_known_values(concept_ids)
        if any(concept_id not in known_values for concept_id in concept_ids):
            return _BENIGN_INCONCLUSIVE

        try:
            result = ast_compare(
                body,
                bindings,
                constant_body,
                {},
                known_values={
                    str(concept_id): value for concept_id, value in known_values.items()
                },
            )
        except (ValueError, SyntaxError, AlgorithmParseError, RecursionError) as exc:
            logging.warning(
                "ast_compare failed for algorithm-vs-direct comparison %s: %s",
                claim.claim_id,
                exc,
            )
            return _PARSE_FAILED

        return _comparison_from_equivalence(result.equivalent)

    def _all_algorithms_equivalent(
        self,
        algo_claims: Sequence[ActiveClaim],
        known_values: Mapping[ConceptId, Any],
    ) -> _AlgorithmComparison:
        for i in range(len(algo_claims)):
            for j in range(i + 1, len(algo_claims)):
                body_a = algo_claims[i].body or ""
                body_b = algo_claims[j].body or ""
                if not body_a or not body_b:
                    # Benign: cannot compare without bodies. Not a parse
                    # failure — mirror previous behavior of signalling
                    # non-equivalence to the caller.
                    return _AlgorithmComparison(equivalent=False)
                bindings_a = self._extract_bindings(algo_claims[i])
                bindings_b = self._extract_bindings(algo_claims[j])
                try:
                    result = ast_compare(
                        body_a,
                        bindings_a,
                        body_b,
                        bindings_b,
                        known_values=(
                            {
                                str(concept_id): value
                                for concept_id, value in known_values.items()
                            }
                            if known_values
                            else None
                        ),
                    )
                except (
                    ValueError,
                    SyntaxError,
                    AlgorithmParseError,
                    RecursionError,
                ) as exc:
                    logging.warning(
                        "ast_compare failed in algorithm equivalence check: %s", exc
                    )
                    return _PARSE_FAILED
                comparison = _comparison_from_equivalence(result.equivalent)
                if comparison.equivalent is not True:
                    return comparison
        return _AlgorithmComparison(equivalent=True)


def _constant_algorithm_body(value: ScalarValue | None) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return f"def compute():\n    return {float(value)!r}\n"
