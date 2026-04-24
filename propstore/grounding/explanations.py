"""Textual explanation helpers for the Gunray grounding backend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import gunray
from argumentation.aspic import GroundAtom, Scalar
from gunray.adapter import GunrayEvaluator
from gunray.schema import DefeasibleTheory, Policy
from gunray.trace import DefeasibleTrace

from propstore.grounding.predicates import PredicateRegistry
from propstore.grounding.translator import translate_to_theory
from propstore.rule_files import LoadedRuleFile

if TYPE_CHECKING:
    from gunray import DialecticalNode


@dataclass(frozen=True)
class GroundingTextExplanation:
    requested_atom: GroundAtom
    explained_atom: GroundAtom | None
    prose: str | None
    tree: str | None
    message: str | None = None


def build_grounding_text_explanation(
    rule_files: tuple[LoadedRuleFile, ...],
    facts: tuple[GroundAtom, ...],
    registry: PredicateRegistry,
    atom: GroundAtom,
    *,
    policy: Policy = Policy.BLOCKING,
) -> GroundingTextExplanation:
    """Render Gunray's textual dialectical explanation for ``atom``.

    Gunray owns the dialectical tree construction and prose renderer.
    Propstore owns the repository-to-theory projection, query parsing,
    and typed report envelope.
    """

    theory = translate_to_theory(rule_files, facts, registry)
    evaluator = GunrayEvaluator()
    _, raw_trace = evaluator.evaluate_with_trace(theory, policy)
    trace = cast(DefeasibleTrace, raw_trace)

    tree = _find_tree(trace, atom.predicate, tuple(atom.arguments))
    explained_atom = atom
    if tree is None:
        opposite_predicate = _complement_predicate(atom.predicate)
        tree = _find_tree(trace, opposite_predicate, tuple(atom.arguments))
        if tree is not None:
            explained_atom = GroundAtom(
                predicate=opposite_predicate,
                arguments=tuple(atom.arguments),
            )

    if tree is None:
        return GroundingTextExplanation(
            requested_atom=atom,
            explained_atom=None,
            prose=None,
            tree=None,
            message="Gunray did not produce a dialectical tree for this atom.",
        )

    criterion = _preference_criterion(theory)
    return GroundingTextExplanation(
        requested_atom=atom,
        explained_atom=explained_atom,
        prose=gunray.explain(tree, criterion),
        tree=gunray.render_tree(tree),
    )


def _find_tree(
    trace: DefeasibleTrace,
    predicate: str,
    arguments: tuple[Scalar, ...],
) -> "DialecticalNode | None":
    for candidate, tree in trace.trees.items():
        if candidate.predicate == predicate and tuple(candidate.arguments) == arguments:
            return tree
    return None


def _complement_predicate(predicate: str) -> str:
    if predicate.startswith("~"):
        return predicate[1:]
    return f"~{predicate}"


def _preference_criterion(theory: DefeasibleTheory) -> gunray.PreferenceCriterion:
    return gunray.CompositePreference(
        gunray.SuperiorityPreference(theory),
        gunray.GeneralizedSpecificity(theory),
    )
