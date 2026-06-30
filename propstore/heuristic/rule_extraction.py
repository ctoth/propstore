"""LLM-seeded DeLP rule proposal extraction (heuristic layer 3).

A heuristic that reads a paper's notes and its already-declared predicates, asks
an LLM for the DeLP rules the paper's argument structure encodes, and records the
admitted ones as :class:`~propstore.families.rules.RuleProposal` artifacts on the
``proposal/rules`` branch. The canonical corpus is never touched — promotion is
the separate, explicit step owned by :mod:`propstore.proposals_rules`.

A proposed rule that references a predicate not declared for the paper is
*rejected*, not recorded: it carries a vacuous status and is returned as a
:class:`RuleRejection` rather than fabricated into a proposal (CLAUDE.md honest
ignorance). An admitted rule is a *stated* assertion of the model.

``litellm`` is the optional ``[embeddings]`` extra and is never imported here; the
real model call lives behind :func:`_llm_call`, which a test fixture replaces.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

import msgspec

from propstore.families.rules import (
    Atom,
    BodyLiteral,
    ProposedRule,
    RuleExtractionProvenance,
    RuleKind,
    RuleProposal,
    RuleProposalRef,
    Term,
    rule_proposal_branch,
)
from propstore.resources import load_resource_text

if TYPE_CHECKING:
    from propstore.repository import Repository

_AGENT = "propstore.heuristic.rule_extraction"
PROMPT_TEMPLATE = load_resource_text("heuristic/rule_extraction_prompt.txt")
PROMPT_SHA = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()
_ATOM_RE = re.compile(r"^\s*(~)?\s*([A-Za-z_][A-Za-z_0-9]*)\s*(\((.*)\))?\s*$")


class _RuleSpec(msgspec.Struct, forbid_unknown_fields=False):
    """The decode shape of one proposed rule in an LLM response."""

    rule_id: str = ""
    rule_type: str = "defeasible"
    head: str = ""
    body: tuple[str, ...] = ()
    predicates_referenced: tuple[str, ...] = ()
    page_reference: str | None = None


class _RuleExtractionPayload(msgspec.Struct, forbid_unknown_fields=False):
    """The decode shape of a rule-extraction LLM response."""

    rules: tuple[_RuleSpec, ...]


@dataclass(frozen=True)
class RuleRejection:
    """One rule the model proposed that was not admitted as a proposal."""

    rule_id: str
    reason: str
    predicates_referenced: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class RuleProposalResult:
    commit_sha: str | None
    rule_ids: tuple[str, ...]
    relpaths: tuple[str, ...]
    proposals: tuple[RuleProposal, ...]
    rejections: tuple[RuleRejection, ...]


def canonical_rule_ref(_source_paper: str, rule_id: str) -> str:
    """Return the canonical rule identity a proposal would promote to."""

    return rule_id


def _paper_notes(source_paper: str) -> str:
    from pathlib import Path

    path = Path("papers") / source_paper / "notes.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"# {source_paper}\n"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _llm_call(**_kwargs: object) -> str:
    raise RuntimeError("rule extraction requires an LLM client or a test fixture")


def _decode_payload(raw: str) -> _RuleExtractionPayload:
    try:
        return msgspec.json.decode(raw, type=_RuleExtractionPayload)
    except (msgspec.DecodeError, msgspec.ValidationError) as exc:
        raise ValueError(f"invalid rule extraction output: {exc}") from exc


def _coerce_term(raw: str) -> Term:
    token = raw.strip()
    if token.lstrip("+-").isdigit():
        return Term(kind="const", value=int(token))
    try:
        if "." in token or "e" in token.lower():
            return Term(kind="const", value=float(token))
    except ValueError:
        pass
    if token in {"true", "false"}:
        return Term(kind="const", value=token == "true")
    if token and token[0].isupper():
        return Term(kind="var", name=token)
    return Term(kind="const", value=token)


def parse_atom(raw: str) -> Atom:
    """Parse a surface-syntax atom (``pred(Arg, ...)``) into an :class:`Atom`."""

    match = _ATOM_RE.match(raw)
    if match is None:
        raise ValueError(f"cannot parse atom: {raw!r}")
    negated, predicate, _parens, inner = match.groups()
    terms: tuple[Term, ...] = ()
    if inner is not None and inner.strip():
        terms = tuple(_coerce_term(part) for part in inner.split(","))
    return Atom(predicate=predicate, terms=terms, negated=negated is not None)


def _parse_body_literal(raw: str) -> BodyLiteral:
    token = raw.strip()
    if token.startswith("not "):
        return BodyLiteral(kind="default_negated", atom=parse_atom(token[4:].strip()))
    return BodyLiteral(kind="positive", atom=parse_atom(token))


def _rule_kind(raw: object) -> RuleKind:
    value = str(raw)
    if value == "defeater":
        return "proper_defeater"
    if value in ("strict", "defeasible", "proper_defeater", "blocking_defeater"):
        return value
    raise ValueError(f"unknown rule kind {value!r}")


def _registered_predicates(repo: Repository, source_paper: str) -> tuple[set[str], str]:
    predicates = tuple(
        handle.document
        for handle in repo.families.predicate.iter_handles()
        if handle.document.authoring_group == source_paper
    )
    refs = {f"{predicate.predicate_id}/{predicate.arity}" for predicate in predicates}
    payload = msgspec.json.encode(
        [
            {
                "id": predicate.predicate_id,
                "arity": predicate.arity,
                "arg_types": list(predicate.arg_types),
            }
            for predicate in sorted(predicates, key=lambda p: p.predicate_id)
        ]
    )
    return refs, _sha(payload.decode("utf-8"))


def _proposal_from_spec(
    spec: _RuleSpec,
    *,
    source_paper: str,
    model_name: str,
    notes_sha: str,
    predicates_sha: str,
) -> RuleProposal:
    rule = ProposedRule(
        id=spec.rule_id,
        kind=_rule_kind(spec.rule_type),
        head=parse_atom(spec.head),
        body=tuple(_parse_body_literal(literal) for literal in spec.body),
    )
    return RuleProposal(
        rule_id=spec.rule_id,
        source_paper=source_paper,
        proposed_rule=rule,
        predicates_referenced=spec.predicates_referenced,
        extraction_provenance=RuleExtractionProvenance(
            operations=("rule_extraction",),
            agent=_AGENT,
            model=model_name,
            prompt_sha=PROMPT_SHA,
            notes_sha=notes_sha,
            predicates_sha=predicates_sha,
            status="stated",
        ),
        extraction_date=str(date.today()),
        page_reference=spec.page_reference or "",
    )


def propose_rules_for_paper(
    repo: Repository,
    *,
    source_paper: str,
    model_name: str,
    prompt_version: str = "v1",
    dry_run: bool = False,
    llm_response: str | None = None,
) -> RuleProposalResult:
    """Extract candidate rules for *source_paper* and record the admitted ones.

    A rule referencing an undeclared predicate is rejected (vacuous), never
    recorded. Admitted rules are recorded on the ``proposal/rules`` branch and
    never written to the canonical corpus. ``dry_run`` parses and plans without
    committing.
    """

    notes = _paper_notes(source_paper)
    registered, predicates_sha = _registered_predicates(repo, source_paper)
    raw = llm_response
    if raw is None:
        raw = _llm_call(
            model_name=model_name,
            prompt=PROMPT_TEMPLATE,
            prompt_version=prompt_version,
            source_paper=source_paper,
            notes=notes,
            predicates=sorted(registered),
        )
    payload = _decode_payload(raw)

    proposals: list[RuleProposal] = []
    rejections: list[RuleRejection] = []
    notes_sha = _sha(notes)
    for index, spec in enumerate(payload.rules, start=1):
        missing = tuple(ref for ref in spec.predicates_referenced if ref not in registered)
        if missing:
            rejections.append(
                RuleRejection(
                    rule_id=spec.rule_id or f"rule-{index:03d}",
                    reason="rule_extraction_predicate_unknown",
                    predicates_referenced=missing,
                    status="vacuous",
                )
            )
            continue
        proposals.append(
            _proposal_from_spec(
                spec,
                source_paper=source_paper,
                model_name=model_name,
                notes_sha=notes_sha,
                predicates_sha=predicates_sha,
            )
        )

    refs = [RuleProposalRef(source_paper, proposal.rule_id) for proposal in proposals]
    relpaths = tuple(
        repo.families.proposal_rules.address(ref).require_path() for ref in refs
    )
    if dry_run or not proposals:
        return RuleProposalResult(
            commit_sha=None,
            rule_ids=tuple(proposal.rule_id for proposal in proposals),
            relpaths=relpaths,
            proposals=tuple(proposals),
            rejections=tuple(rejections),
        )

    bound = repo.families.transact(
        message=f"Record {len(proposals)} rule proposal(s) for {source_paper}",
        branch=rule_proposal_branch(),
    )
    with bound as transaction:
        for ref, proposal in zip(refs, proposals, strict=True):
            transaction.proposal_rules.save(ref, proposal)
    commit_sha = bound.commit_sha
    if commit_sha is None:
        raise ValueError("rule proposal transaction did not produce a commit")
    return RuleProposalResult(
        commit_sha=commit_sha,
        rule_ids=tuple(proposal.rule_id for proposal in proposals),
        relpaths=relpaths,
        proposals=tuple(proposals),
        rejections=tuple(rejections),
    )


__all__ = [
    "PROMPT_SHA",
    "PROMPT_TEMPLATE",
    "RuleProposalResult",
    "RuleRejection",
    "canonical_rule_ref",
    "parse_atom",
    "propose_rules_for_paper",
    "rule_proposal_branch",
]
