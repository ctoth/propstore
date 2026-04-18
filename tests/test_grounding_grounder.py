"""Tests for the propstore grounder — chunk 1.5a (red).

These tests describe the contract for the Phase-1 grounder that will
live in ``propstore/grounding/grounder.py`` together with the
``GroundedRulesBundle`` dataclass in ``propstore/grounding/bundle.py``.

Neither module exists yet — every import of either module is deferred
into strategy bodies or test bodies so pytest can *collect* this file
cleanly while every test fails at run time with
``ModuleNotFoundError: No module named 'propstore.grounding.grounder'``
(or ``...bundle``).

Target output format (verified via runtime inspection of the gunray
evaluator; see report):

    The gunray ``DefeasibleEvaluator`` returns a
    ``gunray.schema.DefeasibleModel`` whose ``sections`` field has the
    type

        dict[str, dict[str, set[tuple[Scalar, ...]]]]

    The outer key is the gunray section name
    (``definitely`` / ``defeasibly`` / ``not_defeasibly`` / ``undecided``)
    and the inner key is the predicate id. **Empty sections are
    dropped** by gunray's evaluator (``defeasible.py`` builds the
    result via ``{name: facts_map for ... if facts_map}``), so the
    grounder's job is to *re-normalise* the section dict so all four
    section names are always present — that is the
    non-commitment-discipline anchor for this pipeline.

    ``Scalar = str | int | float | bool`` (see
    ``gunray.schema.Scalar`` and ``argumentation.aspic.Scalar`` — both
    are the same union).

Theoretical sources:

    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (Definition 7, p.3): a Datalog program's fact base is
      a finite set of ground atoms in the Herbrand base; the fact
      base is trivially in the ground model.
    - Section 3 (Definition 9): the ground substitution set is a
      function of the program and its fact base — grounding
      enumerates all variable substitutions that satisfy the body.
      The grounder delegates this enumeration to gunray.
    - Section 4: a ground model is the closure of the fact base under
      the rules; every ground atom has a well-defined status.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic
    Programming: An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): the canonical DeLP example is
      ``bird(tweety) ∈ Facts`` with the defeasible rule
      ``flies(X) -< bird(X)``. The Phase-1 grounder reproduces this
      textbook derivation end-to-end.
    - Section 4 (p.25): a defeasible program has a four-valued answer
      system — YES (strict-provable), NO (overruled),
      UNDECIDED (blocked by equal-strength peer), UNKNOWN
      (no supporting rule). Gunray's four sections
      (``definitely`` / ``defeasibly`` / ``not_defeasibly`` /
      ``undecided``) map onto that answer system. The
      non-commitment anchor here is that **all four sections are
      preserved in the bundle, even when empty** — render-time
      policy decides which to surface; storage never drops one.
"""

from __future__ import annotations

import dataclasses

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


# ── Local builders (no conftest, no helpers outside this file) ──────
#
# Deferred imports: every helper imports propstore types inside its
# body so test collection succeeds even though
# ``propstore.grounding.grounder`` and ``propstore.grounding.bundle``
# do not exist yet. This mirrors the pattern from
# ``tests/test_grounding_translator.py`` — the prompt explicitly asks
# for inline duplication rather than shared fixtures.


_VARIABLE_NAMES = st.sampled_from(["X", "Y", "Z"])
_CONSTANT_NAMES = st.sampled_from(["tweety", "opus", "polly"])
_HEAD_PREDICATES = st.sampled_from(["flies", "walks", "swims"])
_BODY_PREDICATES = st.sampled_from(["bird", "penguin", "fish"])


def _build_term_var(name: str):
    """Build a variable ``TermDocument``.

    Garcia & Simari 2004 §3 (p.3-4): variables are uppercase
    identifiers that the Herbrand grounding pass substitutes.
    """

    from propstore.artifacts.documents.rules import TermDocument

    return TermDocument(kind="var", name=name, value=None)


def _build_atom(predicate: str, terms):
    """Build an ``AtomDocument`` with the supplied predicate and terms.

    Diller, Borg, Bex 2025 §3 fixes the ``p(t_1,...,t_n)`` shape that
    the gunray schema consumes after stringification.
    """

    from propstore.artifacts.documents.rules import AtomDocument

    return AtomDocument(predicate=predicate, terms=tuple(terms), negated=False)


def _build_rule_document(
    rule_id: str,
    kind: str,
    head,
    body=(),
):
    """Build a ``RuleDocument``.

    Garcia & Simari 2004 §3: DeLP rules partition into strict
    (``<-``), defeasible (``-<``), and defeater rules. Phase 1 of the
    grounder consumes authored strict, defeasible, and defeater rules.
    """

    from propstore.artifacts.documents.rules import RuleDocument

    return RuleDocument(
        id=rule_id,
        kind=kind,  # type: ignore[arg-type]
        head=head,
        body=tuple(body),
    )


def _build_rule_file(rules):
    """Wrap a sequence of ``RuleDocument`` in a ``LoadedRuleFile``.

    Mirrors the envelope shape from
    ``propstore/rule_documents.py`` (Garcia & Simari 2004 §3: a rule
    file is a flat tuple of rules anchored to a paper source).
    """

    from quire.documents import LoadedDocument
    from propstore.artifacts.documents.rules import RulesFileDocument, RuleSourceDocument
    from propstore.rule_files import LoadedRuleFile

    file_doc = RulesFileDocument(
        source=RuleSourceDocument(paper="test_paper"),
        rules=tuple(rules),
    )
    loaded = LoadedDocument(
        filename="generated.yaml",
        source_path=None,
        knowledge_root=None,
        document=file_doc,
    )
    return LoadedRuleFile.from_loaded_document(loaded)


def _build_predicate_document(
    predicate_id: str,
    arity: int,
    arg_types=(),
    derived_from=None,
):
    """Build a ``PredicateDocument`` for the typed registry.

    Diller, Borg, Bex 2025 §3-§4: the Datalog schema indexes
    predicates by id with arity and per-position types fixed at
    declaration time.
    """

    from propstore.artifacts.documents.predicates import PredicateDocument

    return PredicateDocument(
        id=predicate_id,
        arity=arity,
        arg_types=tuple(arg_types),
        derived_from=derived_from,
        description=None,
    )


def _build_registry(predicates):
    """Wrap predicate documents in a ``PredicateRegistry``.

    Diller, Borg, Bex 2025 §3: the registry is the flat id->schema
    map that the grounding pipeline queries at fact-extraction and
    substitution time.
    """

    from propstore.grounding.predicates import PredicateRegistry
    from quire.documents import LoadedDocument
    from propstore.artifacts.documents.predicates import PredicatesFileDocument
    from propstore.predicate_files import LoadedPredicateFile

    file_doc = PredicatesFileDocument(predicates=tuple(predicates))
    loaded = LoadedDocument(
        filename="generated",
        source_path=None,
        knowledge_root=None,
        document=file_doc,
    )
    file = LoadedPredicateFile.from_loaded_document(loaded)
    return PredicateRegistry.from_files([file])


def _bird_registry():
    """Registry declaring the canonical ``bird/1`` and ``flies/1`` pair.

    Garcia & Simari 2004 §3: ``bird/1`` is the textbook
    defeasible-reasoning predicate; ``flies/1`` is the defeasible
    consequent. Diller, Borg, Bex 2025 §3 registers both by id.
    """

    return _build_registry(
        [
            _build_predicate_document(
                predicate_id="bird",
                arity=1,
                arg_types=("Concept",),
                derived_from="concept.relation:is_a:Bird",
            ),
            _build_predicate_document(
                predicate_id="flies",
                arity=1,
                arg_types=("Concept",),
                derived_from=None,
            ),
            _build_predicate_document(
                predicate_id="penguin",
                arity=1,
                arg_types=("Concept",),
                derived_from=None,
            ),
        ]
    )


# ── Hypothesis strategies ───────────────────────────────────────────
#
# All strategies are wrapped via ``st.deferred`` at the @given call
# site — the prompt requires deferred imports so the test file can be
# collected even though ``propstore.grounding.grounder`` and
# ``propstore.grounding.bundle`` have not been created yet.


def ground_atom_tuples() -> st.SearchStrategy:
    """Strategy producing a ``tuple[GroundAtom, ...]`` of small size.

    Diller, Borg, Bex 2025 §3 Definition 7: the fact base is a finite
    set of ground atoms ``p(c_1,...,c_n)``. Garcia & Simari 2004 §3
    uses ``bird(tweety)`` as the canonical example. The strategy
    deduplicates so the generated tuple matches the ``extract_facts``
    guarantee (no repeats).
    """

    @st.composite
    def _build(draw):
        from argumentation.aspic import GroundAtom

        count = draw(st.integers(min_value=0, max_value=4))
        seen: set[tuple[str, tuple[str, ...]]] = set()
        atoms: list = []
        for _ in range(count):
            predicate = draw(_BODY_PREDICATES)
            constant = draw(_CONSTANT_NAMES)
            key = (predicate, (constant,))
            if key in seen:
                continue
            seen.add(key)
            atoms.append(GroundAtom(predicate, (constant,)))
        return tuple(atoms)

    return _build()


def defeasible_rule_file_batches() -> st.SearchStrategy:
    """Strategy producing a small ``list[LoadedRuleFile]`` of defeasible rules.

    Rules are safe-by-construction — the head variable is drawn from
    the same pool as the body variable (Garcia & Simari 2004 §3.3,
    p.8: every head variable must appear in the body for a rule to
    be safe, otherwise grounding is ill-defined). Rule ids are made
    globally unique across the batch so a flattened view carries no
    collisions (Diller, Borg, Bex 2025 §3 treats the rule id as the
    stable key for downstream argument construction).
    """

    @st.composite
    def _build(draw):
        rule_count = draw(st.integers(min_value=0, max_value=3))
        rules: list = []
        for index in range(rule_count):
            head_pred = draw(_HEAD_PREDICATES)
            body_pred = draw(_BODY_PREDICATES)
            variable = draw(_VARIABLE_NAMES)
            head = _build_atom(head_pred, [_build_term_var(variable)])
            body_atom = _build_atom(body_pred, [_build_term_var(variable)])
            rules.append(
                _build_rule_document(
                    rule_id=f"r{index}",
                    kind="defeasible",
                    head=head,
                    body=(body_atom,),
                )
            )
        if not rules:
            return [_build_rule_file([])]
        # Split across 1..len files to exercise multi-file input
        # (Diller, Borg, Bex 2025 §3: rule files are a compositional
        # surface — the grounder must be invariant over how they are
        # split at authoring time).
        split_point = draw(st.integers(min_value=1, max_value=len(rules)))
        file_a = _build_rule_file(rules[:split_point])
        file_b = _build_rule_file(rules[split_point:])
        return [file_a, file_b]

    return _build()


def rule_file_batches() -> st.SearchStrategy:
    """Alias used by the rule/fact preservation property test.

    Diller, Borg, Bex 2025 §3: grounding a first-order rule base
    against a fact base is deterministic in the program inputs; the
    preserved-rules property test reuses the same batch generator.
    """

    return defeasible_rule_file_batches()


# ── Expected gunray section names ───────────────────────────────────
#
# These are the four section names gunray's ``DefeasibleEvaluator``
# emits (see ``gunray.defeasible.evaluate_with_trace``). The grounder
# normalises its output so every bundle has all four keys present,
# even when one or more sections are empty — that is the
# non-commitment anchor from Garcia & Simari 2004 §4 (p.25, four-
# valued answer system).
_FOUR_SECTIONS = ("definitely", "defeasibly", "not_defeasibly", "undecided")


# ── Bundle tests ───────────────────────────────────────────────────


def test_bundle_is_frozen() -> None:
    """GroundedRulesBundle is an immutable frozen dataclass.

    Diller, Borg, Bex 2025 §3: the grounded model is a pure function
    of the program inputs; the bundle wrapping that model therefore
    must not be mutated after construction. Attempting to set any
    field raises ``dataclasses.FrozenInstanceError``.
    """

    from propstore.grounding.bundle import GroundedRulesBundle
    from propstore.grounding.grounder import ground

    bundle = ground([], (), _bird_registry())
    assert isinstance(bundle, GroundedRulesBundle)
    with pytest.raises(dataclasses.FrozenInstanceError):
        bundle.source_rules = ()  # type: ignore[misc]


def test_bundle_sections_are_immutable() -> None:
    """Bundle ``sections`` maps and inner collections cannot be mutated.

    Garcia & Simari 2004 §4 (p.25): the four-valued answer system is
    the authoritative record of a defeasible program's conclusions;
    mutating the bundle after construction would silently corrupt
    that record. The bundle either stores the sections as a
    ``Mapping`` view that rejects assignment (``TypeError``) or as a
    frozen mapping type — either way, attempts to mutate must raise.
    """

    from propstore.grounding.grounder import ground

    bundle = ground([], (), _bird_registry())
    with pytest.raises((TypeError, AttributeError)):
        bundle.sections["definitely"] = {}  # type: ignore[index]


def test_bundle_section_keys_are_the_four_gunray_sections() -> None:
    """Bundle exposes all four gunray section names, always.

    Garcia & Simari 2004 §4 (p.25): the four-valued answer system is
    ``{YES, NO, UNDECIDED, UNKNOWN}`` — every ground literal lands in
    exactly one bucket. Gunray's four sections
    (``definitely`` / ``defeasibly`` / ``not_defeasibly`` /
    ``undecided``) map onto that system. **Non-commitment anchor**:
    no section is ever dropped, even when empty, so render-time
    policy sees the full shape.
    """

    from propstore.grounding.grounder import ground

    bundle = ground([], (), _bird_registry())
    assert set(bundle.sections.keys()) == set(_FOUR_SECTIONS)


# ── Grounder property tests ─────────────────────────────────────────


@given(facts=st.deferred(ground_atom_tuples))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_grounder_only_facts_no_rules_definitely_equals_input(facts) -> None:
    """Diller, Borg, Bex 2025 §3: the fact base is trivially in the
    ground model.

    With no rules, every input fact appears in the ``definitely``
    section under its predicate id, and no new facts are invented.
    Garcia & Simari 2004 §3 treats the Herbrand base as the
    initial state of the derivation.
    """

    from propstore.grounding.grounder import ground

    bundle = ground([], facts, _bird_registry())

    # Every input fact shows up under definitely[predicate].
    for atom in facts:
        rows = bundle.sections["definitely"].get(atom.predicate, frozenset())
        assert tuple(atom.arguments) in {tuple(row) for row in rows}

    # And the definitely section carries no rows the input didn't.
    total_definitely_rows = sum(
        len(rows) for rows in bundle.sections["definitely"].values()
    )
    assert total_definitely_rows == len(facts)


@given(facts=st.deferred(ground_atom_tuples))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_grounder_determinism(facts) -> None:
    """Running ground() twice on the same input produces equal bundles.

    Diller, Borg, Bex 2025 §3 (Definition 9): the ground substitution
    set is a deterministic function of the program and its fact
    base. Reproducibility is required for content-hash addressed
    sidecar builds: if grounding were order-dependent, the sidecar
    would rebuild spuriously on every run.
    """

    from propstore.grounding.grounder import ground

    first = ground([], facts, _bird_registry())
    second = ground([], facts, _bird_registry())
    assert first == second
    assert first.sections == second.sections
    assert first.source_facts == second.source_facts


@given(
    rule_files=st.deferred(rule_file_batches),
    facts=st.deferred(ground_atom_tuples),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_grounder_preserves_source_rules_and_facts(rule_files, facts) -> None:
    """Non-commitment anchor: the bundle is a full record of what
    went in.

    Diller, Borg, Bex 2025 §3: the grounded model is a pair
    ``(P, F) -> M`` — storing only ``M`` loses the provenance of the
    derivation. Garcia & Simari 2004 §4 treats the original rule
    base as part of the program's identity. The bundle therefore
    carries the original ``rule_files`` and ``facts`` verbatim so
    downstream consumers (the T2.5 bridge, the render layer) can
    reach back to the authored inputs.
    """

    from propstore.grounding.grounder import ground

    bundle = ground(rule_files, facts, _bird_registry())
    assert tuple(bundle.source_rules) == tuple(rule_files)
    assert tuple(bundle.source_facts) == tuple(facts)


@given(
    rule_files=st.deferred(defeasible_rule_file_batches),
    facts=st.deferred(ground_atom_tuples),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_grounder_all_four_sections_present(rule_files, facts) -> None:
    """Every grounding produces a bundle with all four section keys.

    Garcia & Simari 2004 §4 (p.25): the four-valued answer system
    always partitions the ground atoms — the sections are
    exhaustive. Diller, Borg, Bex 2025 §3: gunray's evaluator drops
    empty sections in its raw output (see
    ``gunray.defeasible.evaluate_with_trace``); the grounder
    normalises the dict so the bundle always carries all four
    section names, even when some are empty. Render-time policy can
    then decide what to show without having to special-case absent
    keys.
    """

    from propstore.grounding.grounder import ground

    bundle = ground(rule_files, facts, _bird_registry())
    assert set(bundle.sections.keys()) == set(_FOUR_SECTIONS)


# ── Concrete example tests ─────────────────────────────────────────


def test_grounder_empty_everything() -> None:
    """Empty rule files and empty facts produce a bundle with all four
    sections present and empty.

    Diller, Borg, Bex 2025 §3: the empty program has an empty
    Herbrand base and an empty ground model. Garcia & Simari 2004 §3
    treats ``(∅, ∅, ∅)`` as a well-formed DeLP program. The bundle's
    non-commitment anchor means all four section keys still appear,
    each mapping to an empty inner map.
    """

    from propstore.grounding.grounder import ground

    bundle = ground([], (), _bird_registry())
    assert set(bundle.sections.keys()) == set(_FOUR_SECTIONS)
    for name in _FOUR_SECTIONS:
        section = bundle.sections[name]
        # Every inner value must itself be empty — no predicate keys
        # carrying any rows, since there is nothing to ground.
        total = sum(len(rows) for rows in section.values())
        assert total == 0


def test_grounder_delp_birds_fly_tweety() -> None:
    """Garcia & Simari 2004 §3 canonical example: birds fly.

    Setup:
    - One defeasible rule: ``flies(X) -< bird(X)``
    - One fact: ``bird(tweety)``

    Expected (from Garcia & Simari 2004 §4 four-valued answer
    system):
    - ``bird(tweety)`` is strictly provable — it appears in
      ``definitely['bird']``.
    - ``flies(tweety)`` is defeasibly provable via the single
      supporting rule with no attacker — it appears in
      ``defeasibly['flies']``.
    - The translator produces the gunray ``DefeasibleTheory`` with
      a stringified ``flies(X) -< bird(X)`` defeasible rule and the
      ``{'bird': [('tweety',)]}`` fact base, per Diller, Borg, Bex
      2025 §3.
    """

    from argumentation.aspic import GroundAtom
    from propstore.grounding.grounder import ground

    rule = _build_rule_document(
        rule_id="birds_fly",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])

    facts = (GroundAtom("bird", ("tweety",)),)

    bundle = ground([rule_file], facts, _bird_registry())

    # bird(tweety) is strictly provable.
    bird_rows = bundle.sections["definitely"].get("bird", frozenset())
    assert ("tweety",) in {tuple(row) for row in bird_rows}

    # flies(tweety) is defeasibly provable.
    flies_rows = bundle.sections["defeasibly"].get("flies", frozenset())
    assert ("tweety",) in {tuple(row) for row in flies_rows}


def test_grounder_multiple_facts_same_predicate_all_grounded() -> None:
    """One rule ``flies(X) -< bird(X)`` over two birds grounds both.

    Diller, Borg, Bex 2025 §3 (Definition 9): grounding enumerates
    all variable substitutions that satisfy the body. Garcia &
    Simari 2004 §3.1: ground instances are obtained by substituting
    every matching Herbrand-base constant into the rule's
    variables. With ``bird(tweety)`` and ``bird(opus)`` in the fact
    base, the single ``flies(X) -< bird(X)`` rule yields two ground
    defeasibly-provable atoms: ``flies(tweety)`` and ``flies(opus)``.
    """

    from argumentation.aspic import GroundAtom
    from propstore.grounding.grounder import ground

    rule = _build_rule_document(
        rule_id="birds_fly",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])

    facts = (
        GroundAtom("bird", ("tweety",)),
        GroundAtom("bird", ("opus",)),
    )

    bundle = ground([rule_file], facts, _bird_registry())

    flies_rows = {
        tuple(row)
        for row in bundle.sections["defeasibly"].get("flies", frozenset())
    }
    assert ("tweety",) in flies_rows
    assert ("opus",) in flies_rows


def test_grounder_policy_is_configurable() -> None:
    """``ground(..., policy=...)`` threads the policy through to gunray.

    Garcia & Simari 2004 §4 (p.25) discusses ambiguity resolution in
    the four-valued answer system. Diller, Borg, Bex 2025 §3 invokes
    gunray's evaluator over the ground model, and gunray's
    ``GunrayEvaluator.evaluate`` accepts a ``Policy`` enum argument
    (``BLOCKING`` is the default). The grounder must accept a
    ``policy`` keyword and thread it through so callers can switch
    regimes.

    Post-Block-2 (gunray notes/policy_propagating_fate.md) only
    ``Policy.BLOCKING`` remains on the dialectical-tree path;
    ``Policy.PROPAGATING`` was deprecated. This test therefore pins
    the narrower contract: calling with an explicit
    ``Policy.BLOCKING`` returns the same four-sectioned bundle as
    the default invocation, and both populate the canonical
    birds-fly derivation.
    """

    from gunray.schema import Policy

    from argumentation.aspic import GroundAtom
    from propstore.grounding.grounder import ground

    rule = _build_rule_document(
        rule_id="birds_fly",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])
    facts = (GroundAtom("bird", ("tweety",)),)

    bundle_blocking = ground(
        [rule_file], facts, _bird_registry(), policy=Policy.BLOCKING
    )
    assert set(bundle_blocking.sections.keys()) == set(_FOUR_SECTIONS)
    flies_rows = {
        tuple(row)
        for row in bundle_blocking.sections["defeasibly"].get(
            "flies", frozenset()
        )
    }
    assert ("tweety",) in flies_rows

    # Default policy (BLOCKING) also works; both runs populate the
    # canonical defeasibly-provable row.
    bundle_default = ground([rule_file], facts, _bird_registry())
    default_flies_rows = {
        tuple(row)
        for row in bundle_default.sections["defeasibly"].get(
            "flies", frozenset()
        )
    }
    assert ("tweety",) in default_flies_rows


# ── Module structure tests ─────────────────────────────────────────


def test_ground_returns_bundle_instance() -> None:
    """``ground()`` returns a ``GroundedRulesBundle`` (not a dict or tuple).

    Garcia & Simari 2004 §4: the four-valued answer system is an
    indivisible record — splitting it into a bare dict would lose
    the provenance linkage to ``source_rules`` and ``source_facts``.
    Diller, Borg, Bex 2025 §3: the grounded model, the fact base,
    and the rule base travel together through the pipeline.
    """

    from propstore.grounding.bundle import GroundedRulesBundle
    from propstore.grounding.grounder import ground

    bundle = ground([], (), _bird_registry())
    assert isinstance(bundle, GroundedRulesBundle)


def test_ground_accepts_empty_rule_files_sequence() -> None:
    """``ground([], (), registry)`` returns a valid bundle — boundary case.

    Diller, Borg, Bex 2025 §3: the empty program is a valid Datalog
    input. Garcia & Simari 2004 §3 treats ``(∅, ∅)`` as a
    well-formed DeLP program. The Phase-1 grounder must not raise
    on degenerate inputs — the sidecar build pipeline invokes it
    with whatever concept graph happens to be present, and an empty
    graph must not wedge the build.
    """

    from propstore.grounding.grounder import ground

    bundle = ground([], (), _bird_registry())
    # All four sections still present, all empty.
    assert set(bundle.sections.keys()) == set(_FOUR_SECTIONS)
    for name in _FOUR_SECTIONS:
        total = sum(len(rows) for rows in bundle.sections[name].values())
        assert total == 0


# ── B3 argument-level surface ───────────────────────────────────────
#
# Block 3 of the gunray refactor exposes typed ``Argument`` objects
# via ``gunray.build_arguments`` (Garcia & Simari 2004 §3 Def 3.6 and
# Diller, Borg, Bex 2025 §4). Propstore's bundle carries those
# argument objects when the grounder is asked for them, so downstream
# consumers (claim graph, dialectical renderer) can work with typed
# polarity instead of string-keyed sections.


def test_bundle_has_arguments_field() -> None:
    """``GroundedRulesBundle`` exposes an ``arguments`` tuple field.

    Block 3 surface contract: every bundle carries a typed-argument
    view alongside the four-section projection. Defaults to an empty
    tuple so every existing caller that constructs a bundle with
    only the three legacy fields still type-checks and runs.
    """

    from propstore.grounding.bundle import GroundedRulesBundle

    bundle = GroundedRulesBundle.empty()
    assert hasattr(bundle, "arguments")
    assert bundle.arguments == ()


def test_bundle_arguments_is_immutable_tuple() -> None:
    """``GroundedRulesBundle.arguments`` is a tuple (not a list).

    The bundle is a frozen dataclass; every field must be hashable
    for ``hash(bundle)`` to work if a future consumer needs it. A
    tuple is the natural fit for the ordered argument sequence.
    """

    from propstore.grounding.bundle import GroundedRulesBundle

    bundle = GroundedRulesBundle.empty()
    assert isinstance(bundle.arguments, tuple)


def test_ground_default_arguments_field_is_empty() -> None:
    """``ground(...)`` without ``return_arguments`` returns an empty tuple.

    Backwards compatibility: the default invocation of ``ground``
    continues to return bundles whose ``arguments`` field is the
    empty tuple. Block 3 opt-in is explicit — callers must set
    ``return_arguments=True`` to incur the argument-enumeration cost.
    """

    from argumentation.aspic import GroundAtom
    from propstore.grounding.grounder import ground

    rule = _build_rule_document(
        rule_id="birds_fly",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])
    facts = (GroundAtom("bird", ("tweety",)),)

    bundle = ground([rule_file], facts, _bird_registry())
    assert bundle.arguments == ()


def test_ground_return_arguments_populates_tuple() -> None:
    """``ground(..., return_arguments=True)`` fills ``bundle.arguments``.

    Block 3 surface contract: when the caller opts in, the bundle
    carries the full ``frozenset[Argument]`` produced by
    ``gunray.build_arguments`` (Garcia & Simari 2004 §3 Def 3.6). For
    the canonical birds-fly example with ``bird(tweety)`` as the
    sole fact, gunray's argument builder must produce at least one
    argument whose conclusion is ``flies(tweety)``.
    """

    import gunray

    from argumentation.aspic import GroundAtom
    from propstore.grounding.grounder import ground

    rule = _build_rule_document(
        rule_id="birds_fly",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])
    facts = (GroundAtom("bird", ("tweety",)),)

    bundle = ground([rule_file], facts, _bird_registry(), return_arguments=True)
    assert isinstance(bundle.arguments, tuple)
    assert len(bundle.arguments) > 0
    for arg in bundle.arguments:
        assert isinstance(arg, gunray.Argument)
    conclusions = {
        (arg.conclusion.predicate, arg.conclusion.arguments)
        for arg in bundle.arguments
    }
    assert ("flies", ("tweety",)) in conclusions


def test_ground_return_arguments_is_deterministic() -> None:
    """Two identical ``ground(..., return_arguments=True)`` calls agree.

    Diller, Borg, Bex 2025 §3 Definition 9: the grounder must be a
    deterministic function of its inputs. The argument ordering
    produced by Block 3 is pinned by a stable sort key so the same
    theory yields the same argument tuple across invocations.
    """

    from argumentation.aspic import GroundAtom
    from propstore.grounding.grounder import ground

    rule = _build_rule_document(
        rule_id="birds_fly",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])
    facts = (
        GroundAtom("bird", ("tweety",)),
        GroundAtom("bird", ("opus",)),
    )

    first = ground([rule_file], facts, _bird_registry(), return_arguments=True)
    second = ground([rule_file], facts, _bird_registry(), return_arguments=True)
    assert first.arguments == second.arguments


@given(
    rule_files=st.deferred(defeasible_rule_file_batches),
    facts=st.deferred(ground_atom_tuples),
)
@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    max_examples=200,
)
def test_hypothesis_ground_return_arguments_is_deterministic(
    rule_files, facts
) -> None:
    """Property: ``ground(..., return_arguments=True)`` is a pure function.

    Diller, Borg, Bex 2025 §3 Definition 9: the ground substitution
    set is a deterministic function of program plus fact base. Block
    3's argument view inherits that determinism: the tuple returned
    by ``gunray.build_arguments`` is sorted via ``_argument_sort_key``
    so two identical invocations must produce byte-identical
    argument tuples across the full Hypothesis search space (small
    randomly-generated theories with up to 3 defeasible rules and
    up to 4 ground facts, 200 examples).

    The property also pins:

    - Every bundle's ``arguments`` field is a tuple (not a list).
    - Every element is a ``gunray.Argument`` instance.
    - Pairwise equality of two runs holds element-for-element.
    """

    import gunray

    from propstore.grounding.grounder import ground

    first = ground(rule_files, facts, _bird_registry(), return_arguments=True)
    second = ground(rule_files, facts, _bird_registry(), return_arguments=True)

    assert isinstance(first.arguments, tuple)
    assert isinstance(second.arguments, tuple)
    assert first.arguments == second.arguments
    for arg in first.arguments:
        assert isinstance(arg, gunray.Argument)
