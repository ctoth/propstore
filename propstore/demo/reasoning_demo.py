"""Materialize a small disk-backed repo that exercises reasoning surfaces."""

from __future__ import annotations

from pathlib import Path

from propstore.families.identity.claims import normalize_claim_file_payload
from propstore.families.identity.concepts import (
    normalize_canonical_concept_payload,
)
from propstore.families.identity.stances import stamp_stance_artifact_id
from propstore.families.registry import (
    ClaimRef,
    ConceptFileRef,
    ContextRef,
    PredicateRef,
    RuleRef,
    StanceRef,
)
from propstore.app.project_init import _seed_form_documents
from propstore.repository import Repository


def _initialize_repo(root: Path) -> Repository:
    repo = Repository.init(root)
    form_documents = _seed_form_documents(repo)
    if form_documents:
        with repo.families.transact(message="Seed default forms") as transaction:
            for ref, document in form_documents:
                transaction.forms.save(ref, document)
        repo.require_git().sync_worktree()
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
                    "output_concept": flight_score["artifact_id"],
                    "value": 1.0,
                    "context": {"id": "demo"},
                    "provenance": {"paper": "reasoning_demo", "page": 1},
                },
                {
                    "id": "claim_cannot_fly",
                    "type": "parameter",
                    "output_concept": flight_score["artifact_id"],
                    "value": 0.0,
                    "context": {"id": "demo"},
                    "provenance": {"paper": "reasoning_demo", "page": 1},
                },
                {
                    "id": "claim_override",
                    "type": "observation",
                    "statement": "Independent evidence defeats the non-flight claim.",
                    "concepts": [tweety["artifact_id"]],
                    "context": {"id": "demo"},
                    "provenance": {"paper": "reasoning_demo", "page": 1},
                },
            ],
        }
    )

    predicate_payloads = (
        {
            "id": "bird",
            "arity": 1,
            "arg_types": ["entity"],
            "derived_from": f"concept.relation:related:{bird_class['artifact_id']}",
            "description": "Ground unary fact for bird instances.",
            "authoring_group": "reasoning_demo",
        },
        {
            "id": "flies",
            "arity": 1,
            "arg_types": ["entity"],
            "description": "Defeasible flight conclusion.",
            "authoring_group": "reasoning_demo",
        },
    )
    rule_payload = {
        "id": "r_flies_from_bird",
        "kind": "defeasible",
        "head": {
            "predicate": "flies",
            "terms": [{"kind": "var", "name": "X"}],
        },
        "body": [
            {
                "kind": "positive",
                "atom": {
                    "predicate": "bird",
                    "terms": [{"kind": "var", "name": "X"}],
                },
            }
        ],
        "source": {"paper": "reasoning_demo"},
        "authoring_group": "reasoning_demo",
    }
    stance_against_yes = stamp_stance_artifact_id({
        "source_claim": claim_map["claim_cannot_fly"],
        "target": claim_map["claim_can_fly"],
        "type": "supersedes",
        "note": "Negative assessment overrides the positive one.",
    })
    stance_against_no = stamp_stance_artifact_id({
        "source_claim": claim_map["claim_override"],
        "target": claim_map["claim_cannot_fly"],
        "type": "supersedes",
        "note": "External evidence defeats the negative assessment.",
    })

    with repo.families.transact(message="Seed reasoning demo") as transaction:
        for ref, payload in (
            (ConceptFileRef("bird_class"), bird_class),
            (ConceptFileRef("tweety"), tweety),
            (ConceptFileRef("flight_score"), flight_score),
        ):
            transaction.concepts.save(
                ref,
                transaction.concepts.coerce(
                    payload,
                    source=repo.families.concepts.address(ref).require_path(),
                ),
            )
        context_ref = ContextRef("demo")
        transaction.contexts.save(
            context_ref,
            transaction.contexts.coerce(
                {"id": "demo", "name": "Reasoning demo"},
                source=repo.families.contexts.address(context_ref).require_path(),
            ),
        )
        source_payload = claims_payload["source"]
        for claim_payload in claims_payload["claims"]:
            claim_payload.setdefault("source", source_payload)
            claims_ref = ClaimRef(str(claim_payload["artifact_id"]))
            transaction.claims.save(
                claims_ref,
                transaction.claims.coerce(
                    claim_payload,
                    source=repo.families.claims.address(claims_ref).require_path(),
                ),
            )
        for payload in (stance_against_yes, stance_against_no):
            stance_ref = StanceRef(str(payload["artifact_code"]))
            transaction.stances.save(
                stance_ref,
                transaction.stances.coerce(
                    payload,
                    source=repo.families.stances.address(stance_ref).require_path(),
                ),
            )
        for predicate_payload in predicate_payloads:
            predicates_ref = PredicateRef(str(predicate_payload["id"]))
            transaction.predicates.save(
                predicates_ref,
                transaction.predicates.coerce(
                    predicate_payload,
                    source=repo.families.predicates.address(predicates_ref).require_path(),
                ),
            )
        rules_ref = RuleRef("r_flies_from_bird")
        transaction.rules.save(
            rules_ref,
            transaction.rules.coerce(
                rule_payload,
                source=repo.families.rules.address(rules_ref).require_path(),
            ),
        )
    git.sync_worktree()
    return repo
