"""Knowledge-root loading helpers for the grounding pipeline."""

from __future__ import annotations

from collections.abc import Sequence

from propstore.core.concepts import load_concepts
from propstore.artifacts.documents.predicates import PredicatesFileDocument
from propstore.artifacts.documents.rules import RulesFileDocument
from propstore.artifacts.schema import load_document_dir
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.facts import extract_facts
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry
from propstore.knowledge_path import KnowledgePath
from propstore.predicate_files import LoadedPredicateFile
from propstore.rule_files import LoadedRuleFile


def load_predicate_files(predicates_root: KnowledgePath | None) -> list[LoadedPredicateFile]:
    """Load all predicate declaration files from a knowledge subtree."""

    return load_document_dir(
        predicates_root,
        PredicatesFileDocument,
        wrapper=LoadedPredicateFile.from_loaded_document,
    )


def load_rule_files(rules_root: KnowledgePath | None) -> list[LoadedRuleFile]:
    """Load all DeLP rule files from a knowledge subtree."""

    return load_document_dir(
        rules_root,
        RulesFileDocument,
        wrapper=LoadedRuleFile.from_loaded_document,
    )


def build_grounded_bundle(
    knowledge_root: KnowledgePath,
    *,
    return_arguments: bool = False,
) -> GroundedRulesBundle:
    """Build the grounding bundle for one knowledge root.

    The explicit rule-free case is: both ``predicates/`` and ``rules/`` are
    absent. That repository surface has no defeasible grounding authoring, so
    the reasoning bundle is intentionally empty. If authored rules exist
    without authored predicates, the boundary fails loudly instead of guessing.
    """

    predicates_root = knowledge_root / "predicates"
    rules_root = knowledge_root / "rules"
    has_predicates = predicates_root.is_dir()
    has_rules = rules_root.is_dir()

    if not has_predicates:
        if has_rules:
            raise ValueError(
                "knowledge root has rules/ but no predicates/; grounding requires "
                "declared predicates"
            )
        return GroundedRulesBundle.empty()

    predicate_files = load_predicate_files(predicates_root)
    if not predicate_files:
        raise ValueError("predicates/ exists but contains no YAML predicate files")

    registry = PredicateRegistry.from_files(predicate_files)
    rule_files: Sequence[LoadedRuleFile] = load_rule_files(rules_root) if has_rules else ()
    concepts = load_concepts(knowledge_root / "concepts")
    facts = extract_facts(concepts, registry)
    return ground(
        rule_files,
        facts,
        registry,
        return_arguments=return_arguments,
    )
