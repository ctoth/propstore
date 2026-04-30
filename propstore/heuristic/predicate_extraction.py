"""Predicate proposal extraction for WS-K2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from quire.documents import convert_document_value

from propstore.families.documents.predicates import (
    PredicateDeclaration,
    PredicateExtractionProvenance,
    PredicateProposalDocument,
)
from propstore.families.registry import (
    PROPOSAL_PREDICATE_BRANCH,
    PredicateFileRef,
    PredicateProposalRef,
)
from propstore.repository import Repository


PROMPT_PATH = Path(__file__).with_name("predicate_extraction_prompt.txt")
PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")
PROMPT_SHA = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PredicateProposalResult:
    commit_sha: str | None
    declarations: tuple[PredicateDeclaration, ...]
    relpath: str
    document: PredicateProposalDocument


def predicate_proposal_branch() -> str:
    branch = PROPOSAL_PREDICATE_BRANCH.fixed_branch
    if branch is None:
        raise ValueError("proposal predicate branch placement must be fixed")
    return branch


def canonical_predicate_ref(source_paper: str) -> PredicateFileRef:
    return PredicateFileRef(source_paper)


def _paper_notes(source_paper: str) -> str:
    path = Path("papers") / source_paper / "notes.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"# {source_paper}\n"


def _notes_sha(notes: str) -> str:
    return hashlib.sha256(notes.encode("utf-8")).hexdigest()


def _llm_call(**kwargs: object) -> str:
    raise RuntimeError(
        "predicate extraction requires an LLM client or a test fixture"
    )


def _loads_payload(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, str):
        loaded = json.loads(raw)
    else:
        loaded = raw
    if not isinstance(loaded, dict):
        raise ValueError("predicate extraction output must be a JSON object")
    return loaded


def _declarations_from_payload(payload: dict[str, Any]) -> tuple[PredicateDeclaration, ...]:
    raw_declarations = payload.get("declarations")
    if not isinstance(raw_declarations, list):
        raise ValueError("predicate extraction output requires declarations list")
    declarations: list[PredicateDeclaration] = []
    for index, item in enumerate(raw_declarations, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"predicate declaration {index} must be an object")
        declarations.append(
            convert_document_value(
                item,
                PredicateDeclaration,
                source=f"predicate extraction declaration {index}",
            )
        )
    return tuple(declarations)


def _proposal_document(
    *,
    source_paper: str,
    model_name: str,
    notes_sha: str,
    declarations: tuple[PredicateDeclaration, ...],
) -> PredicateProposalDocument:
    return PredicateProposalDocument(
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


def propose_predicates_for_paper(
    repo: Repository,
    *,
    source_paper: str,
    model_name: str,
    prompt_version: str = "v1",
    dry_run: bool = False,
    llm_response: str | None = None,
) -> PredicateProposalResult:
    notes = _paper_notes(source_paper)
    raw = llm_response
    if raw is None:
        raw = _llm_call(
            model_name=model_name,
            prompt=PROMPT_TEMPLATE,
            prompt_version=prompt_version,
            source_paper=source_paper,
            notes=notes,
        )
    declarations = _declarations_from_payload(_loads_payload(raw))
    document = _proposal_document(
        source_paper=source_paper,
        model_name=model_name,
        notes_sha=_notes_sha(notes),
        declarations=declarations,
    )
    ref = PredicateProposalRef(source_paper)
    relpath = repo.families.proposal_predicates.address(ref).require_path()
    if dry_run:
        return PredicateProposalResult(
            commit_sha=None,
            declarations=declarations,
            relpath=relpath,
            document=document,
        )

    commit_sha: str | None = None
    with repo.families.transact(
        message=f"Record predicate proposals for {source_paper}",
        branch=predicate_proposal_branch(),
    ) as transaction:
        transaction.proposal_predicates.save(ref, document)
        transaction.transaction.commit()
        commit_sha = transaction.commit_sha
    if commit_sha is None:
        raise ValueError("predicate proposal transaction did not produce a commit")
    return PredicateProposalResult(
        commit_sha=commit_sha,
        declarations=declarations,
        relpath=relpath,
        document=document,
    )
