"""Rule authoring workflows used by CLI adapters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from quire.documents import convert_document_value, encode_document

from propstore.families.documents.rules import (
    AtomDocument,
    BodyLiteralDocument,
    RuleDocument,
    RuleSourceDocument,
    TermDocument,
)
from propstore.families.registry import RuleRef
from propstore.grounding.predicates import PredicateRegistry
from propstore.repository import Repository


_RULE_KINDS = ("strict", "defeasible", "proper_defeater", "blocking_defeater")


class RuleWorkflowError(Exception):
    """Raised when a rule workflow cannot complete."""


_RULE_MUTATION_LOCK = Lock()


class RuleFileNotFoundError(RuleWorkflowError):
    def __init__(self, file: str) -> None:
        super().__init__(f"Rule file '{file}' not found")
        self.file = file


class RuleNotFoundError(RuleWorkflowError):
    """Raised when a named rule artifact is absent."""

    def __init__(self, rule_id: str) -> None:
        super().__init__(f"Rule '{rule_id}' not found")
        self.rule_id = rule_id


class RuleReferencedError(RuleWorkflowError):
    """Raised when a rule id is still referenced by a superiority artifact."""


class RuleSuperiorityPairNotFoundError(RuleWorkflowError):
    """Raised when a requested superiority artifact is absent."""


@dataclass(frozen=True)
class RuleAddRequest:
    """CLI request to add a rule artifact.

    ``file`` is optional authoring metadata only and never determines the
    canonical storage path.
    """

    file: str | None
    paper: str
    rule_id: str
    kind: str
    head: str
    body: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuleAddReport:
    filepath: Path
    document: RuleDocument
    created: bool


@dataclass(frozen=True)
class RuleRemoveRequest:
    rule_id: str


@dataclass(frozen=True)
class RuleRemoveReport:
    filepath: Path
    rule_id: str
    removed: bool


@dataclass(frozen=True)
class RuleSuperiorityAddRequest:
    file: str | None
    superior_rule_id: str
    inferior_rule_id: str


@dataclass(frozen=True)
class RuleSuperiorityRemoveRequest:
    file: str | None
    superior_rule_id: str
    inferior_rule_id: str


@dataclass(frozen=True)
class RuleSuperiorityReport:
    filepath: Path
    superior_rule_id: str
    inferior_rule_id: str


@dataclass(frozen=True)
class RuleListItem:
    authoring_group: str | None
    rule_id: str
    kind: str
    paper: str | None


@dataclass(frozen=True)
class RuleShowReport:
    filepath: Path
    rendered: str


_ATOM_RE = re.compile(r"^\s*(~)?\s*([A-Za-z_][A-Za-z_0-9]*)\s*(\((.*)\))?\s*$")


def _coerce_term(raw: str) -> TermDocument:
    token = raw.strip()
    if not token:
        raise RuleWorkflowError("empty term in atom")
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        return TermDocument(kind="const", value=token[1:-1])
    if token.lstrip("+-").isdigit():
        return TermDocument(kind="const", value=int(token))
    try:
        if "." in token or "e" in token.lower():
            return TermDocument(kind="const", value=float(token))
    except ValueError:
        pass
    if token[0].isupper():
        return TermDocument(kind="var", name=token)
    return TermDocument(kind="const", value=token)


def parse_atom(raw: str) -> AtomDocument:
    if not isinstance(raw, str) or not raw.strip():
        raise RuleWorkflowError("atom string must be non-empty")
    match = _ATOM_RE.match(raw)
    if match is None:
        raise RuleWorkflowError(f"cannot parse atom: {raw!r}")
    negated_tok, predicate, _parens, inner = match.groups()
    terms: tuple[TermDocument, ...] = ()
    if inner is not None and inner.strip():
        parts = [part for part in (piece.strip() for piece in inner.split(",")) if part]
        terms = tuple(_coerce_term(part) for part in parts)
    return AtomDocument(
        predicate=predicate,
        terms=terms,
        negated=negated_tok is not None,
    )


def parse_body_literal(raw: str) -> BodyLiteralDocument:
    token = raw.strip()
    if token.startswith("not "):
        return BodyLiteralDocument(
            kind="default_negated",
            atom=parse_atom(token[4:].strip()),
        )
    return BodyLiteralDocument(kind="positive", atom=parse_atom(token))


def _term_payload(term: TermDocument) -> dict[str, object]:
    payload: dict[str, object] = {"kind": term.kind}
    if term.name is not None:
        payload["name"] = term.name
    if term.value is not None:
        payload["value"] = term.value
    return payload


def _atom_payload(atom: AtomDocument) -> dict[str, object]:
    payload: dict[str, object] = {"predicate": atom.predicate}
    if atom.terms:
        payload["terms"] = [_term_payload(term) for term in atom.terms]
    if atom.negated:
        payload["negated"] = True
    return payload


def _body_literal_payload(literal: BodyLiteralDocument) -> dict[str, object]:
    return {
        "kind": literal.kind,
        "atom": _atom_payload(literal.atom),
    }


def _rule_document_payload(request: RuleAddRequest) -> dict[str, object]:
    head_atom = parse_atom(request.head)
    body_literals = tuple(parse_body_literal(entry) for entry in request.body)
    data: dict[str, object] = {
        "id": request.rule_id,
        "kind": request.kind,
        "head": _atom_payload(head_atom),
        "body": [_body_literal_payload(literal) for literal in body_literals],
        "source": {"paper": request.paper},
    }
    if request.file:
        data["authoring_group"] = request.file
    return data


def _predicate_registry_at_head(repo: Repository, commit: str | None) -> PredicateRegistry:
    return PredicateRegistry.from_documents(
        tuple(handle.document for handle in repo.families.predicates.iter_handles(commit=commit))
    )


def _rule_atoms(rule: RuleDocument) -> tuple[AtomDocument, ...]:
    return (rule.head,) + tuple(literal.atom for literal in rule.body)


def reject_rule_document_conflicts(
    repo: Repository,
    *,
    commit: str | None,
    target_ref: RuleRef,
    document: RuleDocument,
) -> None:
    if document.id != target_ref.rule_id:
        raise RuleWorkflowError(
            f"rule artifact id {target_ref.rule_id!r} must match document id {document.id!r}"
        )

    existing = repo.families.rules.load(target_ref, commit=commit)
    if existing is not None and existing.promoted_from_sha != document.promoted_from_sha:
        relpath = repo.families.rules.address(target_ref).require_path()
        raise RuleWorkflowError(f"rule {document.id!r} already declared in {relpath}")

    registry = _predicate_registry_at_head(repo, commit)
    for atom in _rule_atoms(document):
        try:
            declaration = registry.lookup(atom.predicate)
        except KeyError as exc:
            raise RuleWorkflowError(
                f"rule {document.id!r} references undeclared predicate {atom.predicate!r}"
            ) from exc
        if declaration.arity != len(atom.terms):
            raise RuleWorkflowError(
                f"rule {document.id!r} references predicate {atom.predicate!r} "
                f"with arity {len(atom.terms)}, declared arity is {declaration.arity}"
            )


def add_rule(
    repo: Repository,
    request: RuleAddRequest,
) -> RuleAddReport:
    """Add a rule as ``rules/<rule-id>.yaml``."""

    if not isinstance(request.rule_id, str) or not request.rule_id:
        raise RuleWorkflowError("rule id must be a non-empty string")
    if request.kind not in _RULE_KINDS:
        raise RuleWorkflowError(
            f"rule kind must be one of {list(_RULE_KINDS)}, got {request.kind!r}"
        )
    if not isinstance(request.paper, str) or not request.paper:
        raise RuleWorkflowError("rule paper slug must be a non-empty string")

    ref = RuleRef(request.rule_id)
    relpath = repo.families.rules.address(ref).require_path()
    filepath = repo.root / relpath

    with _RULE_MUTATION_LOCK, repo.head_bound_transaction(
        repo.snapshot.primary_branch_name(),
        path="rule.add",
    ) as head_txn:
        document = convert_document_value(
            _rule_document_payload(request),
            RuleDocument,
            source=relpath,
        )
        reject_rule_document_conflicts(
            repo,
            commit=head_txn.expected_head,
            target_ref=ref,
            document=document,
        )

        with head_txn.families_transact(
            message=f"Declare rule {request.rule_id}",
        ) as transaction:
            transaction.rules.save(ref, document)

    return RuleAddReport(filepath=filepath, document=document, created=True)


def list_rules(repo: Repository) -> tuple[RuleListItem, ...]:
    items: list[RuleListItem] = []
    for handle in repo.families.rules.iter_handles():
        rule = handle.document
        paper = None if rule.source is None else rule.source.paper
        items.append(
            RuleListItem(
                authoring_group=rule.authoring_group,
                rule_id=rule.id,
                kind=rule.kind,
                paper=paper,
            )
        )
    return tuple(sorted(items, key=lambda item: item.rule_id))


def show_rule(repo: Repository, rule_id: str) -> RuleShowReport:
    ref = RuleRef(rule_id)
    document = repo.families.rules.load(ref)
    if document is None:
        raise RuleNotFoundError(rule_id)
    filepath = repo.root / repo.families.rules.address(ref).require_path()
    return RuleShowReport(
        filepath=filepath,
        rendered=encode_document(document).decode("utf-8"),
    )


def remove_rule(
    repo: Repository,
    request: RuleRemoveRequest,
) -> RuleRemoveReport:
    if not isinstance(request.rule_id, str) or not request.rule_id:
        raise RuleWorkflowError("rule id must be a non-empty string")

    ref = RuleRef(request.rule_id)
    with _RULE_MUTATION_LOCK, repo.mutation_guard():
        existing = repo.families.rules.load(ref)
        if existing is None:
            raise RuleNotFoundError(request.rule_id)

        filepath = repo.root / repo.families.rules.address(ref).require_path()
        repo.families.rules.delete(
            ref,
            message=f"Remove rule {request.rule_id}",
        )

    return RuleRemoveReport(filepath=filepath, rule_id=request.rule_id, removed=True)


def add_rule_superiority(
    repo: Repository,
    request: RuleSuperiorityAddRequest,
) -> RuleSuperiorityReport:
    raise RuleWorkflowError("rule superiority artifacts are not implemented yet")


def remove_rule_superiority(
    repo: Repository,
    request: RuleSuperiorityRemoveRequest,
) -> RuleSuperiorityReport:
    raise RuleWorkflowError("rule superiority artifacts are not implemented yet")
