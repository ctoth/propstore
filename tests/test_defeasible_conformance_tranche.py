from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SUITE_SRC = _REPO_ROOT.parent / "datalog-conformance-suite" / "src"

_MISSING_SOURCE_TREES = [str(_path) for _path in (_SUITE_SRC,) if not _path.exists()]
if _MISSING_SOURCE_TREES:
    pytest.skip(
        "Requires sibling source trees: " + ", ".join(_MISSING_SOURCE_TREES),
        allow_module_level=True,
    )

_SUITE_SRC_TEXT = str(_SUITE_SRC)
if _SUITE_SRC_TEXT not in sys.path:
    sys.path.insert(0, _SUITE_SRC_TEXT)

from datalog_conformance.plugin import discover_yaml_tests
from datalog_conformance.runner import YamlTestRunner
from datalog_conformance.schema import DefeasibleTheory as SuiteTheory
from datalog_conformance.schema import Rule as SuiteRule
from datalog_conformance.schema import TestCase as SuiteCase
from gunray.conformance_adapter import GunrayConformanceEvaluator
from gunray.adapter import GunrayEvaluator
from gunray.disagreement import complement as gunray_complement
from gunray.parser import parse_atom_text
from gunray.types import Constant, GroundAtom as GunrayGroundAtom, Variable


def _decode_gunray_predicate_token(token: str) -> tuple[str, bool]:
    """Decode a gunray-serialized predicate token into (positive, negated).

    Gunray encodes strong negation via a ``~`` prefix on the
    predicate name (see ``gunray.disagreement.complement``).
    Propstore stores polarity as a typed bool on ``AtomDocument`` /
    ``PredicateDocument``, so the tranche builders have to project
    from gunray's convention onto propstore's typed convention.

    This helper routes the projection through a ``GroundAtom`` ->
    ``complement`` round-trip so the ``~``-handling lives inside
    gunray's typed surface rather than as a raw string hack in the
    test file. See ``propstore.aspic_bridge._decode_grounded_predicate``
    for the mirror helper on the production code path.
    """

    probe = GunrayGroundAtom(predicate=token, arguments=())
    toggled = gunray_complement(probe)
    negated = len(toggled.predicate) < len(probe.predicate)
    positive = toggled.predicate if negated else probe.predicate
    return positive, negated


_SUITE_TESTS_ROOT = _SUITE_SRC / "datalog_conformance" / "_tests"
_DEFEASIBLE_ROOT = _SUITE_TESTS_ROOT / "defeasible"

_GUNRAY_TRANCHE_IDS = (
    "basic/depysible_birds::depysible_not_flies_tweety",
    "superiority/maher_example2_tweety::maher_example2_tweety",
    "closure/morris_core_examples::morris_example6_students_movies_distinguishes_closures",
)

_PROPSTORE_TRANSLATION_TRANCHE_IDS = (
    "basic/goldszmidt_example1_nixon::goldszmidt_example1_pacifist_conflict",
)

def _case_id(yaml_path: Path, case: SuiteCase) -> str:
    relative = yaml_path.relative_to(_DEFEASIBLE_ROOT).with_suffix("")
    return f"{relative.as_posix()}::{case.name}"


def _selected_cases(case_ids: tuple[str, ...]) -> list[tuple[Path, SuiteCase]]:
    cases_by_id = {
        _case_id(yaml_path, case): (yaml_path, case)
        for yaml_path, case in discover_yaml_tests(_DEFEASIBLE_ROOT)
    }
    missing = [case_id for case_id in case_ids if case_id not in cases_by_id]
    if missing:
        raise KeyError(f"Missing conformance cases: {missing!r}")
    return [cases_by_id[case_id] for case_id in case_ids]


def _suite_cases_to_ids(cases: list[tuple[Path, SuiteCase]]) -> list[str]:
    return [_case_id(yaml_path, case) for yaml_path, case in cases]


_GUNRAY_TRANCHE_CASES = _selected_cases(_GUNRAY_TRANCHE_IDS)
_PROPSTORE_TRANSLATION_TRANCHE_CASES = _selected_cases(
    _PROPSTORE_TRANSLATION_TRANCHE_IDS
)


@pytest.mark.parametrize(
    ("yaml_path", "case"),
    _GUNRAY_TRANCHE_CASES,
    ids=_suite_cases_to_ids(_GUNRAY_TRANCHE_CASES),
)
def test_gunray_matches_curated_strong_negation_conformance_tranche(
    yaml_path: Path,
    case: SuiteCase,
) -> None:
    if case.skip is not None:
        pytest.skip(case.skip)

    runner = YamlTestRunner(GunrayConformanceEvaluator())
    runner.run_test_case(case)


def _build_term_document(term: Variable | Constant):
    from propstore.artifacts.documents.rules import TermDocument

    if isinstance(term, Variable):
        return TermDocument(kind="var", name=term.name, value=None)
    if isinstance(term, Constant):
        return TermDocument(kind="const", name=None, value=term.value)
    raise TypeError(f"Unsupported Gunray term for translator tranche: {type(term).__name__}")


def _build_atom_document(atom_text: str):
    from propstore.artifacts.documents.rules import AtomDocument

    parsed = parse_atom_text(atom_text)
    predicate, negated = _decode_gunray_predicate_token(parsed.predicate)
    return AtomDocument(
        predicate=predicate,
        terms=tuple(_build_term_document(term) for term in parsed.terms),
        negated=negated,
    )


def _build_rule_document(rule: SuiteRule, *, kind: str):
    from propstore.artifacts.documents.rules import RuleDocument

    return RuleDocument(
        id=rule.id,
        kind=cast("str", kind),
        head=_build_atom_document(rule.head),
        body=tuple(_build_atom_document(atom_text) for atom_text in rule.body),
    )


def _build_rule_file(theory: SuiteTheory):
    from propstore.loaded import LoadedDocument
    from propstore.artifacts.documents.rules import RuleSourceDocument, RulesFileDocument
    from propstore.rule_files import LoadedRuleFile

    rule_documents = [
        *(_build_rule_document(rule, kind="strict") for rule in theory.strict_rules),
        *(_build_rule_document(rule, kind="defeasible") for rule in theory.defeasible_rules),
        *(_build_rule_document(rule, kind="defeater") for rule in theory.defeaters),
    ]
    loaded_document = LoadedDocument(
        filename="suite-derived.yaml",
        source_path=None,
        knowledge_root=None,
        document=RulesFileDocument(
            source=RuleSourceDocument(paper="datalog-conformance-suite"),
            rules=tuple(rule_documents),
        ),
    )
    return LoadedRuleFile.from_loaded_document(loaded_document)


def _build_fact_atoms(theory: SuiteTheory):
    from propstore.aspic import GroundAtom

    facts: list[GroundAtom] = []
    for predicate, rows in theory.facts.items():
        _, negated = _decode_gunray_predicate_token(predicate)
        if negated:
            raise NotImplementedError(
                "Translator tranche only covers suite cases whose facts stay within "
                "the current positive-fact propstore surface"
            )
        for row in rows:
            facts.append(GroundAtom(predicate=predicate, arguments=tuple(row)))
    return tuple(facts)


def _build_registry(theory: SuiteTheory):
    from propstore.grounding.predicates import PredicateRegistry
    from propstore.loaded import LoadedDocument
    from propstore.artifacts.documents.predicates import (
        PredicateDocument,
        PredicatesFileDocument,
    )
    from propstore.predicate_files import LoadedPredicateFile

    arities: dict[str, int] = {}
    for predicate, rows in theory.facts.items():
        _, negated = _decode_gunray_predicate_token(predicate)
        if negated:
            continue
        row_list = list(rows)
        arities[predicate] = len(row_list[0]) if row_list else 0
    for rule in (*theory.strict_rules, *theory.defeasible_rules, *theory.defeaters):
        head = parse_atom_text(rule.head)
        head_positive, _ = _decode_gunray_predicate_token(head.predicate)
        arities[head_positive] = head.arity
        for atom_text in rule.body:
            body_atom = parse_atom_text(atom_text)
            body_positive, _ = _decode_gunray_predicate_token(body_atom.predicate)
            arities[body_positive] = body_atom.arity

    loaded_document = LoadedDocument(
        filename="suite-derived-predicates.yaml",
        source_path=None,
        knowledge_root=None,
        document=PredicatesFileDocument(
            predicates=tuple(
                PredicateDocument(
                    id=predicate,
                    arity=arity,
                    arg_types=tuple("Concept" for _ in range(arity)),
                    derived_from=None,
                    description=None,
                )
                for predicate, arity in sorted(arities.items())
            )
        ),
    )
    return PredicateRegistry.from_files(
        [LoadedPredicateFile.from_loaded_document(loaded_document)]
    )


def _evaluate_translated_suite_theory(case: SuiteCase, *, policy_name: str | None = None) -> object:
    from propstore.grounding.translator import translate_to_theory
    from gunray.schema import Policy

    assert case.theory is not None
    rule_file = _build_rule_file(case.theory)
    facts = _build_fact_atoms(case.theory)
    registry = _build_registry(case.theory)
    translated = translate_to_theory([rule_file], facts, registry)
    policy = None if policy_name is None else Policy(policy_name)
    return GunrayEvaluator().evaluate(translated, policy)


@pytest.mark.parametrize(
    ("yaml_path", "case"),
    _PROPSTORE_TRANSLATION_TRANCHE_CASES,
    ids=_suite_cases_to_ids(_PROPSTORE_TRANSLATION_TRANCHE_CASES),
)
def test_propstore_translation_matches_curated_suite_cases(
    yaml_path: Path,
    case: SuiteCase,
) -> None:
    if case.skip is not None:
        pytest.skip(case.skip)
    if case.theory is None:
        raise AssertionError("Translator tranche requires defeasible theory cases")

    if case.expect_per_policy is not None:
        for policy_name, expected in case.expect_per_policy.items():
            actual_model = _evaluate_translated_suite_theory(case, policy_name=policy_name)
            sections = getattr(actual_model, "sections", None)
            if not isinstance(sections, dict):
                raise AssertionError("Gunray evaluator did not return defeasible sections")
            for section_name, predicates in expected.items():
                assert section_name in sections
                for predicate, rows in predicates.items():
                    actual_rows = {
                        tuple(row) for row in sections[section_name].get(predicate, set())
                    }
                    assert actual_rows == set(rows)
        return

    actual_model = _evaluate_translated_suite_theory(case)
    expected = case.expect
    if expected is None:
        raise AssertionError("Translator tranche requires explicit expectations")

    sections = getattr(actual_model, "sections", None)
    if not isinstance(sections, dict):
        raise AssertionError("Gunray evaluator did not return defeasible sections")

    for section_name, predicates in expected.items():
        assert section_name in sections
        for predicate, rows in predicates.items():
            actual_rows = {
                tuple(row) for row in sections[section_name].get(predicate, set())
            }
            assert actual_rows == set(rows)
