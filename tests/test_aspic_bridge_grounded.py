"""Tests for ASPIC+ bridge T2.5 — project_grounded_rules.

Chunk 1.7a of the gunray grounding workstream. Pins the contract for
``propstore.aspic_bridge.project_grounded_rules``: a function that
walks every ``RuleDocument`` in a ``GroundedRulesBundle``, enumerates
ground variable substitutions against the fact base drawn from
``sections["definitely"]`` and ``sections["defeasibly"]``, and emits
one ASPIC+ ``Rule`` per valid substitution.

The target function does NOT exist yet — every import of
``propstore.aspic_bridge.project_grounded_rules`` is deferred into
the test body so pytest can *collect* this file cleanly while every
test fails at runtime with ``AttributeError`` (or, for any symbol
that has not yet been introduced elsewhere, ``ImportError``). That is
the RED contract for this chunk.

Target signature per prompts/gunray-chunk-1-7a-bridge-tests.md::

    def project_grounded_rules(
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
``yes`` because that is the Garcia section gunray treats as positively
warranted; ``no`` carries warranted complements, ``undecided`` carries
blocked literals, and ``unknown`` carries no argument. Phase 1 implements
only the positive fact-base path.

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
    from propstore.families.documents.rules import BodyLiteralDocument, RuleDocument


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

    from propstore.families.documents.rules import BodyLiteralDocument, RuleDocument

    return RuleDocument(
        id=rule_id,
        kind=kind,  # type: ignore[arg-type]
        head=head,
        body=tuple(
            BodyLiteralDocument(kind="positive", atom=atom)
            for atom in body
        ),
    )


def _bundle(rules=(), yes=None):
    """Construct a ``GroundedRulesBundle`` with explicit section content.

    Accepts a flat ``{predicate_id: frozenset[tuple[Scalar, ...]]}``
    map for the ``yes`` section. The other Garcia sections (``no`` /
    ``undecided`` / ``unknown``) are always present-and-empty per the
    non-commitment discipline anchor in the project CLAUDE.md.

    Diller, Borg, Bex 2025 §3 Def 7 (p.3): the fact base inside a
    grounded model is a finite set of ground atoms keyed by predicate
    id — that is the shape the bundle sections carry and the shape
    T2.5 will read to enumerate substitutions.
    """

    from propstore.grounding.bundle import GroundedRulesBundle

    def _freeze(section: Mapping[str, frozenset[tuple]] | None):
        if section is None:
            return MappingProxyType({})
        inner: dict[str, frozenset[tuple]] = {}
        for predicate_id, rows in section.items():
            inner[predicate_id] = frozenset(rows)
        return MappingProxyType(inner)

    sections = MappingProxyType(
        {
            "yes": _freeze(yes),
            "no": MappingProxyType({}),
            "undecided": MappingProxyType({}),
            "unknown": MappingProxyType({}),
        }
    )
    from argumentation.aspic import GroundAtom

    source_facts = tuple(
        GroundAtom(predicate, tuple(row))
        for predicate, rows in (yes or {}).items()
        for row in rows
    )

    from propstore.grounding.grounder import ground
    from propstore.grounding.predicates import PredicateRegistry

    return ground(
        tuple(rules),
        source_facts,
        PredicateRegistry(()),
        return_arguments=True,
    )


def _project(bundle, literals=None):
    from propstore.aspic_bridge import project_grounded_rules

    return project_grounded_rules(bundle, {} if literals is None else literals)


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

    return st.builds(lambda _n: _bundle(rules=(), yes={}), st.just(0))


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
    return _bundle(rules=(rule,), yes=facts), constants


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

    projection = _project(bundle)
    assert projection.strict_rules == frozenset()
    assert projection.defeasible_rules == frozenset()
    assert projection.literals == {}


def test_project_grounded_rules_exposes_structured_origins() -> None:
    body = (_atom("bird", (_var("X"),)),)
    head = _atom("flies", (_var("X"),))
    rule = _rule_doc("rule:birds-fly", "defeasible", head, body=body)
    bundle = _bundle(rules=(rule,), yes={"bird": frozenset({("tweety",)})})

    projection = _project(bundle)
    (ground_rule,) = tuple(projection.defeasible_rules)
    origin = projection.origins[ground_rule]

    assert ground_rule.name == "gr0"
    assert "#" not in ground_rule.name
    assert "rule:birds-fly" not in ground_rule.name
    assert origin.source_rule_id == "rule:birds-fly"
    assert origin.substitution == (("X", "tweety"),)
    assert origin.role == "ground"


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

    bundle, _constants = payload
    projection = _project(bundle)
    assert projection.strict_rules == frozenset()
    for rule in projection.defeasible_rules:
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

    bundle, _constants = payload
    projection = _project(bundle)
    names = [r.name for r in projection.defeasible_rules]
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

    bundle, _constants = payload
    projection = _project(bundle)
    for rule in projection.defeasible_rules:
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

    bundle, _constants = payload
    projection = _project(bundle)
    for rule in projection.defeasible_rules:
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

    bundle, _constants = payload
    from propstore.core.literal_keys import claim_key

    seed_key = claim_key("claim-alpha")
    seed_lit = Literal(atom=GroundAtom("claim-alpha"), negated=False)
    literals_in: dict[LiteralKey, Literal] = {seed_key: seed_lit}
    out_literals = _project(bundle, literals_in).literals
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

    bundle, _constants = payload
    projection = _project(bundle)
    for rule in projection.defeasible_rules:
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

    rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        yes={"bird": frozenset([("tweety",)])},
    )
    projection = _project(bundle)
    assert projection.strict_rules == frozenset()
    assert len(projection.defeasible_rules) == 1
    emitted = next(iter(projection.defeasible_rules))
    assert emitted.kind == "defeasible"
    assert emitted.consequent == Literal(
        atom=GroundAtom("flies", ("tweety",)),
        negated=False,
    )
    assert emitted.antecedents == (
        Literal(atom=GroundAtom("bird", ("tweety",)), negated=False),
    )
    assert emitted.name is not None
    assert emitted.name.startswith("gr")
    assert projection.origins[emitted].source_rule_id == "rule:birds-fly"


def test_delp_birds_fly_two_birds_produces_two_rule_instances() -> None:
    """Two ``bird`` facts → two distinct defeasible Rule instances.

    Garcia & Simari 2004 §3 (p.4): grounding enumerates every
    substitution that makes the body consistent with the fact base.
    With two birds and a single variable, the enumeration produces
    two rule instances whose Rule.name values are distinct (Modgil &
    Prakken 2018 Def 2, p.8 — unique n(r) per defeasible rule).
    """

    rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        yes={"bird": frozenset([("tweety",), ("opus",)])},
    )
    projection = _project(bundle)
    assert len(projection.defeasible_rules) == 2
    names = {r.name for r in projection.defeasible_rules}
    assert len(names) == 2
    consequents = {r.consequent.atom.arguments for r in projection.defeasible_rules}
    assert consequents == {("tweety",), ("opus",)}


def test_rule_with_no_matching_fact_produces_zero_instances() -> None:
    """``flies(X) -< bird(X)`` with only ``mammal(fido)`` → zero instances.

    Garcia & Simari 2004 §3 (p.4): a rule instance exists only when
    every body atom can be bound against the fact base. With no
    ``bird/1`` fact the body cannot be satisfied and the enumeration
    yields the empty set.
    """

    rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        yes={"mammal": frozenset([("fido",)])},
    )
    projection = _project(bundle)
    assert projection.strict_rules == frozenset()
    assert projection.defeasible_rules == frozenset()


def test_multi_body_rule_requires_all_atoms_to_ground() -> None:
    """Multi-body rule enumerates only consistent joint substitutions.

    Garcia & Simari 2004 §3 (p.4) and Diller, Borg, Bex 2025 §3:
    grounding a body ``{bird(X), feathered(X)}`` requires that both
    atoms bind to the SAME constant via the same substitution
    (natural-join semantics). With facts
    ``{bird(tweety), feathered(tweety), bird(opus)}`` the join
    produces exactly one instance for tweety and zero for opus.
    """

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
        yes={
            "bird": frozenset([("tweety",), ("opus",)]),
            "feathered": frozenset([("tweety",)]),
        },
    )
    projection = _project(bundle)
    assert len(projection.defeasible_rules) == 1
    emitted = next(iter(projection.defeasible_rules))
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

    rule = _rule_doc(
        "rule:p-from-q",
        "defeasible",
        _atom("p", ()),
        body=(_atom("q", ()),),
    )
    bundle = _bundle(
        rules=(rule,),
        yes={"q": frozenset([()])},
    )
    projection = _project(bundle)
    assert len(projection.defeasible_rules) == 1
    emitted = next(iter(projection.defeasible_rules))
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
    from propstore.core.literal_keys import ground_key

    rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        yes={"bird": frozenset([("tweety",)])},
    )
    projection = _project(bundle)
    defeasible = projection.defeasible_rules
    out_literals = projection.literals
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
    from propstore.core.literal_keys import ground_key

    rule = _rule_doc(
        "rule:birds-fly",
        "defeasible",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        yes={"bird": frozenset([("tweety",)])},
    )
    from propstore.core.literal_keys import claim_key

    claim_lits: dict[LiteralKey, Literal] = {
        claim_key("claim-1"): Literal(atom=GroundAtom("claim-1"), negated=False),
        claim_key("claim-2"): Literal(atom=GroundAtom("claim-2"), negated=False),
    }
    out_literals = _project(bundle, dict(claim_lits)).literals
    for cid, lit in claim_lits.items():
        assert cid in out_literals
        assert out_literals[cid] == lit
    # And the grounded atoms are added alongside, not in place of.
    assert ground_key(GroundAtom("flies", ("tweety",)), False) in out_literals
    assert ground_key(GroundAtom("bird", ("tweety",)), False) in out_literals


# ---------------------------------------------------------------------------
# Strict and defeater support.
# ---------------------------------------------------------------------------


def test_strict_rule_in_bundle_resolves_to_axiom() -> None:
    """A fact-only strict RuleDocument is simplified into the axiom base."""

    from argumentation.aspic import GroundAtom, Literal
    from propstore.aspic_bridge.grounding import _ground_facts_to_axioms

    rule = _rule_doc(
        "rule:hard-birds-fly",
        "strict",
        _atom("flies", (_var("X"),)),
        body=(_atom("bird", (_var("X"),)),),
    )
    bundle = _bundle(
        rules=(rule,),
        yes={"bird": frozenset([("tweety",)])},
    )
    projection = _project(bundle)
    assert projection.strict_rules == frozenset()
    assert projection.defeasible_rules == frozenset()
    from argumentation.aspic import KnowledgeBase
    from propstore.grounding.gunray_complement import GUNRAY_COMPLEMENT_ENCODER

    kb = _ground_facts_to_axioms(
        bundle,
        {},
        KnowledgeBase(axioms=frozenset(), premises=frozenset()),
        complement_encoder=GUNRAY_COMPLEMENT_ENCODER,
    )
    assert Literal(GroundAtom("flies", ("tweety",))) in kb.axioms


def test_defeater_rule_in_bundle_emits_undercutter_rule() -> None:
    """A defeater grounds to a negated rule-name literal that undercuts."""

    from argumentation.aspic import GroundAtom, Literal
    from propstore.core.literal_keys import ground_key

    defeater_head = _atom("flies", (_var("X"),))
    defeater_head.negated = True
    rule = _rule_doc(
        "rule:penguins-block-flight",
        "proper_defeater",
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
        yes={
            "bird": frozenset([("opus",)]),
            "penguin": frozenset([("opus",)]),
        },
    )
    projection = _project(bundle)
    emitted = {
        projection.origins[rule].source_rule_id: rule
        for rule in projection.defeasible_rules
        if rule.name is not None
    }
    target_rule = emitted["rule:birds-fly"]
    defeater_rule = emitted["rule:penguins-block-flight"]
    assert target_rule.name is not None
    assert target_rule.consequent == Literal(
        atom=GroundAtom("flies", ("opus",)),
        negated=False,
    )
    assert defeater_rule.consequent == Literal(
        atom=GroundAtom(target_rule.name),
        negated=True,
    )
    assert projection.literals[ground_key(GroundAtom(target_rule.name), True)] == defeater_rule.consequent
