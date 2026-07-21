"""Assemble a grounded bundle from the authored grounding substrate.

:func:`build_grounded_bundle` takes the authored predicates, rules, superiorities,
and the concept/claim fact substrate (gathered into a small :class:`GroundingRepo`)
and produces a :class:`GroundedRulesBundle`. The surface validity check is the
only place grounding refuses to proceed: ``rules/`` without ``predicates/`` is an
invalid surface; both absent is an empty (valid) bundle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.predicates import Predicate
from propstore.families.rules import DefeasibleRule, RuleSuperiority
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.facts import (
    ConceptRelations,
    GroundingFactInputs,
    extract_facts,
)
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class GroundingRepo:
    """The authored grounding substrate gathered for one grounding run."""

    predicates: tuple[Predicate, ...] = ()
    rules: tuple[DefeasibleRule, ...] = ()
    rule_superiority: tuple[RuleSuperiority, ...] = ()
    concepts: tuple[ConceptRelations, ...] = ()
    claims: tuple[Claim, ...] = ()


def load_grounding_repo(
    repo: Repository, *, commit: str | None = None
) -> GroundingRepo:
    """Gather the authored grounding substrate from a repository at ``commit``.

    Reads the predicate, defeasible-rule, rule-superiority, claim, and concept
    families from ``repo`` (the repository ``HEAD`` when ``commit`` is ``None``)
    into a :class:`GroundingRepo`. This is the one place the substrate is gathered
    from a repository; the build spine and the grounding inspection adapter both
    call it rather than re-reading families themselves.
    """

    def _documents(family_name: str) -> tuple[object, ...]:
        return tuple(
            handle.document
            for handle in repo.families.by_name(family_name).iter_handles(commit=commit)
        )

    predicates = tuple(d for d in _documents("predicate") if isinstance(d, Predicate))
    rules = tuple(
        d for d in _documents("defeasible_rule") if isinstance(d, DefeasibleRule)
    )
    superiority = tuple(
        d for d in _documents("rule_superiority") if isinstance(d, RuleSuperiority)
    )
    claims = tuple(d for d in _documents("claim") if isinstance(d, Claim))
    concepts = tuple(
        ConceptRelations(concept_id=d.concept_id, canonical_name=d.canonical_name)
        for d in _documents("concept")
        if isinstance(d, Concept)
    )
    return GroundingRepo(
        predicates=predicates,
        rules=rules,
        rule_superiority=superiority,
        concepts=concepts,
        claims=claims,
    )


def build_grounded_bundle(
    repo: GroundingRepo, *, commit: str | None = None, return_arguments: bool = False
) -> GroundedRulesBundle:
    """Ground the authored substrate into a bundle.

    ``rules/`` present with no ``predicates/`` is rejected; both absent yields an
    empty bundle (all four sections present and empty). ``commit`` is accepted for
    call-site symmetry with commit-pinned loaders.
    """

    _ = commit
    if not repo.predicates:
        if repo.rules:
            raise ValueError(
                "knowledge root has rules/ but no predicates/; "
                "grounding requires declared predicates"
            )
        return GroundedRulesBundle.empty()
    registry = PredicateRegistry.from_documents(repo.predicates)
    facts = extract_facts(
        GroundingFactInputs(concepts=repo.concepts, claims=repo.claims), registry
    )
    return ground(
        repo.rules,
        facts,
        registry,
        superiority=repo.rule_superiority,
        return_arguments=return_arguments,
    )
