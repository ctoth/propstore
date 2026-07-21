"""LLM-seeded predicate proposal extraction (heuristic layer 3).

A heuristic that reads a paper's notes, asks an LLM for the predicate vocabulary
its formal claims range over, and records the result as a
:class:`~propstore.families.predicates.PredicateProposal` on the
``proposal/predicates`` branch. The canonical corpus is never touched — promotion
is the separate, explicit accept-then-promote step owned by
:mod:`propstore.proposals_predicates` (CLAUDE.md layer 3 → layer 1).

Honest ignorance (CLAUDE.md): an extracted declaration is a *stated* assertion of
the model, so the recorded :class:`PredicateExtractionProvenance` carries
``status="stated"`` — never ``measured`` and never a fabricated confidence.

``litellm`` is the optional ``[embeddings]`` extra. This module never imports it
at module load; the real model call lives behind :func:`_llm_call`, which a test
fixture (or a future client) replaces. ``dry_run`` returns the parsed plan
without committing anything.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from propstore.families.predicates import (
    PredicateDeclaration,
    PredicateExtractionProvenance,
    PredicateProposalRef,
)
from propstore.proposals_predicates import predicate_proposal_branch, propose_predicates
from propstore.resources import load_resource_text

if TYPE_CHECKING:
    from propstore.repository import Repository

_AGENT = "propstore.heuristic.predicate_extraction"
PROMPT_TEMPLATE = load_resource_text("heuristic/predicate_extraction_prompt.txt")
PROMPT_SHA = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()


class _PredicateExtractionPayload(msgspec.Struct, forbid_unknown_fields=False):
    """The decode shape of one predicate-extraction LLM response."""

    declarations: tuple[PredicateDeclaration, ...]


@dataclass(frozen=True)
class PredicateProposalResult:
    """The outcome of one predicate-extraction pass.

    ``commit_sha`` is ``None`` for a dry run (and for an empty extraction);
    ``declarations`` is what the model proposed; ``relpath`` is where the proposal
    is (or would be) recorded.
    """

    commit_sha: str | None
    declarations: tuple[PredicateDeclaration, ...]
    relpath: str


def canonical_predicate_ref(predicate_id: str) -> str:
    """Return the canonical predicate identity a declaration would promote to."""

    return predicate_id


def _paper_notes(source_paper: str) -> str:
    path = Path("papers") / source_paper / "notes.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"# {source_paper}\n"


def _notes_sha(notes: str) -> str:
    return hashlib.sha256(notes.encode("utf-8")).hexdigest()


def _llm_call(**_kwargs: object) -> str:
    raise RuntimeError("predicate extraction requires an LLM client or a test fixture")


def _declarations_from_response(raw: str) -> tuple[PredicateDeclaration, ...]:
    try:
        payload = msgspec.json.decode(raw, type=_PredicateExtractionPayload)
    except (msgspec.DecodeError, msgspec.ValidationError) as exc:
        raise ValueError(f"invalid predicate extraction output: {exc}") from exc
    return payload.declarations


def propose_predicates_for_paper(
    repo: Repository,
    *,
    source_paper: str,
    model_name: str,
    prompt_version: str = "v1",
    dry_run: bool = False,
    llm_response: str | None = None,
) -> PredicateProposalResult:
    """Extract candidate predicates for *source_paper* and record the proposal.

    The LLM produces a ``stated`` assertion of the vocabulary; the proposal is
    recorded through the :mod:`propstore.proposals_predicates` owner (the one
    proposal-write path) and never written to the canonical corpus. ``dry_run``
    parses and plans without committing.
    """

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
    declarations = _declarations_from_response(raw)
    relpath = repo.families.proposal_predicates.address(
        PredicateProposalRef(source_paper)
    ).require_path()

    if dry_run:
        return PredicateProposalResult(
            commit_sha=None, declarations=declarations, relpath=relpath
        )

    extraction_provenance = PredicateExtractionProvenance(
        operations=("predicate_extraction",),
        agent=_AGENT,
        model=model_name,
        prompt_sha=PROMPT_SHA,
        notes_sha=_notes_sha(notes),
        status="stated",
    )
    commit_sha = propose_predicates(
        repo,
        source_paper=source_paper,
        declarations=declarations,
        extraction_provenance=extraction_provenance,
        extraction_date=str(date.today()),
    )
    return PredicateProposalResult(
        commit_sha=commit_sha, declarations=declarations, relpath=relpath
    )


__all__ = [
    "PROMPT_SHA",
    "PROMPT_TEMPLATE",
    "PredicateProposalResult",
    "canonical_predicate_ref",
    "predicate_proposal_branch",
    "propose_predicates_for_paper",
]
