"""Materialize a small disk-backed repo that exercises reasoning surfaces."""

from __future__ import annotations

from pathlib import Path

from propstore.artifacts import FORM_FAMILY
from propstore.artifacts.codecs import render_yaml_value
from propstore.artifacts.identity import (
    normalize_canonical_concept_payload,
    normalize_claim_file_payload,
)
from propstore.cli.init import _seed_form_documents
from propstore.repo.repository import Repository


def _initialize_repo(root: Path) -> Repository:
    repo = Repository.init(root)
    form_documents = _seed_form_documents(repo)
    if form_documents:
        with repo.artifacts.transact(message="Seed default forms") as transaction:
            for ref, document in form_documents:
                transaction.save(FORM_FAMILY, ref, document)
        repo.snapshot.sync_worktree()
    return repo


def materialize_reasoning_demo(root: Path) -> Repository:
    """Create a git-backed demo repo that exercises grounding and ASPIC flows."""
    repo = _initialize_repo(root)

    bird_class = normalize_canonical_concept_payload(
        {
            "id": "bird_class",
            "canonical_name": "bird_class",
            "status": "accepted",
            "definition": "Classification concept used to ground bird/1 facts.",
            "form": "structural",
            "domain": "reasoning_demo",
        },
        local_handle="bird_class",
    )
    tweety = normalize_canonical_concept_payload(
        {
            "id": "tweety",
            "canonical_name": "tweety",
            "status": "accepted",
            "definition": "Demo individual used in the grounded Tweety rule.",
            "form": "structural",
            "domain": "reasoning_demo",
            "relationships": [
                {
                    "type": "related",
                    "target": bird_class["artifact_id"],
                    "note": "Marks tweety as a bird-instance for the grounding demo.",
                }
            ],
        },
        local_handle="tweety",
    )
    flight_score = normalize_canonical_concept_payload(
        {
            "id": "flight_score",
            "canonical_name": "flight_score",
            "status": "accepted",
            "definition": "Dimensionless target concept resolved by argumentation.",
            "form": "score",
            "domain": "reasoning_demo",
        },
        local_handle="flight_score",
    )

    claims_payload, claim_map = normalize_claim_file_payload(
        {
            "source": {"paper": "reasoning_demo"},
            "claims": [
                {
                    "id": "claim_can_fly",
                    "type": "parameter",
                    "concept": "flight_score",
                    "value": 1.0,
                    "provenance": {"paper": "reasoning_demo", "page": 1},
                },
                {
                    "id": "claim_cannot_fly",
                    "type": "parameter",
                    "concept": "flight_score",
                    "value": 0.0,
                    "provenance": {"paper": "reasoning_demo", "page": 1},
                },
                {
                    "id": "claim_override",
                    "type": "observation",
                    "statement": "Independent evidence defeats the non-flight claim.",
                    "concepts": ["tweety"],
                    "provenance": {"paper": "reasoning_demo", "page": 1},
                },
            ],
        }
    )

    predicates_payload = {
        "predicates": [
            {
                "id": "bird",
                "arity": 1,
                "arg_types": ["entity"],
                "derived_from": f"concept.relation:related:{bird_class['artifact_id']}",
                "description": "Ground unary fact for bird instances.",
            },
            {
                "id": "flies",
                "arity": 1,
                "arg_types": ["entity"],
                "description": "Defeasible flight conclusion.",
            },
        ]
    }
    rules_payload = {
        "source": {"paper": "reasoning_demo"},
        "rules": [
            {
                "id": "r_flies_from_bird",
                "kind": "defeasible",
                "head": {
                    "predicate": "flies",
                    "terms": [{"kind": "var", "name": "X"}],
                },
                "body": [
                    {
                        "predicate": "bird",
                        "terms": [{"kind": "var", "name": "X"}],
                    }
                ],
            }
        ],
    }
    stance_against_yes = {
        "source_claim": claim_map["claim_cannot_fly"],
        "stances": [
            {
                "target": claim_map["claim_can_fly"],
                "type": "supersedes",
                "note": "Negative assessment overrides the positive one.",
            }
        ],
    }
    stance_against_no = {
        "source_claim": claim_map["claim_override"],
        "stances": [
            {
                "target": claim_map["claim_cannot_fly"],
                "type": "supersedes",
                "note": "External evidence defeats the negative assessment.",
            }
        ],
    }

    repo.git.commit_files(
        {
            "concepts/bird_class.yaml": render_yaml_value(bird_class).encode("utf-8"),
            "concepts/tweety.yaml": render_yaml_value(tweety).encode("utf-8"),
            "concepts/flight_score.yaml": render_yaml_value(flight_score).encode("utf-8"),
            "claims/reasoning_demo.yaml": render_yaml_value(claims_payload).encode("utf-8"),
            "predicates/reasoning_demo.yaml": render_yaml_value(predicates_payload).encode("utf-8"),
            "rules/reasoning_demo.yaml": render_yaml_value(rules_payload).encode("utf-8"),
            "stances/claim_cannot_fly.yaml": render_yaml_value(stance_against_yes).encode("utf-8"),
            "stances/claim_override.yaml": render_yaml_value(stance_against_no).encode("utf-8"),
        },
        "Seed reasoning demo",
    )
    repo.git.sync_worktree()
    return repo
