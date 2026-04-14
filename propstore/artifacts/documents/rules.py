"""Typed document models for DeLP-style rule YAML files.

This module hosts the authored-file schema for Defeasible Logic Programming
(DeLP) rules. Rules express either strict (``<-``) or defeasible (``-<``)
implications, optionally adorned with default negation in the body and
strong negation ``~`` on literal heads.

Theoretical source:
    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.

The document types round-trip through ``msgspec.yaml`` under strict
decoding; they do not enforce DeLP safety at load time — that check is the
authoring CLI's job. The schema only needs to carry safe rules faithfully.
"""

from __future__ import annotations

from typing import Literal

from propstore.artifacts.schema import DocumentStruct


class TermDocument(DocumentStruct):
    """A DeLP term — either a variable or a constant.

    Garcia & Simari 2004 §3 (p.3-4): terms in the DeLP language are
    variables (uppercase identifiers that get ground over the Herbrand
    base, §3.1 p.4) or constants. Constants here use the propstore
    ``Scalar`` union ``str | int | float | bool`` (cf.
    ``propstore.aspic.Scalar``).

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
    p.2, p.4). Default negation lives instead in the rule's separate
    ``negative_body`` channel (§6.1 p.29-31).

    Attributes:
        predicate: The predicate symbol name.
        terms: The term tuple (arity ≥ 0).
        negated: ``True`` iff this atom carries strong negation ``~``.
    """

    predicate: str
    terms: tuple[TermDocument, ...] = ()
    negated: bool = False


class RuleDocument(DocumentStruct):
    """A DeLP rule — strict, defeasible, or defeater.

    Garcia & Simari 2004 §3 (p.3) partitions rule-like objects into
    strict rules ``L_0 <- L_1, ..., L_n`` (indefeasible, empty body = a
    fact) and defeasible rules ``L_0 -< L_1, ..., L_n`` (tentative
    conclusions, §3 p.3). Section 4 (p.16, Defs 4.1 and 4.2) further
    recognises proper and blocking defeaters as the only other rule-like
    constructs in the language; this schema spells that choice out as
    the ``kind: "defeater"`` discriminant value.

    The language is safe (Garcia & Simari 2004 §3.3 p.8): every variable
    appearing in the head of a rule must also appear somewhere in the
    body (positive or negative) so grounding via the Herbrand base
    (§3.1 p.4) is well-defined. This schema does **not** enforce safety
    at load time — the authoring CLI is responsible for rejecting unsafe
    rules. The document type only needs to round-trip safe rules.

    Default negation on bodies (Garcia & Simari 2004 §6.1 p.29-31)
    travels in the separate ``negative_body`` channel so positive and
    default-negated literals remain syntactically distinguishable after
    a YAML round-trip.

    Attributes:
        id: A stable authoring identifier for the rule.
        kind: ``"strict"``, ``"defeasible"``, or ``"defeater"``.
        head: The head atom (may carry strong negation via ``negated``).
        body: Ordered positive-body atoms.
        negative_body: Ordered default-negated body atoms (§6.1).
    """

    id: str
    kind: Literal["strict", "defeasible", "defeater"]
    head: AtomDocument
    body: tuple[AtomDocument, ...] = ()
    negative_body: tuple[AtomDocument, ...] = ()


class RuleSourceDocument(DocumentStruct):
    """Provenance block for a rules file.

    Mirrors ``ClaimSourceDocument`` from ``propstore/claim_documents.py``
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

    Parallels ``ClaimsFileDocument`` (``propstore/claim_documents.py``
    line 333): a ``source`` block plus an ordered tuple of rules. Order
    is preserved across YAML round-trip because authored order can carry
    implicit preference information relevant to structured-argumentation
    last-link comparisons (Modgil & Prakken 2018 Def 13).

    Attributes:
        source: Provenance block identifying the originating paper.
        rules: Ordered tuple of rule documents.
    """

    source: RuleSourceDocument
    rules: tuple[RuleDocument, ...] = ()
