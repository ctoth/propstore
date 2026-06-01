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
