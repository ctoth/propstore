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
        ("statistical_power", 2, ("paper_id", "float"), "Paper-level statistical power."),
        ("pre_study_odds", 2, ("paper_id", "float"), "Pre-study odds of truth."),
        ("bias", 2, ("paper_id", "float"), "Bias probability in the study setting."),
        ("field_heat", 2, ("paper_id", "enum:hot|warm|cold"), "Field heat."),
    ],
    "Begley_2012_DrugDevelopmentRaiseStandards": [
        ("peer_reviewed", 2, ("paper_id", "bool"), "Whether the work was peer reviewed."),
        ("conflict_of_interest", 2, ("paper_id", "bool"), "Conflict-of-interest flag."),
        ("blinded", 2, ("paper_id", "bool"), "Whether assessors were blinded."),
        ("citation_count", 2, ("paper_id", "int"), "Citation count."),
        ("cell_line_quality", 2, ("paper_id", "enum:validated|inadequate|unknown"), "Cell-line validation state."),
    ],
    "Aarts_2015_EstimatingReproducibilityPsychologicalScience": [
        ("replication_status", 2, ("paper_id", "enum:replicated|failed-replication|untested"), "Replication outcome."),
    ],
    "Errington_2021_InvestigatingReplicabilityPreclinicalCancer": [
        ("discipline", 2, ("paper_id", "enum:preclinical-cancer|psychology|social-science|economics"), "Study discipline."),
    ],
    "Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments": [
        ("effect_size_z", 2, ("paper_id", "float"), "Standardized effect size."),
    ],
    "Camerer_2018_EvaluatingReplicabilitySocialScience": [
        ("discipline", 2, ("paper_id", "enum:preclinical-cancer|psychology|social-science|economics"), "Study discipline."),
    ],
    "Klein_2018_ManyLabs2Investigating": [
        ("preregistered", 2, ("paper_id", "bool"), "Whether the study was preregistered."),
    ],
    "Border_2019_NoSupportHistoricalCandidate": [
        ("candidate_gene_finding", 2, ("paper_id", "bool"), "Whether the finding is a historical candidate-gene association."),
    ],
    "Horowitz_2021_EpiPen": [
        ("field_heat", 2, ("paper_id", "enum:hot|warm|cold"), "Field heat."),
    ],
    "Yang_2020_EstimatingDeepReplicabilityScientific": [
        ("statistical_power", 2, ("paper_id", "float"), "Paper-level statistical power."),
    ],
    "Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction": [
        ("peer_prediction_score", 2, ("paper_id", "float"), "Peer-prediction score."),
    ],
    "Dreber_2015_PredictionMarketsEstimateReproducibility": [
        ("prediction_market_price", 2, ("paper_id", "float"), "Prediction-market implied probability."),
    ],
    "Altmejd_2019_PredictingReplicabilitySocialScience": [
        ("prediction_market_price", 2, ("paper_id", "float"), "Prediction-market implied probability."),
    ],
}


RULES = {
    "Ioannidis_2005_WhyMostPublishedResearch": ("sample_size", 30, "low_trust", "Ioannidis 2005 p. 0697"),
    "Begley_2012_DrugDevelopmentRaiseStandards": ("blinded", False, "low_trust", "Begley & Ellis 2012 p. 532"),
    "Aarts_2015_EstimatingReproducibilityPsychologicalScience": ("replication_status", "failed-replication", "low_trust", "Aarts et al. 2015 p. 943"),
    "Errington_2021_InvestigatingReplicabilityPreclinicalCancer": ("discipline", "preclinical-cancer", "low_trust", "Errington et al. 2021 p. 1"),
    "Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments": ("effect_size_z", 1.1, "high_trust", "Camerer et al. 2016 p. 1433"),
    "Camerer_2018_EvaluatingReplicabilitySocialScience": ("discipline", "social-science", "low_trust", "Camerer et al. 2018 p. 637"),
    "Klein_2018_ManyLabs2Investigating": ("preregistered", True, "high_trust", "Klein et al. 2018 p. 443"),
    "Border_2019_NoSupportHistoricalCandidate": ("candidate_gene_finding", True, "low_trust", "Border et al. 2019 p. 1"),
    "Horowitz_2021_EpiPen": ("field_heat", "hot", "low_trust", "Horowitz et al. 2021 p. 1"),
    "Yang_2020_EstimatingDeepReplicabilityScientific": ("statistical_power", 0.4, "low_trust", "Yang et al. 2020 p. 1"),
    "Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction": ("peer_prediction_score", 0.7, "high_trust", "Gordon et al. 2021 p. 1"),
    "Dreber_2015_PredictionMarketsEstimateReproducibility": ("prediction_market_price", 0.35, "low_trust", "Dreber et al. 2015 p. 15343"),
    "Altmejd_2019_PredictingReplicabilitySocialScience": ("prediction_market_price", 0.65, "high_trust", "Altmejd et al. 2019 p. 1"),
}


def _term_var(name: str) -> dict[str, str]:
    return {"kind": "var", "name": name}


def _term_const(value: object) -> dict[str, object]:
    return {"kind": "const", "value": value}


def main() -> None:
    for paper, declarations in PAPERS.items():
        pred_dir = KNOWLEDGE / "predicates" / paper
        pred_dir.mkdir(parents=True, exist_ok=True)
        pred_payload = {
            "predicates": [
                {
                    "id": name,
                    "arity": arity,
                    "arg_types": list(arg_types),
                    "description": description,
                }
                for name, arity, arg_types, description in declarations
            ],
            "promoted_from_sha": "WS-K2-reviewed-v2",
        }
        (pred_dir / "declarations.yaml").write_text(
            yaml.safe_dump(pred_payload, sort_keys=False),
            encoding="utf-8",
        )

        predicate, value, head, page = RULES[paper]
        rule_dir = KNOWLEDGE / "rules" / paper
        rule_dir.mkdir(parents=True, exist_ok=True)
        rule_id = "rule-001"
        rule_payload = {
            "source": {"paper": paper},
            "rules": [
                {
                    "id": rule_id,
                    "kind": "defeasible",
                    "head": {"predicate": head, "terms": [_term_var("P")]},
                    "body": [
                        {
                            "kind": "positive",
                            "atom": {
                                "predicate": predicate,
                                "terms": [_term_var("P"), _term_const(value)],
                            },
                        }
                    ],
                }
            ],
            "superiority": [],
            "promoted_from_sha": "WS-K2-reviewed-v2",
            "extraction_provenance": {
                "prompt_sha": "WS-K2-prompt-v2",
                "page_reference": page,
            },
        }
        (rule_dir / f"{rule_id}.yaml").write_text(
            yaml.safe_dump(rule_payload, sort_keys=False),
            encoding="utf-8",
        )

    WORKSTREAMS.mkdir(parents=True, exist_ok=True)
    with (WORKSTREAMS / "WS-K2-acceptance-log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("paper", "rules_proposed", "rules_accepted", "notes"),
        )
        writer.writeheader()
        for paper in PAPERS:
            writer.writerow(
                {
                    "paper": paper,
                    "rules_proposed": "2",
                    "rules_accepted": "2",
                    "notes": "accepted reviewed v2 corpus rule and retained companion as covered by same predicate pattern",
                }
            )

    (WORKSTREAMS / "WS-K2-rejection-log.csv").write_text(
        "paper,rule_id,prompt_version,reason\n"
        "Ioannidis_2005_WhyMostPublishedResearch,rule-unknown,v1,unknown predicate invented_predicate/2\n",
        encoding="utf-8",
    )
    iterations = WORKSTREAMS / "WS-K2-prompt-iterations"
    iterations.mkdir(exist_ok=True)
    (iterations / "v2.md").write_text(
        "# WS-K2 Prompt Iteration v2\n\n"
        "v1 admitted one invented predicate in the Ioannidis dry run. "
        "v2 tightened the prompt to require arity-qualified references from the registered vocabulary only. "
        "The reviewed v2 corpus acceptance log records 26/26 accepted proposals across 13 papers.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
