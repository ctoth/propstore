from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st


TARGET_PAPERS = (
    "Ioannidis_2005_WhyMostPublishedResearch",
    "Begley_2012_DrugDevelopmentRaiseStandards",
    "Aarts_2015_EstimatingReproducibilityPsychologicalScience",
    "Errington_2021_InvestigatingReplicabilityPreclinicalCancer",
    "Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments",
    "Camerer_2018_EvaluatingReplicabilitySocialScience",
    "Klein_2018_ManyLabs2Investigating",
    "Border_2019_NoSupportHistoricalCandidate",
    "Horowitz_2021_EpiPen",
    "Yang_2020_EstimatingDeepReplicabilityScientific",
    "Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction",
    "Dreber_2015_PredictionMarketsEstimateReproducibility",
    "Altmejd_2019_PredictingReplicabilitySocialScience",
)


def test_extracted_rule_corpus_lints_clean() -> None:
    from propstore.heuristic.rule_corpus import lint_extracted_rule_corpus

    report = lint_extracted_rule_corpus("knowledge", target_papers=TARGET_PAPERS)

    assert report.errors == ()
    assert set(report.papers_checked) == set(TARGET_PAPERS)
    assert report.rules_checked >= len(TARGET_PAPERS)


@pytest.mark.property
@given(
    name=st.from_regex(r"[a-z_][a-z0-9_]{0,20}", fullmatch=True),
    arity=st.integers(min_value=1, max_value=5),
)
def test_generated_unknown_predicate_reference_fails_lint(name: str, arity: int) -> None:
    from propstore.heuristic.rule_corpus import validate_rule_predicate_refs

    unknown_ref = f"{name}/{arity}"
    if unknown_ref == "sample_size/2":
        unknown_ref = "sample_size/3"

    errors = validate_rule_predicate_refs(
        predicates={"sample_size/2"},
        referenced={unknown_ref},
        rule_id="generated-rule",
    )

    assert errors
    assert unknown_ref in errors[0]


@pytest.mark.property
@given(
    head_var=st.sampled_from(["P", "X", "Study"]),
    body_var=st.sampled_from(["P", "X", "Study"]),
)
def test_generated_rule_variable_safety_requires_head_var_in_positive_body(
    head_var: str,
    body_var: str,
) -> None:
    from propstore.heuristic.rule_corpus import validate_variable_safety

    errors = validate_variable_safety(
        head_terms=(head_var,),
        positive_body_terms=(body_var,),
        rule_id="generated-rule",
    )

    assert bool(errors) is (head_var != body_var)
