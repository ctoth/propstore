from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeAlias, cast

import pytest
import yaml

from gunray.adapter import GunrayEvaluator
from gunray.conformance_adapter import GunrayConformanceEvaluator
from gunray.disagreement import complement as gunray_complement
from gunray.parser import parse_atom_text
from gunray.schema import DefeasibleTheory as SuiteTheory
from gunray.schema import ClosurePolicy, MarkingPolicy
from gunray.schema import Rule as SuiteRule
from gunray.types import Constant, GroundAtom as GunrayGroundAtom, Variable
from propstore.resources import load_resource_text


Scalar: TypeAlias = str | int | float | bool
FactTuple: TypeAlias = tuple[Scalar, ...]
PredicateFacts: TypeAlias = dict[str, list[FactTuple]]
DefeasibleSections: TypeAlias = dict[str, PredicateFacts]


@dataclass(frozen=True)
class SuiteCase:
    name: str
    description: str
    source: str
    tags: list[str]
    theory: SuiteTheory | None = None
    expect: DefeasibleSections | None = None
    expect_per_policy: dict[str, DefeasibleSections] | None = None
    skip: str | None = None


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


_DEFEASIBLE_RESOURCE_ROOT = "conformance/defeasible"

_GUNRAY_TRANCHE_IDS = (
    "basic/depysible_birds::depysible_not_flies_tweety",
    "superiority/maher_example2_tweety::maher_example2_tweety",
    "closure/morris_core_examples::morris_example6_students_movies_distinguishes_closures",
)

_PROPSTORE_TRANSLATION_TRANCHE_IDS = (
    "basic/goldszmidt_example1_nixon::goldszmidt_example1_pacifist_conflict",
    "superiority/maher_example2_tweety::maher_example2_tweety",
)


def _case_id(resource_path: str, case: SuiteCase) -> str:
    relative = Path(resource_path).with_suffix("")
    return f"{relative.as_posix()}::{case.name}"


def _load_resource_cases(resource_path: str) -> list[SuiteCase]:
    raw = yaml.safe_load(
        load_resource_text(f"{_DEFEASIBLE_RESOURCE_ROOT}/{resource_path}")
    )
    if not isinstance(raw, dict):
        raise AssertionError(f"Conformance resource {resource_path} must be a mapping")
    if "tests" in raw:
        base_source = _optional_string(raw.get("source")) or resource_path
        base_tags = _string_list(raw.get("tags", []))
        entries = raw.get("tests")
        if not isinstance(entries, list):
            raise AssertionError(f"{resource_path}: tests must be a list")
        return [
            _case_from_mapping(
                entry,
                source=base_source,
                tags=base_tags,
                path=f"{resource_path}.tests[{index}]",
            )
            for index, entry in enumerate(entries)
        ]
    return [_case_from_mapping(raw, source=resource_path, tags=[], path=resource_path)]


def _case_from_mapping(
    raw: object,
    *,
    source: str,
    tags: list[str],
    path: str,
) -> SuiteCase:
    data = _mapping(raw, path)
    theory = (
        _theory_from_mapping(data["theory"], f"{path}.theory")
        if "theory" in data
        else None
    )
    expect = (
        _sections(data["expect"], f"{path}.expect")
        if "expect" in data
        else None
    )
    expect_per_policy = None
    if "expect_per_policy" in data:
        policy_map = _mapping(data["expect_per_policy"], f"{path}.expect_per_policy")
        expect_per_policy = {
            str(policy_name): _sections(
                expectation,
                f"{path}.expect_per_policy.{policy_name}",
            )
            for policy_name, expectation in policy_map.items()
        }
    case_source = _optional_string(data.get("source")) or source
    case_tags = [*tags, *_string_list(data.get("tags", []))]
    return SuiteCase(
        name=_required_string(data, "name", path),
        description=_required_string(data, "description", path),
        source=case_source,
        tags=case_tags,
        theory=theory,
        expect=expect,
        expect_per_policy=expect_per_policy,
        skip=_optional_string(data.get("skip")),
    )


def _theory_from_mapping(raw: object, path: str) -> SuiteTheory:
    data = _mapping(raw, path)
    return SuiteTheory(
        facts=_predicate_facts(data.get("facts", {}), f"{path}.facts"),
        strict_rules=_rules(data.get("strict_rules", []), f"{path}.strict_rules"),
        defeasible_rules=_rules(
            data.get("defeasible_rules", []),
            f"{path}.defeasible_rules",
        ),
        defeaters=_rules(data.get("defeaters", []), f"{path}.defeaters"),
        superiority=_pairs(data.get("superiority", []), f"{path}.superiority"),
        conflicts=_pairs(data.get("conflicts", []), f"{path}.conflicts"),
    )


def _rules(raw: object, path: str) -> list[SuiteRule]:
    return [
        SuiteRule(
            id=_required_string(_mapping(item, f"{path}[{index}]"), "id", f"{path}[{index}]"),
            head=_required_string(_mapping(item, f"{path}[{index}]"), "head", f"{path}[{index}]"),
            body=_string_list(_mapping(item, f"{path}[{index}]").get("body", [])),
        )
        for index, item in enumerate(_sequence(raw, path))
    ]


def _pairs(raw: object, path: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for index, item in enumerate(_sequence(raw, path)):
        pair = _sequence(item, f"{path}[{index}]")
        if len(pair) != 2 or not all(isinstance(part, str) for part in pair):
            raise AssertionError(f"{path}[{index}] must be a two-item string pair")
        pairs.append((cast(str, pair[0]), cast(str, pair[1])))
    return pairs


def _sections(raw: object, path: str) -> DefeasibleSections:
    data = _mapping(raw, path)
    return {
        str(section): _predicate_facts(predicates, f"{path}.{section}")
        for section, predicates in data.items()
    }


def _predicate_facts(raw: object, path: str) -> PredicateFacts:
    data = _mapping(raw, path)
    result: PredicateFacts = {}
    for predicate, rows in data.items():
        row_values: list[FactTuple] = []
        for index, row in enumerate(_sequence(rows, f"{path}.{predicate}")):
            values = _sequence(row, f"{path}.{predicate}[{index}]")
            if not all(isinstance(value, str | int | float | bool) for value in values):
                raise AssertionError(f"{path}.{predicate}[{index}] must contain scalars")
            row_values.append(tuple(cast(Scalar, value) for value in values))
        result[str(predicate)] = row_values
    return result


def _mapping(raw: object, path: str) -> dict[object, object]:
    if not isinstance(raw, dict):
        raise AssertionError(f"{path} must be a mapping")
    return cast(dict[object, object], raw)


def _sequence(raw: object, path: str) -> list[object]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise AssertionError(f"{path} must be a list")
    return cast(list[object], raw)


def _string_list(raw: object) -> list[str]:
    values = _sequence(raw, "string-list")
    if not all(isinstance(value, str) for value in values):
        raise AssertionError("Expected a list of strings")
    return [cast(str, value) for value in values]


def _required_string(data: dict[object, object], key: str, path: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise AssertionError(f"{path}.{key} must be a string")
    return value


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise AssertionError("Expected optional string")
    return value


def _selected_cases(case_ids: tuple[str, ...]) -> list[tuple[Path, SuiteCase]]:
    resource_paths = sorted({case_id.split("::", 1)[0] + ".yaml" for case_id in case_ids})
    cases_by_id = {
        _case_id(resource_path, case): (Path(resource_path), case)
        for resource_path in resource_paths
        for case in _load_resource_cases(resource_path)
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
@pytest.mark.differential
def test_gunray_matches_curated_strong_negation_conformance_tranche(
    yaml_path: Path,
    case: SuiteCase,
) -> None:
    if case.skip is not None:
        pytest.skip(case.skip)

    _run_suite_case(GunrayConformanceEvaluator(), case)


def _run_suite_case(evaluator: object, case: SuiteCase) -> None:
    if case.theory is None:
        raise AssertionError("Defeasible conformance tranche requires theory cases")
    evaluate = getattr(evaluator, "evaluate", None)
    if not callable(evaluate):
        raise AssertionError("Evaluator does not expose evaluate()")

    if case.expect_per_policy is not None:
        for policy_name, expected in case.expect_per_policy.items():
            if policy_name in {policy.value for policy in ClosurePolicy}:
                actual_model = evaluate(case.theory, ClosurePolicy(policy_name))
            else:
                actual_model = evaluate(case.theory, MarkingPolicy(policy_name))
            _assert_sections(case.name, expected, _extract_sections(actual_model), policy_name)
        return

    if case.expect is None:
        raise AssertionError("Defeasible conformance tranche requires expectations")
    actual_model = evaluate(case.theory, MarkingPolicy.BLOCKING)
    _assert_sections(
        case.name,
        case.expect,
        _extract_sections(actual_model),
        MarkingPolicy.BLOCKING.value,
    )


def _extract_sections(raw_model: object) -> dict[str, dict[str, set[FactTuple]]]:
    sections = getattr(raw_model, "sections", raw_model)
    if not isinstance(sections, dict):
        raise AssertionError("Defeasible model must expose sections")
    result: dict[str, dict[str, set[FactTuple]]] = {}
    for section, predicates in sections.items():
        if not isinstance(section, str) or not isinstance(predicates, dict):
            raise AssertionError("Defeasible sections must be nested mappings")
        result[section] = {
            str(predicate): {tuple(cast(tuple[Scalar, ...], row)) for row in rows}
            for predicate, rows in predicates.items()
        }
    return result


def _assert_sections(
    case_name: str,
    expected: DefeasibleSections,
    actual: dict[str, dict[str, set[FactTuple]]],
    policy: str,
) -> None:
    for section_name, predicates in expected.items():
        assert section_name in actual, (
            f"{case_name} policy {policy!r}: missing section {section_name!r}"
        )
        for predicate, rows in predicates.items():
            actual_rows = actual[section_name].get(predicate, set())
            assert actual_rows == set(rows), (
                f"{case_name} policy {policy!r} section {section_name!r} "
                f"predicate {predicate!r}: expected {set(rows)!r}, got {actual_rows!r}"
            )


def _build_term_document(term: Variable | Constant):
    from propstore.families.documents.rules import TermDocument

    if isinstance(term, Variable):
        return TermDocument(kind="var", name=term.name, value=None)
    if isinstance(term, Constant):
        return TermDocument(kind="const", name=None, value=term.value)
    raise TypeError(f"Unsupported Gunray term for translator tranche: {type(term).__name__}")


def _build_atom_document(atom_text: str):
    from propstore.families.documents.rules import AtomDocument

    parsed = parse_atom_text(atom_text)
    predicate, negated = _decode_gunray_predicate_token(parsed.predicate)
    return AtomDocument(
        predicate=predicate,
        terms=tuple(_build_term_document(term) for term in parsed.terms),
        negated=negated,
    )


def _build_rule_document(rule: SuiteRule, *, kind: str):
    from propstore.families.documents.rules import BodyLiteralDocument, RuleDocument

    return RuleDocument(
        id=rule.id,
        kind=cast("str", kind),
        head=_build_atom_document(rule.head),
        body=tuple(
            BodyLiteralDocument(
                kind="positive",
                atom=_build_atom_document(atom_text),
            )
            for atom_text in rule.body
        ),
    )


def _build_rule_file(theory: SuiteTheory):
    from quire.documents import LoadedDocument
    from propstore.families.documents.rules import RuleSourceDocument, RulesFileDocument
    from propstore.rule_files import LoadedRuleFile

    rule_documents = [
        *(_build_rule_document(rule, kind="strict") for rule in theory.strict_rules),
        *(_build_rule_document(rule, kind="defeasible") for rule in theory.defeasible_rules),
        *(
            _build_rule_document(rule, kind="proper_defeater")
            for rule in theory.defeaters
        ),
    ]
    loaded_document = LoadedDocument(
        filename="suite-derived.yaml",
        source_path=None,
        knowledge_root=None,
        document=RulesFileDocument(
            source=RuleSourceDocument(paper="datalog-conformance-suite"),
            rules=tuple(rule_documents),
            superiority=tuple(theory.superiority),
        ),
    )
    return LoadedRuleFile.from_loaded_document(loaded_document)


def _build_fact_atoms(theory: SuiteTheory):
    from argumentation.aspic import GroundAtom

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
    from quire.documents import LoadedDocument
    from propstore.families.documents.predicates import (
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

    assert case.theory is not None
    rule_file = _build_rule_file(case.theory)
    facts = _build_fact_atoms(case.theory)
    registry = _build_registry(case.theory)
    translated = translate_to_theory([rule_file], facts, registry)
    if policy_name is None:
        return GunrayEvaluator().evaluate(
            translated,
            marking_policy=MarkingPolicy.BLOCKING,
        )
    if policy_name in {policy.value for policy in ClosurePolicy}:
        return GunrayEvaluator().evaluate(
            translated,
            closure_policy=ClosurePolicy(policy_name),
        )
    return GunrayEvaluator().evaluate(
        translated,
        marking_policy=MarkingPolicy(policy_name),
    )


@pytest.mark.parametrize(
    ("yaml_path", "case"),
    _PROPSTORE_TRANSLATION_TRANCHE_CASES,
    ids=_suite_cases_to_ids(_PROPSTORE_TRANSLATION_TRANCHE_CASES),
)
@pytest.mark.differential
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
