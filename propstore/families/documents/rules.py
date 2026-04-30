"""Typed document models for DeLP-style rule YAML files.

This module hosts the authored-file schema for Defeasible Logic Programming
(DeLP) rules. Rules express strict (``<-``), defeasible (``-<``), proper
defeater, or blocking defeater implications, with strong negation ``~`` on
literals and default negation ``not`` as a distinct body-literal kind.

Theoretical source:
    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.

The document types round-trip through ``msgspec.yaml`` under strict
decoding; they do not enforce DeLP safety at load time — that check is the
authoring CLI's job. The schema only needs to carry safe rules faithfully.
"""

from __future__ import annotations

from typing import Literal

from quire.documents import DocumentStruct


class TermDocument(DocumentStruct):
    """A DeLP term — either a variable or a constant.

    Garcia & Simari 2004 §3 (p.3-4): terms in the DeLP language are
    variables (uppercase identifiers that get ground over the Herbrand
    base, §3.1 p.4) or constants. Constants here use the propstore
    ``Scalar`` union ``str | int | float | bool`` (cf.
    ``argumentation.aspic.Scalar``).

    Attributes:
        kind: ``"var"`` for a variable term, ``"const"`` for a constant.
        name: The variable name when ``kind == "var"``.
        value: The constant scalar when ``kind == "const"``.
    """

    kind: Literal["var", "const"]
    name: str | None = None
    value: str | int | float | bool | None = None


class AtomDocument(DocumentStruct):
    """A DeLP atom — a predicate symbol applied to a tuple of terms.

    Garcia & Simari 2004 §3 (p.3): an atom is ``p(t_1, ..., t_n)`` where
    ``p`` is a predicate symbol and each ``t_i`` is a term. The ``negated``
    flag captures strong negation ``~`` as permitted by the DeLP language
    on both literal heads and literal bodies (Garcia & Simari 2004 §3
    p.2, p.4).

    Attributes:
        predicate: The predicate symbol name.
        terms: The term tuple (arity ≥ 0).
        negated: ``True`` iff this atom carries strong negation ``~``.
    """

    predicate: str
    terms: tuple[TermDocument, ...] = ()
    negated: bool = False


class BodyLiteralDocument(DocumentStruct):
    """A DeLP body literal.

    Garcia & Simari 2004 pp. 125-126 Defs. 6.1-6.3 extends DeLP with
    default negation ``not L``. That is separate from strong negation
    ``~L`` (carried by ``AtomDocument.negated``), so body entries use an
    explicit kind instead of overloading atom polarity.

    Attributes:
        kind: ``"positive"`` for ordinary body literals or
            ``"default_negated"`` for ``not L``.
        atom: The underlying literal atom. Its ``negated`` flag still
            means strong negation.
    """

    kind: Literal["positive", "default_negated"]
    atom: AtomDocument


class RuleDocument(DocumentStruct):
    """A DeLP rule — strict, defeasible, proper defeater, or blocking defeater.

    Garcia & Simari 2004 §3 (p.3) partitions rule-like objects into
    strict rules ``L_0 <- L_1, ..., L_n`` (indefeasible, empty body = a
    fact) and defeasible rules ``L_0 -< L_1, ..., L_n`` (tentative
    conclusions, §3 p.3). Section 4 (p.16, Defs 4.1 and 4.2) further
    recognises proper and blocking defeaters (Defs. 4.1 and 4.2, p. 110);
    this schema keeps those outcomes separate as ``"proper_defeater"`` and
    ``"blocking_defeater"`` instead of the old collapsed ``"defeater"``
    value.

    The language is safe (Garcia & Simari 2004 §3.3 p.8): every variable
    appearing in the head of a rule must also appear somewhere in the
    body (positive or negative) so grounding via the Herbrand base
    (§3.1 p.4) is well-defined. This schema does **not** enforce safety
    at load time — the authoring CLI is responsible for rejecting unsafe
    rules. The document type only needs to round-trip safe rules.

    Attributes:
        id: A stable authoring identifier for the rule.
        kind: ``"strict"``, ``"defeasible"``, ``"proper_defeater"``, or
            ``"blocking_defeater"``.
        head: The head atom (may carry strong negation via ``negated``).
        body: Ordered body literals. Default-negated literals have
            ``BodyLiteralDocument.kind == "default_negated"``.
    """

    id: str
    kind: Literal["strict", "defeasible", "proper_defeater", "blocking_defeater"]
    head: AtomDocument
    body: tuple[BodyLiteralDocument, ...] = ()


class RuleExtractionProvenance(DocumentStruct):
    """Prompt, source, and predicate-vocabulary provenance for a proposed rule."""

    operations: tuple[str, ...]
    agent: str
    model: str
    prompt_sha: str
    notes_sha: str
    predicates_sha: str
    status: str


class RuleProposalDocument(DocumentStruct):
    """Proposal-branch payload for one extracted rule."""

    source_paper: str
    rule_id: str
    proposed_rule: RuleDocument
    predicates_referenced: tuple[str, ...]
    extraction_provenance: RuleExtractionProvenance
    extraction_date: str
    page_reference: str | None = None
    promoted_from_sha: str | None = None


class RuleSourceDocument(DocumentStruct):
    """Provenance block for a rules file.

    Mirrors ``ClaimSourceDocument`` from
    ``propstore.families.claims.documents``
    but scoped to the minimal fields the rule-authoring workflow needs
    today. Garcia & Simari 2004 rules are authored per-paper; the
    ``paper`` field anchors a rules file to the theory source it is
    encoding.

    Attributes:
        paper: The paper directory name (slug) this rules file derives
            its DeLP content from.
    """

    paper: str


class RulesFileDocument(DocumentStruct):
    """Top-level envelope for an authored DeLP rules YAML file.

    Parallels ``ClaimsFileDocument`` from
    ``propstore.families.claims.documents``: a ``source`` block plus an
    ordered tuple of rules. Rule priority is authored explicitly through
    ``superiority`` pairs, oriented ``(superior_rule_id, inferior_rule_id)``
    to match Garcia & Simari's DeLP superiority relation. YAML order stays
    stable for reproducibility, not as an implicit priority channel.

    Attributes:
        source: Provenance block identifying the originating paper.
        rules: Ordered tuple of rule documents.
        superiority: Explicit rule-priority pairs. Each pair is
            ``(superior_rule_id, inferior_rule_id)``.
    """

    source: RuleSourceDocument
    rules: tuple[RuleDocument, ...] = ()
    superiority: tuple[tuple[str, str], ...] = ()
    promoted_from_sha: str | None = None
