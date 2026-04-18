"""Property tests for RuleDocument / RulesFileDocument YAML schema.

These tests describe the contract for the DeLP-style rule document types
that will live in `propstore/rule_documents.py`. The module does not yet
exist — imports are deferred into the test bodies so pytest can collect
this file cleanly while every test fails at run time with ImportError.

Theoretical source:
    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): DeLP language — strict rules L_0 <- L_1,...,L_n,
      defeasible rules L_0 -< L_1,...,L_n, facts, strong negation ~.
    - Section 3.1 (p.4): Ground instances of schematic rules via the
      Herbrand base; variables denoted by uppercase letters.
    - Section 3.3 (p.8): Safety — every variable appearing in the head
      of a rule must also appear in the body so grounding can resolve it.
    - Section 4 (p.16): Proper and blocking defeaters (Defs 4.1, 4.2).

DocumentStruct conventions mirrored from `propstore/artifacts/documents/claims.py`:
    - `msgspec.Struct` with `kw_only=True, forbid_unknown_fields=True`.
    - List-valued fields use `tuple[T, ...] = ()` for immutability.
    - Round-tripping through `msgspec.yaml.{encode,decode}` is idempotent
      under strict decoding.
"""

from __future__ import annotations

import msgspec
import msgspec.yaml
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


# ── Hypothesis strategies ───────────────────────────────────────────
#
# Strategies live in this file per the chunk 1.1a constraint: no
# conftest.py, no shared helper module. Every strategy closes over
# deferred imports so the file parses without `propstore.artifacts.documents.rules`.


_VARIABLE_NAMES = st.sampled_from(["X", "Y", "Z", "W", "U", "V"])
_PREDICATE_NAMES = st.sampled_from(
    ["bird", "flies", "penguin", "chicken", "scared", "nests", "feathered"]
)
_CONST_SCALARS: st.SearchStrategy[str | int | float | bool] = st.one_of(
    st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
            min_size=1, max_size=8),
    st.integers(min_value=-100, max_value=100),
    st.floats(allow_nan=False, allow_infinity=False, width=32),
    st.booleans(),
)


def term_documents() -> st.SearchStrategy:
    """Strategy producing well-formed TermDocument instances.

    DeLP terms (Garcia & Simari 2004 §3, p.3-4) are either variables
    (uppercase identifiers that get ground via the Herbrand base) or
    constants. Constants here are the propstore `Scalar` union:
    ``str | int | float | bool`` (cf. ``argumentation.aspic.Scalar``).
    """
    from propstore.artifacts.documents.rules import TermDocument  # noqa: E402

    var_strategy = _VARIABLE_NAMES.map(
        lambda name: TermDocument(kind="var", name=name)
    )
    const_strategy = _CONST_SCALARS.map(
        lambda value: TermDocument(kind="const", value=value)
    )
    return st.one_of(var_strategy, const_strategy)


def atom_documents(
    *,
    max_arity: int = 4,
    variables: st.SearchStrategy | None = None,
) -> st.SearchStrategy:
    """Strategy producing well-formed AtomDocument instances.

    Atoms in DeLP (Garcia & Simari 2004 §3, p.3) are predicate symbols
    applied to term tuples, optionally prefixed by strong negation ``~``.
    The ``negated`` boolean captures strong negation; the ``terms`` tuple
    carries arity ≥ 0 term documents.
    """
    from propstore.artifacts.documents.rules import AtomDocument, TermDocument  # noqa: E402

    if variables is not None:
        var_term_strategy = variables.map(
            lambda name: TermDocument(kind="var", name=name)
        )
        term_strategy = st.one_of(
            var_term_strategy,
            _CONST_SCALARS.map(
                lambda value: TermDocument(kind="const", value=value)
            ),
        )
    else:
        term_strategy = term_documents()

    return st.builds(
        AtomDocument,
        predicate=_PREDICATE_NAMES,
        terms=st.lists(term_strategy, min_size=0, max_size=max_arity).map(tuple),
        negated=st.booleans(),
    )


def rule_documents(*, max_body_size: int = 3) -> st.SearchStrategy:
    """Strategy producing safe-by-construction RuleDocument instances.

    Garcia & Simari 2004 §3.3 (p.8) safety: every variable appearing in
    the head must also appear somewhere in the body.
    We guarantee this by first drawing a shared variable pool, building
    body atoms over any subset of that pool, then building the head over
    the subset of variables actually used in the body.
    """
    from propstore.artifacts.documents.rules import AtomDocument, RuleDocument, TermDocument  # noqa: E402

    @st.composite
    def _build(draw: st.DrawFn) -> RuleDocument:
        body_variables = draw(
            st.lists(_VARIABLE_NAMES, min_size=1, max_size=4, unique=True)
        )
        body_var_strategy = st.sampled_from(body_variables)
        body = draw(
            st.lists(
                atom_documents(variables=body_var_strategy, max_arity=3),
                min_size=1,
                max_size=max_body_size,
            )
        )
        # Collect the variables actually appearing in the body.
        used: set[str] = set()
        for atom in body:
            for term in atom.terms:
                if term.kind == "var" and term.name is not None:
                    used.add(term.name)

        # Head variables must come from vars ACTUALLY used in the body.
        # If no body atom introduces a variable (all zero-arity or all-const),
        # the head must be ground — no variables available to bind.
        if used:
            head_var_strategy = st.sampled_from(sorted(used))
            head = draw(atom_documents(variables=head_var_strategy, max_arity=3))
        else:
            head = draw(atom_documents(variables=st.nothing(), max_arity=3))

        # Guard: if the drawn head introduced a variable not in the body
        # (it can't — head_var_strategy is constrained), skip. Defensive.
        head_vars = {t.name for t in head.terms if t.kind == "var" and t.name is not None}
        assert head_vars <= used  # strategy guarantees head vars come only from actually-used body vars

        kind = draw(st.sampled_from(["strict", "defeasible", "defeater"]))
        rule_id = draw(
            st.text(
                alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
                min_size=1,
                max_size=10,
            ).map(lambda s: f"rule:{s}")
        )
        return RuleDocument(
            id=rule_id,
            kind=kind,
            head=head,
            body=tuple(body),
        )

    return _build()


def rules_file_documents() -> st.SearchStrategy:
    """Strategy producing well-formed RulesFileDocument envelopes.

    Mirrors the ClaimsFileDocument shape from
    `propstore/artifacts/documents/claims.py`: a source block plus an
    ordered tuple of rule documents.
    """
    from propstore.artifacts.documents.rules import (  # noqa: E402
        RulesFileDocument,
        RuleSourceDocument,
    )

    source_strategy = st.builds(
        RuleSourceDocument,
        paper=st.sampled_from(
            ["Garcia_2004_DefeasibleLogicProgramming", "example/paper", "test/fixture"]
        ),
    )
    return st.builds(
        RulesFileDocument,
        source=source_strategy,
        rules=st.lists(rule_documents(), min_size=0, max_size=4).map(tuple),
    )


# ── Property tests ─────────────────────────────────────────────────


@given(doc=st.deferred(rule_documents))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_rule_document_yaml_round_trip(doc) -> None:
    """Encoding then decoding a RuleDocument must be idempotent.

    Basic round-trip property required by any msgspec document type
    (pattern from `propstore/artifacts/documents/claims.py`). This exercises the
    DeLP language shape end-to-end: kind discriminator, head atom,
    positive body, and default-negation body (Garcia & Simari 2004 §3,
    §6.1 p.29).
    """
    from propstore.artifacts.documents.rules import RuleDocument  # noqa: E402

    encoded = msgspec.yaml.encode(doc)
    decoded = msgspec.yaml.decode(encoded, type=RuleDocument, strict=True)
    assert decoded == doc


@given(doc=st.deferred(rules_file_documents))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_rules_file_document_yaml_round_trip(doc) -> None:
    """Same round-trip property at the file-envelope level.

    The RulesFileDocument envelope parallels ClaimsFileDocument
    (``propstore/artifacts/documents/claims.py``). Round-tripping a whole
    file must be idempotent under strict decoding so authored YAML and
    re-encoded YAML agree structurally.
    """
    from propstore.artifacts.documents.rules import RulesFileDocument  # noqa: E402

    encoded = msgspec.yaml.encode(doc)
    decoded = msgspec.yaml.decode(encoded, type=RulesFileDocument, strict=True)
    assert decoded == doc


@given(doc=st.deferred(rule_documents))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_rule_document_safety_body_covers_head_variables(doc) -> None:
    """DeLP safety invariant (Garcia & Simari 2004 §3.3, p.8).

    Every variable appearing in the head of a rule must also appear
    somewhere in the body, so that grounding via
    the Herbrand base (§3.1, p.4) can resolve it. Rules produced by
    ``rule_documents()`` are safe by construction; this test pins that
    property in place so the strategy or the document type cannot
    regress to unsafe rules silently.
    """
    head_vars = {
        term.name
        for term in doc.head.terms
        if term.kind == "var" and term.name is not None
    }
    body_vars: set[str] = set()
    for atom in doc.body:
        for term in atom.terms:
            if term.kind == "var" and term.name is not None:
                body_vars.add(term.name)
    assert head_vars <= body_vars, (
        f"unsafe rule: head vars {head_vars - body_vars} not bound by body"
    )


def test_rule_document_unknown_kind_rejected() -> None:
    """RuleDocument.kind must be one of {strict, defeasible, defeater}.

    Garcia & Simari 2004 §3 (p.3) distinguishes strict rules (``<-``)
    from defeasible rules (``-<``); §4 (p.16, Defs 4.1 and 4.2) adds
    proper and blocking defeaters as the only other rule-like objects.
    Any other kind string is an authoring error and must be rejected
    by strict msgspec decoding.
    """
    from propstore.artifacts.documents.rules import RuleDocument  # noqa: E402

    invalid_yaml = b"""
id: rule:invalid
kind: maybe
head:
  predicate: flies
  terms:
    - {kind: var, name: X}
  negated: false
body:
  - predicate: bird
    terms:
      - {kind: var, name: X}
    negated: false
"""
    with pytest.raises(msgspec.ValidationError):
        msgspec.yaml.decode(invalid_yaml, type=RuleDocument, strict=True)


def test_rule_document_forbids_unknown_fields() -> None:
    """DocumentStruct forbids unknown fields (strict schema).

    Pattern inherited from ``propstore/document_schema.py`` DocumentStruct
    which sets ``forbid_unknown_fields=True`` on the msgspec base class.
    A rule document carrying a mystery field is an authoring error and
    must be rejected by strict decoding.
    """
    from propstore.artifacts.documents.rules import RuleDocument  # noqa: E402

    yaml_with_extra = b"""
id: rule:birds-fly
kind: defeasible
head:
  predicate: flies
  terms:
    - {kind: var, name: X}
  negated: false
body:
  - predicate: bird
    terms:
      - {kind: var, name: X}
    negated: false
mystery_field: hello
"""
    with pytest.raises(msgspec.ValidationError):
        msgspec.yaml.decode(yaml_with_extra, type=RuleDocument, strict=True)


def test_rule_document_example_delp_birds_fly() -> None:
    """Concrete example: DeLP ``birds typically fly`` defeasible rule.

    Garcia & Simari 2004 uses the birds/penguins example throughout §3
    (p.3-5). This test pins the YAML shape against a concrete parseable
    document so the authored-file surface does not drift.
    """
    from propstore.artifacts.documents.rules import RuleDocument  # noqa: E402

    yaml_text = b"""
id: rule:birds-fly
kind: defeasible
head:
  predicate: flies
  terms:
    - {kind: var, name: X}
  negated: false
body:
  - predicate: bird
    terms:
      - {kind: var, name: X}
    negated: false
"""
    doc = msgspec.yaml.decode(yaml_text, type=RuleDocument, strict=True)
    assert doc.id == "rule:birds-fly"
    assert doc.kind == "defeasible"
    assert doc.head.predicate == "flies"
    assert doc.head.terms[0].kind == "var"
    assert doc.head.terms[0].name == "X"
    assert doc.body[0].predicate == "bird"
    assert doc.body[0].terms[0].name == "X"


def test_rule_document_example_delp_penguin_strict() -> None:
    """Concrete example: DeLP ``penguin -> bird`` strict rule.

    Garcia & Simari 2004 §3 (p.3-4) uses strict rules to encode
    indefeasible taxonomic knowledge — every penguin is a bird. The
    ``kind: strict`` discriminator must parse and the atom shape must
    match the defeasible example above.
    """
    from propstore.artifacts.documents.rules import RuleDocument  # noqa: E402

    yaml_text = b"""
id: rule:penguin-is-bird
kind: strict
head:
  predicate: bird
  terms:
    - {kind: var, name: X}
  negated: false
body:
  - predicate: penguin
    terms:
      - {kind: var, name: X}
    negated: false
"""
    doc = msgspec.yaml.decode(yaml_text, type=RuleDocument, strict=True)
    assert doc.kind == "strict"
    assert doc.head.predicate == "bird"
    assert doc.body[0].predicate == "penguin"


def test_rule_document_example_delp_strong_negation_head() -> None:
    """Concrete example: DeLP defeasible rule with strong negation on head.

    Garcia & Simari 2004 §3 (p.2, p.4) admits strong negation ``~`` on
    heads of both strict and defeasible rules. ``~flies(X) -< penguin(X)``
    is the canonical rebutter to ``flies(X) -< bird(X)`` (Fig around §3).
    ``negated: true`` on the head atom must round-trip cleanly.
    """
    from propstore.artifacts.documents.rules import RuleDocument  # noqa: E402

    yaml_text = b"""
id: rule:penguins-do-not-fly
kind: defeasible
head:
  predicate: flies
  terms:
    - {kind: var, name: X}
  negated: true
body:
  - predicate: penguin
    terms:
      - {kind: var, name: X}
    negated: false
"""
    doc = msgspec.yaml.decode(yaml_text, type=RuleDocument, strict=True)
    assert doc.head.negated is True
    assert doc.head.predicate == "flies"


@given(file_doc=st.deferred(rules_file_documents))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_rules_file_document_preserves_rule_order(file_doc) -> None:
    """Rules in a file preserve their declared order across round-trip.

    Rule order matters for preference construction in structured
    argumentation: Modgil & Prakken 2018 (§Def 13) invokes last-link
    over the last defeasible rule in an argument, so the authored order
    in a rules file can carry implicit preference information that must
    not be scrambled by YAML encoding.
    """
    from propstore.artifacts.documents.rules import RulesFileDocument  # noqa: E402

    encoded = msgspec.yaml.encode(file_doc)
    decoded = msgspec.yaml.decode(encoded, type=RulesFileDocument, strict=True)
    assert tuple(r.id for r in decoded.rules) == tuple(r.id for r in file_doc.rules)


def test_rules_file_document_preserves_authored_superiority() -> None:
    """Authored superiority pairs round-trip at the file-envelope level.

    Garcia & Simari 2004 §3 includes a superiority relation over rules.
    The rule-file surface carries it explicitly as ``[superior, inferior]``
    pairs so priority semantics do not depend on incidental YAML order.
    """
    from propstore.artifacts.documents.rules import (  # noqa: E402
        AtomDocument,
        RuleDocument,
        RulesFileDocument,
        RuleSourceDocument,
    )

    head = AtomDocument(predicate="flies")
    file_doc = RulesFileDocument(
        source=RuleSourceDocument(paper="Garcia_2004_DefeasibleLogicProgramming"),
        rules=(
            RuleDocument(id="r1", kind="defeasible", head=head),
            RuleDocument(id="r2", kind="defeasible", head=head),
        ),
        superiority=(("r2", "r1"),),
    )

    encoded = msgspec.yaml.encode(file_doc)
    decoded = msgspec.yaml.decode(encoded, type=RulesFileDocument, strict=True)

    assert decoded.superiority == (("r2", "r1"),)


def test_rules_file_document_rejects_malformed_superiority_pair() -> None:
    """A superiority entry must be exactly two rule ids."""
    from propstore.artifacts.documents.rules import RulesFileDocument  # noqa: E402

    invalid_yaml = b"""
source:
  paper: Garcia_2004_DefeasibleLogicProgramming
rules: []
superiority:
  - [r2, r1, extra]
"""
    with pytest.raises(msgspec.ValidationError):
        msgspec.yaml.decode(invalid_yaml, type=RulesFileDocument, strict=True)


def test_loaded_rule_file_from_loaded_document() -> None:
    """LoadedRuleFile wraps LoadedDocument[RulesFileDocument].

    Mirrors the typed loaded-document wrapper pattern used by the document
    loaders. Constructing a
    ``LoadedDocument[RulesFileDocument]`` manually and wrapping it via
    ``LoadedRuleFile.from_loaded_document`` must expose:
      - ``filename`` / ``source_path`` / ``knowledge_root`` metadata
        carried over from the underlying LoadedDocument
      - ``.rules`` property returning the underlying tuple unchanged
    """
    from quire.documents import LoadedDocument
    from propstore.artifacts.documents.rules import (  # noqa: E402
        AtomDocument,
        RuleDocument,
        RulesFileDocument,
        RuleSourceDocument,
        TermDocument,
    )
    from propstore.rule_files import LoadedRuleFile

    rule = RuleDocument(
        id="rule:birds-fly",
        kind="defeasible",
        head=AtomDocument(
            predicate="flies",
            terms=(TermDocument(kind="var", name="X"),),
            negated=False,
        ),
        body=(
            AtomDocument(
                predicate="bird",
                terms=(TermDocument(kind="var", name="X"),),
                negated=False,
            ),
        ),
    )
    file_doc = RulesFileDocument(
        source=RuleSourceDocument(paper="Garcia_2004_DefeasibleLogicProgramming"),
        rules=(rule,),
    )
    loaded = LoadedDocument(
        filename="birds",
        source_path=None,
        knowledge_root=None,
        document=file_doc,
    )
    wrapped = LoadedRuleFile.from_loaded_document(loaded)

    assert wrapped.filename == "birds"
    assert wrapped.rules == (rule,)
    assert wrapped.document is file_doc


def test_rule_document_fact_is_strict_rule_with_empty_body() -> None:
    """A fact is a strict rule with an empty body.

    Garcia & Simari 2004 §3 (p.3): "A fact is a strict rule with empty
    body." The document schema must admit ``kind: strict`` together with
    ``body: []`` and round-trip it cleanly.
    """
    from propstore.artifacts.documents.rules import RuleDocument  # noqa: E402

    yaml_text = b"""
id: rule:tweety-is-a-bird
kind: strict
head:
  predicate: bird
  terms:
    - {kind: const, value: tweety}
  negated: false
body: []
"""
    doc = msgspec.yaml.decode(yaml_text, type=RuleDocument, strict=True)
    assert doc.kind == "strict"
    assert doc.body == ()
    assert doc.head.terms[0].kind == "const"
    assert doc.head.terms[0].value == "tweety"
