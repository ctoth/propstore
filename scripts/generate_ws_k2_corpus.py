from __future__ import annotations

import csv
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
WORKSTREAMS = ROOT / "reviews" / "2026-04-26-claude" / "workstreams"


PAPERS = {
    "Ioannidis_2005_WhyMostPublishedResearch": [
        ("sample_size", 2, ("paper_id", "int"), "Paper-level sample size."),
        (
            "statistical_power",
            2,
            ("paper_id", "float"),
            "Paper-level statistical power.",
        ),
        ("pre_study_odds", 2, ("paper_id", "float"), "Pre-study odds of truth."),
        ("bias", 2, ("paper_id", "float"), "Bias probability in the study setting."),
        ("field_heat", 2, ("paper_id", "enum:hot|warm|cold"), "Field heat."),
    ],
    "Begley_2012_DrugDevelopmentRaiseStandards": [
        (
            "peer_reviewed",
            2,
            ("paper_id", "bool"),
            "Whether the work was peer reviewed.",
        ),
        ("conflict_of_interest", 2, ("paper_id", "bool"), "Conflict-of-interest flag."),
        ("blinded", 2, ("paper_id", "bool"), "Whether assessors were blinded."),
        ("citation_count", 2, ("paper_id", "int"), "Citation count."),
        (
            "cell_line_quality",
            2,
            ("paper_id", "enum:validated|inadequate|unknown"),
            "Cell-line validation state.",
        ),
    ],
    "Aarts_2015_EstimatingReproducibilityPsychologicalScience": [
        (
            "replication_status",
            2,
            ("paper_id", "enum:replicated|failed-replication|untested"),
            "Replication outcome.",
        ),
    ],
    "Errington_2021_InvestigatingReplicabilityPreclinicalCancer": [
        (
            "discipline",
            2,
            ("paper_id", "enum:preclinical-cancer|psychology|social-science|economics"),
            "Study discipline.",
        ),
    ],
    "Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments": [
        ("effect_size_z", 2, ("paper_id", "float"), "Standardized effect size."),
    ],
    "Camerer_2018_EvaluatingReplicabilitySocialScience": [
        (
            "discipline",
            2,
            ("paper_id", "enum:preclinical-cancer|psychology|social-science|economics"),
            "Study discipline.",
        ),
    ],
    "Klein_2018_ManyLabs2Investigating": [
        (
            "preregistered",
            2,
            ("paper_id", "bool"),
            "Whether the study was preregistered.",
        ),
    ],
    "Border_2019_NoSupportHistoricalCandidate": [
        (
            "candidate_gene_finding",
            2,
            ("paper_id", "bool"),
            "Whether the finding is a historical candidate-gene association.",
        ),
    ],
    "Horowitz_2021_EpiPen": [
        ("field_heat", 2, ("paper_id", "enum:hot|warm|cold"), "Field heat."),
    ],
    "Yang_2020_EstimatingDeepReplicabilityScientific": [
        (
            "statistical_power",
            2,
            ("paper_id", "float"),
            "Paper-level statistical power.",
        ),
    ],
    "Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction": [
        ("peer_prediction_score", 2, ("paper_id", "float"), "Peer-prediction score."),
    ],
    "Dreber_2015_PredictionMarketsEstimateReproducibility": [
        (
            "prediction_market_price",
            2,
            ("paper_id", "float"),
            "Prediction-market implied probability.",
        ),
    ],
    "Altmejd_2019_PredictingReplicabilitySocialScience": [
        (
            "prediction_market_price",
            2,
            ("paper_id", "float"),
            "Prediction-market implied probability.",
        ),
    ],
}


RULES = {
    "Ioannidis_2005_WhyMostPublishedResearch": (
        "sample_size",
        30,
        "low_trust",
        "Ioannidis 2005 p. 0697",
    ),
    "Begley_2012_DrugDevelopmentRaiseStandards": (
        "blinded",
        False,
        "low_trust",
        "Begley & Ellis 2012 p. 532",
    ),
    "Aarts_2015_EstimatingReproducibilityPsychologicalScience": (
        "replication_status",
        "failed-replication",
        "low_trust",
        "Aarts et al. 2015 p. 943",
    ),
    "Errington_2021_InvestigatingReplicabilityPreclinicalCancer": (
        "discipline",
        "preclinical-cancer",
        "low_trust",
        "Errington et al. 2021 p. 1",
    ),
    "Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments": (
        "effect_size_z",
        1.1,
        "high_trust",
        "Camerer et al. 2016 p. 1433",
    ),
    "Camerer_2018_EvaluatingReplicabilitySocialScience": (
        "discipline",
        "social-science",
        "low_trust",
        "Camerer et al. 2018 p. 637",
    ),
    "Klein_2018_ManyLabs2Investigating": (
        "preregistered",
        True,
        "high_trust",
        "Klein et al. 2018 p. 443",
    ),
    "Border_2019_NoSupportHistoricalCandidate": (
        "candidate_gene_finding",
        True,
        "low_trust",
        "Border et al. 2019 p. 1",
    ),
    "Horowitz_2021_EpiPen": (
        "field_heat",
        "hot",
        "low_trust",
        "Horowitz et al. 2021 p. 1",
    ),
    "Yang_2020_EstimatingDeepReplicabilityScientific": (
        "statistical_power",
        0.4,
        "low_trust",
        "Yang et al. 2020 p. 1",
    ),
    "Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction": (
        "peer_prediction_score",
        0.7,
        "high_trust",
        "Gordon et al. 2021 p. 1",
    ),
    "Dreber_2015_PredictionMarketsEstimateReproducibility": (
        "prediction_market_price",
        0.35,
        "low_trust",
        "Dreber et al. 2015 p. 15343",
    ),
    "Altmejd_2019_PredictingReplicabilitySocialScience": (
        "prediction_market_price",
        0.65,
        "high_trust",
        "Altmejd et al. 2019 p. 1",
    ),
}


def _term_var(name: str) -> dict[str, str]:
    return {"kind": "var", "name": name}


def _term_const(value: object) -> dict[str, object]:
    return {"kind": "const", "value": value}


if __name__ == "__main__":
    main()
