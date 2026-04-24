"""Repository-family loading helpers for the grounding pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from argumentation.aspic import GroundAtom
from propstore.families.concepts.stages import LoadedConcept, parse_concept_record_document
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.facts import extract_facts
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry
from propstore.predicate_files import LoadedPredicateFile
from propstore.repository import Repository
from propstore.rule_files import LoadedRuleFile


@dataclass(frozen=True)
class GroundingInputs:
    rule_files: tuple[LoadedRuleFile, ...]
    facts: tuple[GroundAtom, ...]
    registry: PredicateRegistry | None


def load_grounding_inputs(
    repo: Repository,
    *,
    commit: str | None = None,
) -> GroundingInputs:
    """Load the repository inputs consumed by the grounding pipeline."""

    tree = repo.tree(commit=commit)
    predicate_files = tuple(
        LoadedPredicateFile(
            filename=ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            document=handle.document,
        )
        for ref in repo.families.predicates.iter(commit=commit)
        for handle in (
            repo.families.predicates.require_handle(ref, commit=commit),
        )
    )
    rule_files: tuple[LoadedRuleFile, ...] = tuple(
        LoadedRuleFile(
            filename=ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            document=handle.document,
        )
        for ref in repo.families.rules.iter(commit=commit)
        for handle in (
            repo.families.rules.require_handle(ref, commit=commit),
        )
    )

    if not predicate_files:
        return GroundingInputs(rule_files=rule_files, facts=(), registry=None)

    registry = PredicateRegistry.from_files(predicate_files)
    concepts = [
        LoadedConcept(
            filename=ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            record=parse_concept_record_document(handle.document),
            document=handle.document,
        )
        for ref in repo.families.concepts.iter(commit=commit)
        for handle in (
            repo.families.concepts.require_handle(ref, commit=commit),
        )
    ]
    facts = extract_facts(concepts, registry)
    return GroundingInputs(
        rule_files=rule_files,
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
        if inputs.rule_files:
            raise ValueError(
                "knowledge root has rules/ but no predicates/; grounding requires "
                "declared predicates"
            )
        return GroundedRulesBundle.empty()

    return ground(
        inputs.rule_files,
        inputs.facts,
        inputs.registry,
        return_arguments=return_arguments,
    )
