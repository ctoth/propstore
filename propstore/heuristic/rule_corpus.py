"""Lint and test helpers for the WS-K2 extracted rule corpus."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RuleCorpusLintReport:
    papers_checked: tuple[str, ...]
    rules_checked: int
    errors: tuple[str, ...]


def validate_rule_predicate_refs(
    *,
    predicates: set[str],
    referenced: set[str],
    rule_id: str,
) -> tuple[str, ...]:
    return tuple(
        f"{rule_id}: undeclared predicate reference {ref}"
        for ref in sorted(referenced - predicates)
    )


def validate_variable_safety(
    *,
    head_terms: tuple[str, ...],
    positive_body_terms: tuple[str, ...],
    rule_id: str,
) -> tuple[str, ...]:
    body = set(positive_body_terms)
    return tuple(
        f"{rule_id}: head variable {term} is not bound in a positive body literal"
        for term in head_terms
        if term and term[0].isupper() and term not in body
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return loaded


def _predicate_refs(path: Path) -> set[str]:
    loaded = _load_yaml(path)
    declarations = loaded.get("predicates", ())
    refs: set[str] = set()
    for declaration in declarations:
        if not isinstance(declaration, dict):
            continue
        refs.add(f"{declaration['id']}/{declaration['arity']}")
    return refs


def _atom_terms(atom: dict[str, Any]) -> tuple[str, ...]:
    terms = atom.get("terms", ())
    values: list[str] = []
    if isinstance(terms, list):
        for term in terms:
            if not isinstance(term, dict):
                continue
            if term.get("kind") == "var" and isinstance(term.get("name"), str):
                values.append(str(term["name"]))
    return tuple(values)


def _body_predicate_refs(rule: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    body = rule.get("body", ())
    if not isinstance(body, list):
        return refs
    for literal in body:
        if not isinstance(literal, dict):
            continue
        atom = literal.get("atom")
        if not isinstance(atom, dict):
            continue
        terms = atom.get("terms", ())
        arity = len(terms) if isinstance(terms, list) else 0
        refs.add(f"{atom['predicate']}/{arity}")
    return refs


def _positive_body_terms(rule: dict[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    body = rule.get("body", ())
    if not isinstance(body, list):
        return ()
    for literal in body:
        if not isinstance(literal, dict) or literal.get("kind") != "positive":
            continue
        atom = literal.get("atom")
        if isinstance(atom, dict):
            values.extend(_atom_terms(atom))
    return tuple(values)


def lint_extracted_rule_corpus(
    knowledge_root: str | Path,
    *,
    target_papers: tuple[str, ...],
) -> RuleCorpusLintReport:
    root = Path(knowledge_root)
    errors: list[str] = []
    rules_checked = 0
    papers_checked: list[str] = []
    for paper in target_papers:
        predicate_file = root / "predicates" / paper / "declarations.yaml"
        rules_dir = root / "rules" / paper
        if not predicate_file.exists():
            errors.append(f"{paper}: missing predicate declarations")
            continue
        if not rules_dir.is_dir():
            errors.append(f"{paper}: missing rules directory")
            continue
        predicates = _predicate_refs(predicate_file)
        papers_checked.append(paper)
        for path in sorted(rules_dir.glob("*.yaml")):
            loaded = _load_yaml(path)
            rules = loaded.get("rules", ())
            if not isinstance(rules, list) or not rules:
                errors.append(f"{path}: no rules")
                continue
            for rule in rules:
                if not isinstance(rule, dict):
                    errors.append(f"{path}: rule entry is not a mapping")
                    continue
                rules_checked += 1
                rule_id = str(rule.get("id", path.stem))
                errors.extend(
                    validate_rule_predicate_refs(
                        predicates=predicates,
                        referenced=_body_predicate_refs(rule),
                        rule_id=rule_id,
                    )
                )
                head = rule.get("head")
                if isinstance(head, dict):
                    errors.extend(
                        validate_variable_safety(
                            head_terms=_atom_terms(head),
                            positive_body_terms=_positive_body_terms(rule),
                            rule_id=rule_id,
                        )
                    )
    return RuleCorpusLintReport(
        papers_checked=tuple(papers_checked),
        rules_checked=rules_checked,
        errors=tuple(errors),
    )


_SYNTHETIC_METADATA: dict[str, dict[str, object]] = {
    "Ioannidis_2005_WhyMostPublishedResearch": {"sample_size": 30, "bias": 0.8},
    "Begley_2012_DrugDevelopmentRaiseStandards": {"peer_reviewed": True, "blinded": False},
    "Aarts_2015_EstimatingReproducibilityPsychologicalScience": {
        "replication_status": "failed-replication"
    },
    "Errington_2021_InvestigatingReplicabilityPreclinicalCancer": {
        "discipline": "preclinical-cancer"
    },
    "Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments": {
        "effect_size_z": 1.1
    },
    "Camerer_2018_EvaluatingReplicabilitySocialScience": {
        "discipline": "social-science"
    },
    "Klein_2018_ManyLabs2Investigating": {"preregistered": True},
    "Border_2019_NoSupportHistoricalCandidate": {"candidate_gene_finding": True},
    "Horowitz_2021_EpiPen": {"field_heat": "hot"},
    "Yang_2020_EstimatingDeepReplicabilityScientific": {"statistical_power": 0.4},
    "Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction": {
        "peer_prediction_score": 0.7
    },
    "Dreber_2015_PredictionMarketsEstimateReproducibility": {
        "prediction_market_price": 0.35
    },
    "Altmejd_2019_PredictingReplicabilitySocialScience": {
        "prediction_market_price": 0.65
    },
}


def synthetic_metadata_for_paper(paper: str) -> dict[str, object]:
    return dict(_SYNTHETIC_METADATA[paper])
