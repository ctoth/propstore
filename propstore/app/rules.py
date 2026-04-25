"""Rule authoring workflows used by CLI adapters.

Authors DeLP strict, defeasible, and defeater rules into
``knowledge/rules/<name>.yaml`` files. Uses the existing
``RULE_FILE_FAMILY`` plumbing so rules appear on the primary branch.

Theoretical source:
    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. §3 p.3 partitions rule-like objects into
    strict ``L_0 <- L_1,...,L_n``, defeasible ``L_0 -< L_1,...,L_n``,
    and defeaters; literals may carry strong negation ``~``.

Atom DSL
--------

The CLI accepts atom strings of the form::

    [~]predicate(term1, term2, ...)

- A leading ``~`` marks strong negation on the literal.
- Terms whose first character is uppercase are treated as variables;
  everything else is a constant. Quoted string literals
  (``"foo"``) and numeric literals are coerced to ``str``, ``int``, or
  ``float``.
- Empty parentheses ``()`` and zero-arity atoms ``predicate`` are both
  accepted as nullary.

The DSL is intentionally minimal; paper authors typically want a few
rules per file, so a quoted-literal / variable convention covers the
common case without introducing a lark grammar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from quire.documents import convert_document_value, encode_document

from propstore.families.documents.rules import (
    AtomDocument,
    RuleDocument,
    RuleSourceDocument,
    RulesFileDocument,
    TermDocument,
)
from propstore.families.registry import RuleFileRef
from propstore.repository import Repository


_RULE_KINDS = ("strict", "defeasible", "defeater")


class RuleWorkflowError(Exception):
    """Raised when a rule workflow cannot complete."""


class RuleFileNotFoundError(RuleWorkflowError):
    def __init__(self, file: str) -> None:
        super().__init__(f"Rule file '{file}' not found")
        self.file = file


class RuleNotFoundError(RuleWorkflowError):
    """Raised when a named rule id is absent from a rules file."""

    def __init__(self, file: str, rule_id: str) -> None:
        super().__init__(f"Rule '{rule_id}' not found in rules file '{file}'")
        self.file = file
        self.rule_id = rule_id


class RuleReferencedError(RuleWorkflowError):
    """Raised when a rule id is still referenced by a superiority pair."""

    def __init__(
        self,
        file: str,
        rule_id: str,
        pairs: tuple[tuple[str, str], ...],
    ) -> None:
        rendered = ", ".join(f"({a}, {b})" for a, b in pairs)
        super().__init__(
            f"cannot remove rule '{rule_id}' from '{file}'; still referenced "
            f"in superiority pair(s): {rendered}. Remove the superiority "
            f"pair(s) first."
        )
        self.file = file
        self.rule_id = rule_id
        self.pairs = pairs


@dataclass(frozen=True)
class RuleAddRequest:
    """CLI request to add a rule to ``rules/<file>.yaml``.

    The authored YAML is a ``RulesFileDocument`` envelope with a
    ``source.paper`` block plus a flat tuple of rules. ``superiority``
    is preserved across appends but not mutated by this workflow; use
    the schema directly (or a future ``pks rule superior`` command) to
    declare rule-priority pairs.

    Attributes:
        file: File stem (e.g. ``"ikeda_2014"``) — determines target path
            ``rules/<file>.yaml``.
        paper: Slug of the source paper, written into
            ``source.paper``. When appending to an existing file, the
            request's paper must match the stored paper.
        rule_id: Authoring id for the rule (e.g. ``"r_ikeda_mi"``).
        kind: One of ``"strict"``, ``"defeasible"``, ``"defeater"``.
        head: Atom DSL string for the head literal. A leading ``~`` is
            strong negation.
        body: Ordered tuple of atom DSL strings for the body literals.
    """

    file: str
    paper: str
    rule_id: str
    kind: str
    head: str
    body: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuleAddReport:
    filepath: Path
    document: RulesFileDocument
    created: bool


@dataclass(frozen=True)
class RuleRemoveRequest:
    """CLI request to remove a rule from ``rules/<file>.yaml``.

    Attributes:
        file: File stem (e.g. ``"ikeda_2014"``).
        rule_id: Authoring id of the rule to remove.
    """

    file: str
    rule_id: str


@dataclass(frozen=True)
class RuleRemoveReport:
    filepath: Path
    rule_id: str
    removed: bool


@dataclass(frozen=True)
class RuleListItem:
    file: str
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
    # Quoted string literal.
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        return TermDocument(kind="const", value=token[1:-1])
    # Numeric literals.
    if token.lstrip("+-").isdigit():
        return TermDocument(kind="const", value=int(token))
    try:
        if "." in token or "e" in token.lower():
            return TermDocument(kind="const", value=float(token))
    except ValueError:
        pass
    # Uppercase head -> variable.
    if token[0].isupper():
        return TermDocument(kind="var", name=token)
    return TermDocument(kind="const", value=token)


def parse_atom(raw: str) -> AtomDocument:
    """Parse an atom DSL string into an ``AtomDocument``.

    See module docstring for the accepted syntax.
    """
    if not isinstance(raw, str) or not raw.strip():
        raise RuleWorkflowError("atom string must be non-empty")
    match = _ATOM_RE.match(raw)
    if match is None:
        raise RuleWorkflowError(f"cannot parse atom: {raw!r}")
    negated_tok, predicate, _parens, inner = match.groups()
    if not predicate:
        raise RuleWorkflowError(f"atom missing predicate: {raw!r}")
    terms: tuple[TermDocument, ...] = ()
    if inner is not None and inner.strip():
        # Split on top-level commas. Nested parens or quoted commas are
        # not supported — the DSL is intentionally shallow.
        parts = [part for part in (piece.strip() for piece in inner.split(",")) if part]
        terms = tuple(_coerce_term(part) for part in parts)
    return AtomDocument(
        predicate=predicate,
        terms=terms,
        negated=negated_tok is not None,
    )


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


def _rule_document_payload(request: RuleAddRequest) -> dict[str, object]:
    head_atom = parse_atom(request.head)
    body_atoms = tuple(parse_atom(entry) for entry in request.body)
    return {
        "id": request.rule_id,
        "kind": request.kind,
        "head": _atom_payload(head_atom),
        "body": [_atom_payload(atom) for atom in body_atoms],
    }


def add_rule(
    repo: Repository,
    request: RuleAddRequest,
) -> RuleAddReport:
    """Add a rule to ``rules/<file>.yaml``.

    Creates the file if absent, with ``source.paper = request.paper``.
    When appending to an existing file, the request's paper must match
    the stored paper.
    """
    if not isinstance(request.rule_id, str) or not request.rule_id:
        raise RuleWorkflowError("rule id must be a non-empty string")
    if request.kind not in _RULE_KINDS:
        raise RuleWorkflowError(
            f"rule kind must be one of {list(_RULE_KINDS)}, got {request.kind!r}"
        )
    if not isinstance(request.paper, str) or not request.paper:
        raise RuleWorkflowError("rule paper slug must be a non-empty string")

    ref = RuleFileRef(request.file)
    relpath = repo.families.rules.address(ref).require_path()
    filepath = repo.root / relpath

    existing = repo.families.rules.load(ref)
    entries: list[RuleDocument] = []
    superiority: tuple[tuple[str, str], ...] = ()
    created = True
    source_block = RuleSourceDocument(paper=request.paper)

    if existing is not None:
        created = False
        existing_paper = existing.source.paper if existing.source is not None else None
        if existing_paper != request.paper:
            raise RuleWorkflowError(
                f"rules file {relpath} already exists for paper "
                f"{existing_paper!r}; cannot append under paper {request.paper!r}"
            )
        source_block = existing.source
        superiority = existing.superiority
        for entry in existing.rules:
            if entry.id == request.rule_id:
                raise RuleWorkflowError(
                    f"rule {request.rule_id!r} already declared in {relpath}"
                )
            entries.append(entry)

    new_entry = convert_document_value(
        _rule_document_payload(request),
        RuleDocument,
        source=f"{relpath}:{request.rule_id}",
    )
    entries.append(new_entry)

    document = RulesFileDocument(
        source=source_block,
        rules=tuple(entries),
        superiority=superiority,
    )

    repo.families.rules.save(
        ref,
        document,
        message=(
            f"Add rule {request.rule_id} to {request.file}"
            if not created
            else f"Declare rules for {request.file}"
        ),
    )
    repo.snapshot.sync_worktree()

    return RuleAddReport(
        filepath=filepath,
        document=document,
        created=created,
    )


def list_rules(repo: Repository) -> tuple[RuleListItem, ...]:
    items: list[RuleListItem] = []
    for ref in repo.families.rules.iter():
        document = repo.families.rules.require(ref)
        paper = None if document.source is None else document.source.paper
        for rule in document.rules:
            items.append(
                RuleListItem(
                    file=ref.name,
                    rule_id=rule.id,
                    kind=rule.kind,
                    paper=paper,
                )
            )
    return tuple(items)


def show_rule_file(
    repo: Repository,
    file: str,
) -> RuleShowReport:
    ref = RuleFileRef(file)
    document = repo.families.rules.load(ref)
    if document is None:
        raise RuleFileNotFoundError(file)
    filepath = repo.root / repo.families.rules.address(ref).require_path()
    return RuleShowReport(
        filepath=filepath,
        rendered=encode_document(document).decode("utf-8"),
    )


def remove_rule(
    repo: Repository,
    request: RuleRemoveRequest,
) -> RuleRemoveReport:
    """Remove a rule from ``rules/<file>.yaml``.

    Raises ``RuleFileNotFoundError`` if the file does not exist,
    ``RuleNotFoundError`` if the rule id is absent, or
    ``RuleReferencedError`` if the rule id still participates in a
    ``superiority`` pair. On success the file is rewritten via the
    existing family ``save`` path (same commit pattern as
    ``add_rule``); if the removal leaves zero rules the file is kept
    as a stub so downstream tooling can continue to observe the
    ``source`` block, matching ``remove_context_lifting_rule``'s
    behaviour for emptied lifting-rule blocks.
    """
    if not isinstance(request.rule_id, str) or not request.rule_id:
        raise RuleWorkflowError("rule id must be a non-empty string")

    ref = RuleFileRef(request.file)
    existing = repo.families.rules.load(ref)
    if existing is None:
        raise RuleFileNotFoundError(request.file)

    relpath = repo.families.rules.address(ref).require_path()
    filepath = repo.root / relpath

    if not any(entry.id == request.rule_id for entry in existing.rules):
        raise RuleNotFoundError(request.file, request.rule_id)

    referencing_pairs = tuple(
        pair for pair in existing.superiority if request.rule_id in pair
    )
    if referencing_pairs:
        raise RuleReferencedError(
            request.file, request.rule_id, referencing_pairs
        )

    remaining = tuple(
        entry for entry in existing.rules if entry.id != request.rule_id
    )
    document = RulesFileDocument(
        source=existing.source,
        rules=remaining,
        superiority=existing.superiority,
    )

    repo.families.rules.save(
        ref,
        document,
        message=f"Remove rule {request.rule_id} from {request.file}",
    )
    repo.snapshot.sync_worktree()

    return RuleRemoveReport(
        filepath=filepath,
        rule_id=request.rule_id,
        removed=True,
    )
