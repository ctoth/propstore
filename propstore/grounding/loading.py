"""Repository-family loading helpers for the grounding pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from argumentation.aspic import GroundAtom
from propstore.families.documents.rules import RuleDocument
from propstore.families.concepts.stages import LoadedConcept, parse_concept_record_document
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.facts import GroundingFactInputs, extract_facts
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry
from propstore.repository import Repository


@dataclass(frozen=True)
class GroundingInputs:
    rules: tuple[RuleDocument, ...]
    facts: tuple[GroundAtom, ...]
    registry: PredicateRegistry | None


def load_grounding_inputs(
    repo: Repository,
    *,
    commit: str | None = None,
) -> GroundingInputs:
    """Load the repository inputs consumed by the grounding pipeline."""

    tree = repo.tree(commit=commit)
    predicates = tuple(
        handle.document
        for handle in repo.families.predicates.iter_handles(commit=commit)
    )
    rules = tuple(
        handle.document
        for handle in repo.families.rules.iter_handles(commit=commit)
    )

    if not predicates:
        return GroundingInputs(rules=rules, facts=(), registry=None)

    registry = PredicateRegistry.from_documents(predicates)
    concepts = [
        LoadedConcept(
            filename=handle.ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            record=parse_concept_record_document(handle.document),
            document=handle.document,
        )
        for handle in repo.families.concepts.iter_handles(commit=commit)
    ]
    claim_files = tuple(
        handle
        for handle in repo.families.claims.iter_handles(commit=commit)
    )
    facts = extract_facts(
        GroundingFactInputs(
            concepts=tuple(concepts),
            claim_files=claim_files,
        ),
        registry,
    )
    return GroundingInputs(
        rules=rules,
        facts=facts,
        registry=registry,
    )


def build_grounded_bundle(
    repo: Repository,
    *,
    commit: str | None = None,
    return_arguments: bool = False,
) -> GroundedRulesBundle:
    """Build the grounding bundle for one repository snapshot.

    The explicit rule-free case is: both predicate and rule families are empty.
    That repository surface has no defeasible grounding authoring, so the
    reasoning bundle is intentionally empty. If authored rules exist without
    authored predicates, the boundary fails loudly instead of guessing.
    """

    inputs = load_grounding_inputs(repo, commit=commit)

    if inputs.registry is None:
        if inputs.rules:
            raise ValueError(
                "knowledge root has rules/ but no predicates/; grounding requires "
                "declared predicates"
            )
        return GroundedRulesBundle.empty()

    return ground(
        inputs.rules,
        inputs.facts,
        inputs.registry,
        return_arguments=return_arguments,
    )
