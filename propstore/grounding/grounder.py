"""Ground a rule/fact program through gunray into a non-committal bundle.

:func:`ground` is the top-level grounding entry: it compiles the program to a
``gunray.DefeasibleTheory`` (:mod:`propstore.grounding.translator`), evaluates it
with a trace, then normalizes the result into a :class:`GroundedRulesBundle` with
all four marking sections present, deterministically ordered arguments, and the
grounding inspection.

Double-count discipline: the bundle stores gunray's own
:class:`gunray.GroundingInspection` directly. Any consumer needing the flattened
ground-rule instances calls ``inspection.all_rule_instances`` (gunray's canonical
flatten) — this module never reconstructs that list by slicing-and-re-adding the
per-kind tuples, which would double-count.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType

import gunray

from propstore.families.rules import DefeasibleRule, RuleSuperiority
from propstore.grounding.bundle import (
    SECTION_NAMES,
    GroundedRulesBundle,
    SectionMap,
    SectionRows,
    build_empty_sections,
)
from propstore.grounding.predicates import PredicateRegistry
from propstore.grounding.translator import translate_to_theory


def ground(
    rules: Sequence[DefeasibleRule],
    facts: tuple[gunray.GroundAtom, ...],
    registry: PredicateRegistry,
    *,
    superiority: Sequence[RuleSuperiority] = (),
    marking_policy: gunray.MarkingPolicy = gunray.MarkingPolicy.BLOCKING,
    closure_policy: gunray.ClosurePolicy | None = None,
    return_arguments: bool = True,
    max_arguments: int | None = None,
) -> GroundedRulesBundle:
    """Ground ``rules`` over ``facts`` and return an immutable result bundle.

    On a gunray argument-enumeration budget overflow, returns a bundle with
    ``status="budget_exceeded"``, the partial arguments, the partial inspection,
    and empty (but all-four-key) sections — never raising past this boundary.
    """

    theory = translate_to_theory(rules, facts, registry, superiority=superiority)
    evaluator = gunray.GunrayEvaluator()
    try:
        raw_model, trace = evaluator.evaluate_with_trace(
            theory,
            marking_policy=marking_policy,
            closure_policy=closure_policy,
            max_arguments=max_arguments,
        )
    except gunray.EnumerationExceeded as exc:
        partial_trace = exc.partial_trace
        inspection = (
            None if partial_trace is None else partial_trace.grounding_inspection
        )
        return GroundedRulesBundle(
            source_rules=tuple(rules),
            source_facts=facts,
            sections=build_empty_sections(),
            source_superiority=tuple(superiority),
            arguments=_sort_arguments(tuple(exc.partial_arguments)),
            grounding_inspection=inspection,
            status="budget_exceeded",
            budget_reason=exc.reason,
        )

    arguments = _sort_arguments(tuple(trace.arguments)) if return_arguments else ()
    return GroundedRulesBundle(
        source_rules=tuple(rules),
        source_facts=facts,
        sections=_normalise_sections(raw_model.sections),
        source_superiority=tuple(superiority),
        arguments=arguments,
        grounding_inspection=trace.grounding_inspection,
        status="complete",
    )


def _normalise_sections(raw_sections: gunray.DefeasibleSections) -> SectionMap:
    """Restore all four section keys with frozen, read-only contents.

    gunray drops empty sections from its model; this re-adds every missing key as
    an empty map so the non-commitment contract (yes/no/undecided/unknown always
    present) holds.
    """

    normalised: dict[str, Mapping[str, SectionRows]] = {}
    for name in SECTION_NAMES:
        inner_raw = raw_sections.get(name)
        inner: dict[str, SectionRows] = {}
        if inner_raw is not None:
            for predicate, rows in inner_raw.items():
                inner[predicate] = frozenset(tuple(row) for row in rows)
        normalised[name] = MappingProxyType(inner)
    return MappingProxyType(normalised)


def _sort_arguments(
    arguments: tuple[gunray.Argument, ...],
) -> tuple[gunray.Argument, ...]:
    """Deterministically order arguments; fall back to string order for stand-ins."""

    try:
        return tuple(sorted(arguments, key=_argument_sort_key))
    except AttributeError:
        return tuple(sorted(arguments, key=str))


def _argument_sort_key(
    argument: gunray.Argument,
) -> tuple[tuple[str, ...], str, tuple[str, ...]]:
    rule_ids = tuple(sorted(rule.rule_id for rule in argument.rules))
    conclusion = argument.conclusion
    conclusion_args = tuple(str(arg) for arg in conclusion.arguments)
    return (rule_ids, conclusion.predicate, conclusion_args)
