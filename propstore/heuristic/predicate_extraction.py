"""Predicate proposal extraction for WS-K2."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path


from propstore.families.predicates.declaration import (
    PredicateDeclaration,
    PredicateExtractionProvenance,
    PredicateProposalArtifact,
)
from propstore.families.registry import (
    PROPOSAL_PREDICATE_BRANCH,
    PredicateRef,
)
from propstore.resources import load_package_resource_text


PROMPT_TEMPLATE = load_package_resource_text(
    "propstore.heuristic",
    "predicate_extraction_prompt.txt",
)
PROMPT_SHA = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PredicateProposalResult:
    commit_sha: str | None
    declarations: tuple[PredicateDeclaration, ...]
    relpath: str
    document: PredicateProposalArtifact


def predicate_proposal_branch() -> str:
    branch = PROPOSAL_PREDICATE_BRANCH.fixed_branch
    if branch is None:
        raise ValueError("proposal predicate branch placement must be fixed")
    return branch


def canonical_predicate_ref(predicate_id: str) -> PredicateRef:
    return PredicateRef(predicate_id)


def _paper_notes(source_paper: str) -> str:
    path = Path("papers") / source_paper / "notes.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"# {source_paper}\n"


def _notes_sha(notes: str) -> str:
    return hashlib.sha256(notes.encode("utf-8")).hexdigest()


def _llm_call(**kwargs: object) -> str:
    raise RuntimeError("predicate extraction requires an LLM client or a test fixture")


def _proposal_document(
    *,
    source_paper: str,
    model_name: str,
    notes_sha: str,
    declarations: tuple[PredicateDeclaration, ...],
) -> PredicateProposalArtifact:
    return PredicateProposalArtifact(
        source_paper=source_paper,
        proposed_declarations=declarations,
        extraction_provenance=PredicateExtractionProvenance(
            operations=("predicate_extraction",),
            agent="propstore.heuristic.predicate_extraction",
            model=model_name,
            prompt_sha=PROMPT_SHA,
            notes_sha=notes_sha,
            status="calibrated",
        ),
        extraction_date=str(date.today()),
    )
