"""Materialize a small disk-backed repo that exercises reasoning surfaces."""

from __future__ import annotations

from pathlib import Path

from propstore.artifacts import (
    CLAIMS_FILE_FAMILY,
    CONCEPT_FILE_FAMILY,
    CONTEXT_FAMILY,
    FORM_FAMILY,
    STANCE_FILE_FAMILY,
)
from propstore.artifacts.codecs import render_yaml_value
from propstore.artifacts.identity import (
    normalize_canonical_concept_payload,
    normalize_claim_file_payload,
)
from propstore.artifacts.refs import ClaimsFileRef, ConceptFileRef, ContextRef, StanceFileRef
from propstore.project_init import _seed_form_documents
from propstore.repository import Repository


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
    git = repo.git
    if git is None:
        raise RuntimeError("reasoning demo requires a git-backed repository")

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
                    "context": {"id": "demo"},
                    "provenance": {"paper": "reasoning_demo", "page": 1},
                },
                {
                    "id": "claim_cannot_fly",
                    "type": "parameter",
                    "concept": "flight_score",
                    "value": 0.0,
                    "context": {"id": "demo"},
                    "provenance": {"paper": "reasoning_demo", "page": 1},
                },
                {
                    "id": "claim_override",
                    "type": "observation",
                    "statement": "Independent evidence defeats the non-flight claim.",
                    "concepts": ["tweety"],
                    "context": {"id": "demo"},
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

    with repo.artifacts.transact(message="Seed reasoning demo") as transaction:
        for ref, payload in (
            (ConceptFileRef("bird_class"), bird_class),
            (ConceptFileRef("tweety"), tweety),
            (ConceptFileRef("flight_score"), flight_score),
        ):
            transaction.save(
                CONCEPT_FILE_FAMILY,
                ref,
                transaction.coerce(
                    CONCEPT_FILE_FAMILY,
                    payload,
                    source=CONCEPT_FILE_FAMILY.resolve_ref(repo, ref).relpath,
                ),
            )
        context_ref = ContextRef("demo")
        transaction.save(
            CONTEXT_FAMILY,
            context_ref,
            transaction.coerce(
                CONTEXT_FAMILY,
                {"id": "demo", "name": "Reasoning demo"},
                source=CONTEXT_FAMILY.resolve_ref(repo, context_ref).relpath,
            ),
        )
        claims_ref = ClaimsFileRef("reasoning_demo")
        transaction.save(
            CLAIMS_FILE_FAMILY,
            claims_ref,
            transaction.coerce(
                CLAIMS_FILE_FAMILY,
                claims_payload,
                source=CLAIMS_FILE_FAMILY.resolve_ref(repo, claims_ref).relpath,
            ),
        )
        for payload in (stance_against_yes, stance_against_no):
            stance_ref = StanceFileRef(str(payload["source_claim"]))
            transaction.save(
                STANCE_FILE_FAMILY,
                stance_ref,
                transaction.coerce(
                    STANCE_FILE_FAMILY,
                    payload,
                    source=STANCE_FILE_FAMILY.resolve_ref(repo, stance_ref).relpath,
                ),
            )

    git.commit_files(
        {
            "predicates/reasoning_demo.yaml": render_yaml_value(predicates_payload).encode("utf-8"),
            "rules/reasoning_demo.yaml": render_yaml_value(rules_payload).encode("utf-8"),
        },
        "Seed reasoning demo predicates and rules",
    )
    git.sync_worktree()
    return repo
