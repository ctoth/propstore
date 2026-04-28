"""Tests for ASPIC+ bridge T2.5 — grounded_rules_to_rules (RED).

Chunk 1.7a of the gunray grounding workstream. Pins the contract for
``propstore.aspic_bridge.grounded_rules_to_rules``: a function that
walks every ``RuleDocument`` in a ``GroundedRulesBundle``, enumerates
ground variable substitutions against the fact base drawn from
``sections["definitely"]`` and ``sections["defeasibly"]``, and emits
one ASPIC+ ``Rule`` per valid substitution.

The target function does NOT exist yet — every import of
``propstore.aspic_bridge.grounded_rules_to_rules`` is deferred into
the test body so pytest can *collect* this file cleanly while every
test fails at runtime with ``AttributeError`` (or, for any symbol
that has not yet been introduced elsewhere, ``ImportError``). That is
the RED contract for this chunk.

Target signature per prompts/gunray-chunk-1-7a-bridge-tests.md::

    def grounded_rules_to_rules(
        bundle: GroundedRulesBundle,
        literals: dict[LiteralKey, Literal],
    ) -> tuple[
        frozenset[Rule],            # strict rules
        frozenset[Rule],            # defeasible rules
        dict[LiteralKey, Literal],  # extended literals dict
    ]:
        ...

Non-commitment anchor (CLAUDE.md): the bundle carries the full ground
model with every verdict section present. The bridge reads only from
``definitely`` and ``defeasibly`` because those are the two sections
gunray treats as an answered ground atom; ``not_defeasibly`` is
negation-as-failure territory and ``undecided`` carries no positive
commitment. Phase 1 implements only the positive fact-base path.

Theoretical sources cited throughout the tests:

    Modgil, S. & Prakken, H. (2018). A general account of argumentation
    with preferences. Artificial Intelligence, 248, 51-104.
    - Def 2 (p.8): defeasible rule shape ``antecedents => consequent``
      with a name n(r) used for undercutting attacks.
    - Def 4 (p.9): K = K_n ∪ K_p ordinary/necessary premise split
      (referenced but handled in Chunk 1.8's T4 extension, not here).
    - Def 5 (p.9-10): recursive argument construction.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - §3 (pp.3-4): canonical ``flies(X) -< bird(X)`` example; the
      Herbrand grounding step produces one rule instance per constant
      binding the variable to a fact-base atom.

    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - §3 Definition 7 (p.3): a Datalog fact base is a finite set of
      ground atoms; rules are first-order and must be grounded via
      substitution against that base.
    - §4: the grounded rule instances are a deterministic function of
      the program and its fact base.

    Riveret, R. (2017). A labelling framework for probabilistic
    argumentation.
    - Def 2.2: negation is involutive. The T2.5 bridge must emit
      Literal objects whose ``.contrary.contrary == lit`` — that
      property is asserted end-to-end here.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

if TYPE_CHECKING:
    from argumentation.aspic import Literal, Rule
    from propstore.core.literal_keys import LiteralKey
    from propstore.grounding.bundle import GroundedRulesBundle
    from propstore.families.documents.rules import RuleDocument


# ---------------------------------------------------------------------------
# Construction helpers (all imports deferred — no module-level binding
# of the target name).
# ---------------------------------------------------------------------------


def _var(name: str):
    """Build a variable ``TermDocument``.

    Garcia & Simari 2004 §3 (p.3-4): DeLP variables are uppercase
    identifiers that the Herbrand grounder (§3.1 p.4) binds to
    constants drawn from the fact base.
    """

    from propstore.families.documents.rules import TermDocument

    return TermDocument(kind="var", name=name, value=None)


def _const(value):
    """Build a constant ``TermDocument``.

    Garcia & Simari 2004 §3 (p.3): DeLP constants are drawn from the
    scalar universe; the propstore schema uses ``str | int | float |
    bool`` (cf. ``argumentation.aspic.Scalar``).
    """

    from propstore.families.documents.rules import TermDocument

    return TermDocument(kind="const", name=None, value=value)


def _atom(predicate: str, terms=()):
    """Build an ``AtomDocument`` — ``predicate(t_1, ..., t_n)``.

    Garcia & Simari 2004 §3 (p.3): a DeLP atom is a predicate applied
    to a term tuple (arity ≥ 0). Strong negation is left unset here.
    """

    from propstore.families.documents.rules import AtomDocument

    return AtomDocument(predicate=predicate, terms=tuple(terms), negated=False)


def _rule_doc(rule_id: str, kind: str, head, body=()):
    """Build a ``RuleDocument``.

    Garcia & Simari 2004 §3 (p.3) partitions rule-like objects into
    strict (``<-``), defeasible (``-<``), and defeater rules; this
    helper is polymorphic over ``kind`` because Phase 1 of T2.5
    deliberately rejects ``strict`` and ``defeater`` variants.
    """

    from propstore.families.documents.rules import RuleDocument

    return RuleDocument(
        id=rule_id,
        kind=kind,  # type: ignore[arg-type]
        head=head,
        body=tuple(body),
    )


def _rule_file(rules):
    """Wrap ``RuleDocument`` sequence in a ``LoadedRuleFile``.

    Mirrors the envelope pattern at
    ``propstore/rule_documents.py:LoadedRuleFile.from_loaded_document``.
    Garcia & Simari 2004 §3: a DeLP program's rule component is a flat
    tuple of rules anchored to a source.
    """

    from quire.documents import LoadedDocument
    from propstore.families.documents.rules import RulesFileDocument, RuleSourceDocument
    from propstore.rule_files import LoadedRuleFile

    file_doc = RulesFileDocument(
        source=RuleSourceDocument(paper="test_chunk_1_7a"),
        rules=tuple(rules),
    )
    loaded = LoadedDocument(
        filename="generated.yaml",
        source_path=None,
        knowledge_root=None,
        document=file_doc,
    )
    return LoadedRuleFile.from_loaded_document(loaded)


def _bundle(rules=(), definitely=None, defeasibly=None):
    """Construct a ``GroundedRulesBundle`` with explicit section content.

    Accepts two flat ``{predicate_id: frozenset[tuple[Scalar, ...]]}``
    maps for the ``definitely`` and ``defeasibly`` sections. The other
    two sections (``not_defeasibly`` / ``undecided``) are always
    present-and-empty per the non-commitment discipline anchor in the
    project CLAUDE.md.

    Diller, Borg, Bex 2025 §3 Def 7 (p.3): the fact base inside a
    grounded model is a finite set of ground atoms keyed by predicate
    id — that is the shape the bundle sections carry and the shape
    T2.5 will read to enumerate substitutions.
    """

    from propstore.grounding.bundle import GroundedRulesBundle

    loaded_files: list = []
    if rules:
        loaded_files.append(_rule_file(rules))

    def _freeze(section: Mapping[str, frozenset[tuple]] | None):
        if section is None:
            return MappingProxyType({})
        inner: dict[str, frozenset[tuple]] = {}
        for predicate_id, rows in section.items():
            inner[predicate_id] = frozenset(rows)
        return MappingProxyType(inner)

    sections = MappingProxyType(
        {
            "definitely": _freeze(definitely),
            "defeasibly": _freeze(defeasibly),
            "not_defeasibly": MappingProxyType({}),
            "undecided": MappingProxyType({}),
        }
    )
    return GroundedRulesBundle(
        source_rules=tuple(loaded_files),
        source_facts=(),
        sections=sections,
    )


# ---------------------------------------------------------------------------
# Hypothesis strategies.
# Every strategy body does deferred imports of project modules so
# collection is safe even when target symbols don't yet exist.
# ---------------------------------------------------------------------------


def _empty_bundle() -> st.SearchStrategy:
    """Strategy: a ``GroundedRulesBundle`` with no rules and no facts.

    Diller, Borg, Bex 2025 §3: the empty Datalog program grounds to
    the empty model. T2.5 on this bundle must return
    ``(frozenset(), frozenset(), literals)``.
    """

    return st.builds(lambda _n: _bundle(rules=(), definitely={}, defeasibly={}), st.just(0))


@st.composite
def _single_unary_rule_bundle(draw):
    """Strategy: ``flies(X) -< bird(X)`` with a random set of bird facts.

    Garcia & Simari 2004 §3 (pp.3-4): the textbook defeasible-reasoning
    example — one variable binding a single body atom against a
    non-empty fact base.
    """

    constants = draw(
        st.lists(
            st.sampled_from(["tweety", "opus", "fido", "chirpy"]),
            min_size=0,
            max_size=4,
            unique=True,
        )
    )
    body = (_atom("bird", (_var("X"),)),)
    head = _atom("flies", (_var("X"),))
    rule = _rule_doc("rule:birds-fly", "defeasible", head, body=body)
    facts = {"bird": frozenset((c,) for c in constants)}
    return _bundle(rules=(rule,), definitely=facts, defeasibly={}), constants


# ---------------------------------------------------------------------------
# Enumeration property tests.
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(_empty_bundle())
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_empty_bundle_produces_empty_rule_sets(bundle) -> None:
    """An empty bundle produces empty rule sets.

    Diller, Borg, Bex 2025 §3 (Def 7, p.3): grounding the empty
    program over the empty fact base yields the empty model. T2.5 on
    an empty ``GroundedRulesBundle`` must therefore return empty
    ``frozenset()`` values for both strict and defeasible rules and
    leave the input literals dict unchanged in content.
    """

    from propstore.aspic_bridge import grounded_rules_to_rules

    strict, defeasible, out_literals = grounded_rules_to_rules(bundle, {})
    assert strict == frozenset()
    assert defeasible == frozenset()
    assert out_literals == {}


@pytest.mark.property
@given(_single_unary_rule_bundle())
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_grounded_rules_kind_is_defeasible_in_phase1(payload) -> None:
    """Every emitted rule has ``kind='defeasible'`` in Phase 1.

    Modgil & Prakken 2018, Def 2 (p.8): strict rules and defeasible
    rules are disjoint. Per the prompt, Phase 1 of T2.5 only handles
    the defeasible DeLP form ``-<`` and the strict frozenset is
    always empty on return.
    """

    from propstore.aspic_bridge import grounded_rules_to_rules

    bundle, _constants = payload
    strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    assert strict == frozenset()
    for rule in defeasible:
        assert rule.kind == "defeasible"


@pytest.mark.property
@given(_single_unary_rule_bundle())
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_grounded_rules_names_are_unique(payload) -> None:
    """All emitted ``Rule.name`` values are distinct.

    Modgil & Prakken 2018, Def 2 (p.8): each defeasible rule carries
    a name ``n(r)`` that is the target of undercutting attacks (Def 8c,
    p.11). If two ground instances shared a name, an undercut against
    one would accidentally apply to the other. The grounding layer
    must therefore mint a unique instance name per substitution.
    """

    from propstore.aspic_bridge import grounded_rules_to_rules

    bundle, _constants = payload
    _strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    names = [r.name for r in defeasible]
    assert len(set(names)) == len(names)


@pytest.mark.property
@given(_single_unary_rule_bundle())
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_grounded_rules_head_predicate_matches_schema(payload) -> None:
    """Each Rule's consequent predicate matches the schema's head predicate.

    Garcia & Simari 2004 §3 (p.4): the Herbrand grounding step is a
    pure substitution — it binds variables to constants without
    rewriting the predicate symbol. The head predicate of the ground
    instance is therefore equal to the head predicate of the schema.
    """

    from propstore.aspic_bridge import grounded_rules_to_rules

    bundle, _constants = payload
    _strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    for rule in defeasible:
        assert rule.consequent.atom.predicate == "flies"


@pytest.mark.property
@given(_single_unary_rule_bundle())
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_grounded_rules_antecedents_length_matches_schema_body(payload) -> None:
    """``len(Rule.antecedents)`` equals the schema body length.

    Garcia & Simari 2004 §3 (p.4): substitution preserves arity at
    every position — the body tuple length is an invariant of
    grounding. Diller, Borg, Bex 2025 §3 frames this same invariant
    in Datalog terms: the Datalog rule-instance body is a
    position-preserving substitution of the schema body.
    """

    from propstore.aspic_bridge import grounded_rules_to_rules

    bundle, _constants = payload
    _strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    for rule in defeasible:
        assert len(rule.antecedents) == 1  # body = (bird(X),)


@pytest.mark.property
@given(_single_unary_rule_bundle())
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_literals_dict_extended_not_replaced(payload) -> None:
    """Input literals dict keys survive into the output dict unchanged.

    Modgil & Prakken 2018, Def 1 (p.8): L is a logical language
    closed under contrariness — it may grow, but existing members do
    not vanish. The T2.5 bridge must therefore extend the literals
    dict rather than replace it, so that T1-produced claim-id keys
    remain reachable after grounding.
    """

    from argumentation.aspic import GroundAtom, Literal
    from propstore.aspic_bridge import grounded_rules_to_rules

    bundle, _constants = payload
    from propstore.core.literal_keys import claim_key

    seed_key = claim_key("claim-alpha")
    seed_lit = Literal(atom=GroundAtom("claim-alpha"), negated=False)
    literals_in: dict[LiteralKey, Literal] = {seed_key: seed_lit}
    _strict, _defeasible, out_literals = grounded_rules_to_rules(
        bundle, literals_in
    )
    assert seed_key in out_literals
    assert out_literals[seed_key] == seed_lit


@pytest.mark.property
@given(_single_unary_rule_bundle())
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_grounded_literals_contrary_involution(payload) -> None:
    """Every emitted literal satisfies ``lit.contrary.contrary == lit``.

    Riveret 2017 Def 2.2: negation is involutive. The aspic.py
    ``Literal.contrary`` property encodes that algebraic fact; this
    test pins that the T2.5-constructed literals do in fact satisfy
    it (which they must, because they all flow through the same
    ``Literal`` dataclass).
    """

    from propstore.aspic_bridge import grounded_rules_to_rules

    bundle, _constants = payload
    _strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    for rule in defeasible:
        assert rule.consequent.contrary.contrary == rule.consequent
        for ante in rule.antecedents:
            assert ante.contrary.contrary == ante


# ---------------------------------------------------------------------------
# Concrete example tests.
# ---------------------------------------------------------------------------


def test_delp_birds_fly_tweety_produces_one_rule_instance() -> None:
    """``flies(X) -< bird(X)`` with ``{bird(tweety)}`` → one Rule instance.

    Garcia & Simari 2004 §3 (pp.3-4): the canonical DeLP example.
    Grounding the schema against the single fact ``bird(tweety)``
    produces exactly one substitution ``{X := tweety}`` and therefore
    exactly one defeasible Rule instance whose antecedents are
    ``(bird(tweety),)`` and whose consequent is ``flies(tweety)``.
    """

    from argumentation.aspic import GroundAtom, Literal
    from propstore.aspic_bridge import grounded_rules_to_rules

    rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        definitely={"bird": frozenset([("tweety",)])},
        defeasibly={},
    )
    strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    assert strict == frozenset()
    assert len(defeasible) == 1
    emitted = next(iter(defeasible))
    assert emitted.kind == "defeasible"
    assert emitted.consequent == Literal(
        atom=GroundAtom("flies", ("tweety",)),
        negated=False,
    )
    assert emitted.antecedents == (
        Literal(atom=GroundAtom("bird", ("tweety",)), negated=False),
    )
    assert emitted.name is not None
    assert emitted.name.startswith("rule:birds-fly")


def test_delp_birds_fly_two_birds_produces_two_rule_instances() -> None:
    """Two ``bird`` facts → two distinct defeasible Rule instances.

    Garcia & Simari 2004 §3 (p.4): grounding enumerates every
    substitution that makes the body consistent with the fact base.
    With two birds and a single variable, the enumeration produces
    two rule instances whose Rule.name values are distinct (Modgil &
    Prakken 2018 Def 2, p.8 — unique n(r) per defeasible rule).
    """

    from propstore.aspic_bridge import grounded_rules_to_rules

    rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        definitely={"bird": frozenset([("tweety",), ("opus",)])},
        defeasibly={},
    )
    _strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    assert len(defeasible) == 2
    names = {r.name for r in defeasible}
    assert len(names) == 2
    consequents = {r.consequent.atom.arguments for r in defeasible}
    assert consequents == {("tweety",), ("opus",)}


def test_rule_with_no_matching_fact_produces_zero_instances() -> None:
    """``flies(X) -< bird(X)`` with only ``mammal(fido)`` → zero instances.

    Garcia & Simari 2004 §3 (p.4): a rule instance exists only when
    every body atom can be bound against the fact base. With no
    ``bird/1`` fact the body cannot be satisfied and the enumeration
    yields the empty set.
    """

    from propstore.aspic_bridge import grounded_rules_to_rules

    rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        definitely={"mammal": frozenset([("fido",)])},
        defeasibly={},
    )
    strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    assert strict == frozenset()
    assert defeasible == frozenset()


def test_multi_body_rule_requires_all_atoms_to_ground() -> None:
    """Multi-body rule enumerates only consistent joint substitutions.

    Garcia & Simari 2004 §3 (p.4) and Diller, Borg, Bex 2025 §3:
    grounding a body ``{bird(X), feathered(X)}`` requires that both
    atoms bind to the SAME constant via the same substitution
    (natural-join semantics). With facts
    ``{bird(tweety), feathered(tweety), bird(opus)}`` the join
    produces exactly one instance for tweety and zero for opus.
    """

    from propstore.aspic_bridge import grounded_rules_to_rules

    rule = _rule_doc(
        "rule:feathered-birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(
            _atom("bird", (_var("X"),)),
            _atom("feathered", (_var("X"),)),
        ),
    )
    bundle = _bundle(
        rules=(rule,),
        definitely={
            "bird": frozenset([("tweety",), ("opus",)]),
            "feathered": frozenset([("tweety",)]),
        },
        defeasibly={},
    )
    _strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    assert len(defeasible) == 1
    emitted = next(iter(defeasible))
    assert emitted.consequent.atom.arguments == ("tweety",)
    # body preserves schema arity and position
    assert len(emitted.antecedents) == 2
    body_preds = tuple(a.atom.predicate for a in emitted.antecedents)
    assert body_preds == ("bird", "feathered")
    for ante in emitted.antecedents:
        assert ante.atom.arguments == ("tweety",)


def test_nullary_predicate_rule_produces_one_instance() -> None:
    """``p -< q`` with ``q`` in the fact base → one instance, empty subst.

    Garcia & Simari 2004 §3 (p.3): nullary predicates (arity 0) are
    propositional atoms. With no variables, grounding collapses to a
    single empty-substitution instance. This test pins the 0-variable
    base case so the enumeration loop is not accidentally
    variable-count-dependent.
    """

    from argumentation.aspic import GroundAtom, Literal
    from propstore.aspic_bridge import grounded_rules_to_rules

    rule = _rule_doc(
        "rule:p-from-q",
        "defeasible",
        _atom("p", ()),
        body=(_atom("q", ()),),
    )
    bundle = _bundle(
        rules=(rule,),
        definitely={"q": frozenset([()])},
        defeasibly={},
    )
    _strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    assert len(defeasible) == 1
    emitted = next(iter(defeasible))
    assert emitted.consequent == Literal(atom=GroundAtom("p", ()), negated=False)
    assert emitted.antecedents == (
        Literal(atom=GroundAtom("q", ()), negated=False),
    )


def test_output_literals_include_grounded_atoms() -> None:
    """Returned literals dict contains entries for every grounded atom.

    Modgil & Prakken 2018, Def 1 (p.8): L must contain every literal
    that appears in any rule or attack. The T2.5 bridge therefore
    extends the literals dict with one entry per distinct GroundAtom
    used as an antecedent or consequent in the emitted rules.
    Canonicalisation note (per the prompt): two GroundAtoms that are
    structurally equal map to the same literal dict entry, keyed by
    the bridge's typed structural literal key.
    """

    from argumentation.aspic import GroundAtom
    from propstore.aspic_bridge import grounded_rules_to_rules
    from propstore.core.literal_keys import ground_key

    rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        definitely={"bird": frozenset([("tweety",)])},
        defeasibly={},
    )
    _strict, defeasible, out_literals = grounded_rules_to_rules(bundle, {})
    # Every literal appearing in an emitted rule must be reachable
    # from the returned literals dict by its canonical structured key.
    for rule_obj in defeasible:
        conseq_key = ground_key(rule_obj.consequent.atom, rule_obj.consequent.negated)
        assert conseq_key in out_literals
        assert out_literals[conseq_key].atom == rule_obj.consequent.atom
        for ante in rule_obj.antecedents:
            ante_key = ground_key(ante.atom, ante.negated)
            assert ante_key in out_literals
            assert out_literals[ante_key].atom == ante.atom
    # Sanity: the specific expected atoms are keyed under the canonical
    # structural ground-literal key.
    assert ground_key(GroundAtom("flies", ("tweety",)), False) in out_literals
    assert ground_key(GroundAtom("bird", ("tweety",)), False) in out_literals


def test_existing_claim_literals_preserved() -> None:
    """Pre-existing claim-id literal entries round-trip unchanged.

    Modgil & Prakken 2018, Def 1 (p.8) and Def 4 (p.9): the claim
    literals produced by T1 live in L as nullary atoms. T2.5 extends
    that language with ground-atom entries but must not displace the
    T1-produced claim entries — the downstream T3-T5 stages still
    look them up by claim id.
    """

    from argumentation.aspic import GroundAtom, Literal
    from propstore.aspic_bridge import grounded_rules_to_rules
    from propstore.core.literal_keys import ground_key

    rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        definitely={"bird": frozenset([("tweety",)])},
        defeasibly={},
    )
    from propstore.core.literal_keys import claim_key

    claim_lits: dict[LiteralKey, Literal] = {
        claim_key("claim-1"): Literal(atom=GroundAtom("claim-1"), negated=False),
        claim_key("claim-2"): Literal(atom=GroundAtom("claim-2"), negated=False),
    }
    _strict, _defeasible, out_literals = grounded_rules_to_rules(
        bundle, dict(claim_lits)
    )
    for cid, lit in claim_lits.items():
        assert cid in out_literals
        assert out_literals[cid] == lit
    # And the grounded atoms are added alongside, not in place of.
    assert ground_key(GroundAtom("flies", ("tweety",)), False) in out_literals
    assert ground_key(GroundAtom("bird", ("tweety",)), False) in out_literals


# ---------------------------------------------------------------------------
# Strict and defeater support.
# ---------------------------------------------------------------------------


def test_strict_rule_in_bundle_populates_strict_rules() -> None:
    """A ``kind='strict'`` RuleDocument becomes a strict ASPIC+ rule."""

    from argumentation.aspic import GroundAtom, Literal
    from propstore.aspic_bridge import grounded_rules_to_rules

    rule = _rule_doc(
        "rule:hard-birds-fly",
        "strict",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        definitely={"bird": frozenset([("tweety",)])},
        defeasibly={},
    )
    strict, defeasible, _out = grounded_rules_to_rules(bundle, {})
    assert len(strict) == 1
    emitted = next(iter(strict))
    assert emitted.kind == "strict"
    assert emitted.name is None
    assert emitted.consequent.atom == GroundAtom("flies", ("tweety",))
    assert emitted.antecedents == (
        Literal(atom=GroundAtom("bird", ("tweety",)), negated=False),
    )
    assert defeasible == frozenset()


def test_defeater_rule_in_bundle_emits_undercutter_rule() -> None:
    """A defeater grounds to a negated rule-name literal that undercuts."""

    from argumentation.aspic import GroundAtom, Literal
    from propstore.aspic_bridge import grounded_rules_to_rules
    from propstore.core.literal_keys import ground_key

    defeater_head = _atom("flies", (_var("X"),))
    defeater_head.negated = True
    rule = _rule_doc(
        "rule:penguins-block-flight",
        "defeater",
        defeater_head,
        body=(_atom("penguin", (_var("X"),)),),
    )
    target_rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(target_rule, rule),
        definitely={
            "bird": frozenset([("opus",)]),
            "penguin": frozenset([("opus",)]),
        },
        defeasibly={},
    )
    _strict, defeasible, out = grounded_rules_to_rules(bundle, {})
    emitted = {rule.name: rule for rule in defeasible if rule.name is not None}
    target_name = next(name for name in emitted if name.startswith("rule:birds-fly#"))
    defeater_name = next(name for name in emitted if name.startswith("rule:penguins-block-flight#"))
    assert emitted[target_name].consequent == Literal(
        atom=GroundAtom("flies", ("opus",)),
        negated=False,
    )
    assert emitted[defeater_name].consequent == Literal(
        atom=GroundAtom(target_name),
        negated=True,
    )
    assert out[ground_key(GroundAtom(target_name), True)] == emitted[defeater_name].consequent
