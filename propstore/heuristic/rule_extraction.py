"""Rule proposal extraction for WS-K2."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


from propstore.families.rules.declaration import (
    AtomDocument,
    AuthoredRuleProposalArtifact,
    BodyLiteralDocument,
    RuleDocument,
    RuleExtractionProvenance,
    TermDocument,
)
from propstore.families.registry import (
    PROPOSAL_RULE_BRANCH,
    RuleRef,
    RuleProposalRef,
)
from propstore.resources import load_package_resource_text
from propstore.repository import Repository


PROMPT_TEMPLATE = load_package_resource_text(
    "propstore.heuristic",
    "rule_extraction_prompt.txt",
)
PROMPT_SHA = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()
_ATOM_RE = re.compile(r"^\s*(~)?\s*([A-Za-z_][A-Za-z_0-9]*)\s*(\((.*)\))?\s*$")


@dataclass(frozen=True)
class RuleRejection:
    rule_id: str
    reason: str
    predicates_referenced: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class RuleProposalResult:
    commit_sha: str | None
    rule_ids: tuple[str, ...]
    relpaths: tuple[str, ...]
    proposals: tuple[AuthoredRuleProposalArtifact, ...]
    rejections: tuple[RuleRejection, ...]


def rule_proposal_branch() -> str:
    branch = PROPOSAL_RULE_BRANCH.fixed_branch
    if branch is None:
        raise ValueError("proposal rule branch placement must be fixed")
    return branch


def canonical_rule_ref(_source_paper: str, rule_id: str) -> RuleRef:
    return RuleRef(rule_id)


def _paper_notes(source_paper: str) -> str:
    path = Path("papers") / source_paper / "notes.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"# {source_paper}\n"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _llm_call(**kwargs: object) -> str:
    raise RuntimeError("rule extraction requires an LLM client or a test fixture")


def _coerce_term(raw: str) -> TermDocument:
    token = raw.strip()
    if token.lstrip("+-").isdigit():
        return TermDocument(kind="const", value=int(token))
    try:
        if "." in token or "e" in token.lower():
            return TermDocument(kind="const", value=float(token))
    except ValueError:
        pass
    if token in {"true", "false"}:
        return TermDocument(kind="const", value=token == "true")
    if token and token[0].isupper():
        return TermDocument(kind="var", name=token)
    return TermDocument(kind="const", value=token)


def _parse_atom(raw: str) -> AtomDocument:
    match = _ATOM_RE.match(raw)
    if match is None:
        raise ValueError(f"cannot parse atom: {raw!r}")
    negated, predicate, _parens, inner = match.groups()
    terms: tuple[TermDocument, ...] = ()
    if inner is not None and inner.strip():
        terms = tuple(_coerce_term(part) for part in inner.split(","))
    return AtomDocument(
        predicate=predicate,
        terms=terms,
        negated=negated is not None,
    )


def _parse_body_literal(raw: str) -> BodyLiteralDocument:
    token = raw.strip()
    if token.startswith("not "):
        return BodyLiteralDocument(
            kind="default_negated",
            atom=_parse_atom(token[4:].strip()),
        )
    return BodyLiteralDocument(kind="positive", atom=_parse_atom(token))


def _rule_kind(raw: object) -> str:
    value = str(raw)
    if value == "defeater":
        return "proper_defeater"
    return value


def _proposal_from_raw(
    raw_rule: dict[str, Any],
    *,
    source_paper: str,
    model_name: str,
    notes_sha: str,
    predicates_sha: str,
) -> AuthoredRuleProposalArtifact:
    rule_id = str(raw_rule["rule_id"])
    body = tuple(_parse_body_literal(str(item)) for item in raw_rule.get("body", ()))
    rule = RuleDocument(
        id=rule_id,
        kind=_rule_kind(raw_rule.get("rule_type", "defeasible")),  # type: ignore[arg-type]
        head=_parse_atom(str(raw_rule["head"])),
        body=body,
    )
    refs = tuple(str(item) for item in raw_rule.get("predicates_referenced", ()))
    return AuthoredRuleProposalArtifact(
        source_paper=source_paper,
        rule_id=rule_id,
        proposed_rule=rule,
        predicates_referenced=refs,
        extraction_provenance=RuleExtractionProvenance(
            operations=("rule_extraction",),
            agent="propstore.heuristic.rule_extraction",
            model=model_name,
            prompt_sha=PROMPT_SHA,
            notes_sha=notes_sha,
            predicates_sha=predicates_sha,
            status="calibrated",
        ),
        extraction_date=str(date.today()),
        page_reference=str(raw_rule.get("page_reference") or ""),
    )
