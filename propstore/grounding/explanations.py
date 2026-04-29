"""Textual explanation helpers for the Gunray grounding backend."""

from __future__ import annotations

from dataclasses import dataclass

import gunray
from argumentation.aspic import GroundAtom, Scalar

from propstore.grounding.predicates import PredicateRegistry
from propstore.grounding.translator import translate_to_theory
from propstore.rule_files import LoadedRuleFile


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
    marking_policy: gunray.MarkingPolicy = gunray.MarkingPolicy.BLOCKING,
) -> GroundingTextExplanation:
    """Render Gunray's textual dialectical explanation for ``atom``.

    Gunray owns the dialectical tree construction and prose renderer.
    Propstore owns the repository-to-theory projection, query parsing,
    and typed report envelope.
    """

    theory = translate_to_theory(rule_files, facts, registry)
    evaluator = gunray.GunrayEvaluator()
    _, trace = evaluator.evaluate_with_trace(theory, marking_policy=marking_policy)

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
    trace: gunray.DefeasibleTrace,
    predicate: str,
    arguments: tuple[Scalar, ...],
) -> gunray.DialecticalNode | None:
    return trace.tree_for_parts(predicate, arguments)


def _complement_predicate(predicate: str) -> str:
    if predicate.startswith("~"):
        return predicate[1:]
    return f"~{predicate}"


def _preference_criterion(theory: gunray.DefeasibleTheory) -> gunray.PreferenceCriterion:
    return gunray.CompositePreference(
        gunray.SuperiorityPreference(theory),
        gunray.GeneralizedSpecificity(theory),
    )
