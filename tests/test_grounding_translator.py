"""Tests for the propstore -> gunray defeasible-theory translator.

These tests describe the contract for the Phase-1 translator that will
live in ``propstore/grounding/translator.py``. The module does not
exist yet — every import is deferred (into strategy bodies and test
bodies) so pytest can collect this file cleanly while every test fails
at run time with ``ModuleNotFoundError: No module named
'propstore.grounding.translator'``.

Target output format (verified by runtime inspection of
``gunray.schema``; authoritative field names):

    ``gunray.schema.DefeasibleTheory`` is a dataclass with six fields:

        facts: PredicateFacts
            -- ``dict[str, Iterable[tuple[Scalar, ...]]]`` where
            ``Scalar = str | int | float | bool``. Keyed by predicate
            name; each value is an iterable of argument tuples.
        strict_rules: list[Rule]
        defeasible_rules: list[Rule]
        defeaters: list[Rule]
        superiority: list[tuple[str, str]]
        conflicts: list[tuple[str, str]]

    ``gunray.schema.Rule`` is a dataclass with three fields:

        id: str
        head: str       -- STRING atom, e.g. ``"flies(X)"``
        body: list[str] -- STRING atoms, e.g. ``["bird(X)"]``

    Gunray parses ``head``/``body`` back into structured
    ``Atom``/``DefeasibleRule`` objects at evaluation time via
    ``gunray.parser.parse_defeasible_theory``. Variables are uppercase
    identifiers; constants are lowercase or literals. The translator's
    job is to stringify propstore's structured ``RuleDocument``
    (which carries ``AtomDocument``/``TermDocument`` internally) into
    that surface syntax while preserving predicate, argument order,
    and variable/constant discrimination.

Supported surface:

- ``kind == "strict"`` populates ``strict_rules``.
- ``kind == "defeasible"`` populates ``defeasible_rules``.
- ``kind == "defeater"`` populates ``defeaters``.
- No superiority pairs (empty list in output). Phase 2.
- No cross-predicate conflicts (empty list in output). Phase 2.
- ``arity == 1`` predicates are what concept-relation derivations
  currently produce, but the translator must not hardcode arity; it
  translates whatever structured atom shape it is given.

Theoretical sources:

    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (p.3): a Datalog program is (facts, rules) where
      facts are ground atoms ``p(c_1,...,c_n)`` and rules are still
      quantified at schema level; grounding happens when the
      evaluator enumerates substitutions over the Herbrand base.
    - Section 3 (Definition 9): the ground substitution set is a
      function of the program and its fact base — the translator
      must not ground rules itself; that is gunray's job.
    - Section 4: stratified negation and constraints are extensions
      over the base Datalog surface; both are Phase 4 here.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic
    Programming: An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): a DeLP program is a pair ``(Facts, Rules)``
      plus a superiority relation ``>``; Phase 1 defers ``>`` and
      conflicts entirely. The canonical ``flies(X) -< bird(X)``
      defeasible rule plus the ``bird(tweety)`` fact is the
      textbook toy example used throughout the tests below.
    - Section 3: rule syntax uses ``-<`` for defeasible, ``<-`` for
      strict; this surface distinction maps onto the
      ``RuleDocument.kind`` discriminant on the propstore side and
      onto the ``defeasible_rules`` / ``strict_rules`` /
      ``defeaters`` lists on the gunray-schema side.
    - Section 3.3 (p.8): safe rules have every head variable
      appearing in the body, so stringifying head variables and
      body variables is well-defined.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


# ── Local builders (no conftest, no helpers outside this file) ──────
#
# Deferred imports: every helper imports propstore types inside its
# body so test collection succeeds even though
# ``propstore.grounding.translator`` does not exist yet.


_VARIABLE_NAMES = st.sampled_from(["X", "Y", "Z"])
_CONSTANT_NAMES = st.sampled_from(["tweety", "opus", "polly"])
_HEAD_PREDICATES = st.sampled_from(["flies", "walks", "swims"])
_BODY_PREDICATES = st.sampled_from(["bird", "penguin", "fish"])


def _build_term_var(name: str):
    """Build a ``TermDocument`` tagged as a variable.

    Garcia & Simari 2004 §3 (p.3-4): variables are uppercase
    identifiers that the Herbrand grounding pass will substitute.
    """

    from propstore.artifacts.documents.rules import TermDocument

    return TermDocument(kind="var", name=name, value=None)


def _build_term_const(value):
    """Build a ``TermDocument`` tagged as a constant.

    Garcia & Simari 2004 §3: constants are lowercase tokens or
    literals drawn from the ``Scalar`` union ``str | int | float |
    bool``.
    """

    from propstore.artifacts.documents.rules import TermDocument

    return TermDocument(kind="const", name=None, value=value)


def _build_atom(predicate: str, terms):
    """Build an ``AtomDocument`` with the supplied predicate and terms.

    Diller, Borg, Bex 2025 §3 fixes the ``p(t_1,...,t_n)`` shape the
    gunray schema consumes after stringification.
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
    (``<-``), defeasible (``-<``), and defeater rules; Phase 1 of the
    translator only accepts ``kind == "defeasible"``.
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

    Mirrors the ``LoadedRuleFile`` envelope shape from
    ``propstore/rule_documents.py`` (§3 of Garcia & Simari 2004: a
    rule file is a flat tuple of rules anchored to a paper source).
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
    predicates by id, with arity and per-position types fixed at
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

    Mirrors ``_build_registry`` in ``tests/test_grounding_facts.py``
    (Diller, Borg, Bex 2025 §3: the registry is the flat id->schema
    map the grounding pipeline queries).
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
    consequent. Diller, Borg, Bex 2025 §3 registers both by id into
    the Datalog schema.
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
        ]
    )


# ── Hypothesis strategies ───────────────────────────────────────────


def defeasible_rule_documents() -> st.SearchStrategy:
    """Strategy producing ``kind == "defeasible"`` RuleDocument values.

    Each rule has a single-variable head and a single-variable body
    over the canonical ``flies(X) -< bird(X)`` shape (Garcia & Simari
    2004 §3). Rule ids are unique per draw so a generated rule tuple
    never collides. Only ``kind == "defeasible"`` is produced because
    Phase 1 of the translator rejects ``strict`` and ``defeater``
    rules; mixing them into the property tests would require every
    property to branch on kind.
    """

    @st.composite
    def _build(draw):
        rule_id = draw(
            st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
                min_size=1,
                max_size=8,
            )
        )
        head_pred = draw(_HEAD_PREDICATES)
        body_pred = draw(_BODY_PREDICATES)
        variable = draw(_VARIABLE_NAMES)
        head = _build_atom(head_pred, [_build_term_var(variable)])
        body_atom = _build_atom(body_pred, [_build_term_var(variable)])
        return _build_rule_document(
            rule_id=rule_id,
            kind="defeasible",
            head=head,
            body=(body_atom,),
        )

    return _build()


def defeasible_rule_file_sequences() -> st.SearchStrategy:
    """Strategy producing a ``list[LoadedRuleFile]`` over defeasible rules.

    Rule ids are made globally unique across the whole file sequence
    so a flattened view carries no collisions (Diller, Borg, Bex 2025
    §3 treats rule ids as the stable key for downstream argument
    construction; duplicates would be authoring errors).
    """

    @st.composite
    def _build(draw):
        rule_count = draw(st.integers(min_value=0, max_value=4))
        rules = []
        for index in range(rule_count):
            base_rule = draw(defeasible_rule_documents())
            # Rewrite id to guarantee uniqueness regardless of what
            # the inner strategy drew.
            unique_id = f"r{index}_{base_rule.id}"
            rules.append(
                _build_rule_document(
                    rule_id=unique_id,
                    kind=base_rule.kind,
                    head=base_rule.head,
                    body=base_rule.body,
                )
            )
        # Split rules across 1..len files to exercise multi-file input.
        if rules:
            split_point = draw(st.integers(min_value=1, max_value=len(rules)))
            file_a = _build_rule_file(rules[:split_point])
            file_b = _build_rule_file(rules[split_point:])
            return [file_a, file_b]
        return [_build_rule_file([])]

    return _build()


def ground_fact_tuples() -> st.SearchStrategy:
    """Strategy producing a ``tuple[GroundAtom, ...]`` over bird-like atoms.

    Garcia & Simari 2004 §3: ground atoms are ``p(c_1,...,c_n)`` with
    constants drawn from the Herbrand base. Diller, Borg, Bex 2025 §3
    Def 7 fixes that shape. Facts here are deduplicated to mirror the
    ``extract_facts`` guarantee — the translator must preserve the
    multiset it receives without adding its own duplicates.
    """

    @st.composite
    def _build(draw):
        from propstore.aspic import GroundAtom

        count = draw(st.integers(min_value=0, max_value=5))
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


# ── Property tests ─────────────────────────────────────────────────


@given(
    rule_files=st.deferred(defeasible_rule_file_sequences),
    facts=st.deferred(ground_fact_tuples),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_translate_preserves_fact_count(rule_files, facts) -> None:
    """Every input fact appears exactly once in the output theory.

    Diller, Borg, Bex 2025 §3: facts are ground atoms in the Herbrand
    base. The translator preserves the fact multiset without
    deduplication (facts are already deduplicated by
    ``extract_facts``). Garcia & Simari 2004 §3 treats the fact base
    as a set, so round-trip count preservation is the minimum
    invariant this test pins.
    """

    from propstore.grounding.translator import translate_to_theory

    theory = translate_to_theory(rule_files, facts, _bird_registry())

    total_rows = sum(
        len(list(rows)) for rows in theory.facts.values()
    )
    assert total_rows == len(facts)


@given(
    rule_files=st.deferred(defeasible_rule_file_sequences),
    facts=st.deferred(ground_fact_tuples),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_translate_preserves_rule_count(rule_files, facts) -> None:
    """Every authored RuleDocument appears as exactly one schema rule.

    Note: schema rules are still quantified — grounding happens when
    gunray evaluates the theory. This test pins the 1-to-1 shape
    (Diller, Borg, Bex 2025 §3 Definition 9: the ground substitution
    pass is gunray's job, not the translator's). Garcia & Simari 2004
    §3 treats rule identity as stable across the program pair.
    """

    from propstore.grounding.translator import translate_to_theory

    theory = translate_to_theory(rule_files, facts, _bird_registry())

    input_rule_count = sum(len(file.rules) for file in rule_files)
    total_output_rules = (
        len(theory.strict_rules)
        + len(theory.defeasible_rules)
        + len(theory.defeaters)
    )
    assert total_output_rules == input_rule_count
    assert theory.superiority == []
    assert theory.conflicts == []


@given(
    rule_files=st.deferred(defeasible_rule_file_sequences),
    facts=st.deferred(ground_fact_tuples),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_translate_rule_head_predicate_preserved(rule_files, facts) -> None:
    """For every RuleDocument, the schema rule's head predicate matches
    the original head's predicate.

    Gunray stringifies atoms as ``predicate(args...)`` (verified via
    ``gunray.parser.parse_atom_text``); the predicate is everything
    before the first ``(``. Garcia & Simari 2004 §3 fixes the
    predicate symbol as the stable identity of the rule head.
    """

    from gunray.parser import parse_atom_text

    from propstore.grounding.translator import translate_to_theory

    theory = translate_to_theory(rule_files, facts, _bird_registry())

    schema_rules = [
        *theory.strict_rules,
        *theory.defeasible_rules,
        *theory.defeaters,
    ]
    input_rules = [rule for file in rule_files for rule in file.rules]

    assert len(schema_rules) == len(input_rules)
    for schema_rule, rule_doc in zip(schema_rules, input_rules):
        parsed_head = parse_atom_text(schema_rule.head)
        assert parsed_head.predicate == rule_doc.head.predicate


@given(
    rule_files=st.deferred(defeasible_rule_file_sequences),
    facts=st.deferred(ground_fact_tuples),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_translate_rule_body_predicates_preserved(rule_files, facts) -> None:
    """For every RuleDocument, the schema rule body's predicate sequence
    matches the original body atoms' predicate sequence.

    Diller, Borg, Bex 2025 §3: rule bodies are ordered atom sequences
    in the Datalog surface; ordering feeds into the structured
    argument's premise ordering (Modgil & Prakken 2018 Def 13).
    Garcia & Simari 2004 §3 treats body order as authoring intent.
    """

    from gunray.parser import parse_atom_text

    from propstore.grounding.translator import translate_to_theory

    theory = translate_to_theory(rule_files, facts, _bird_registry())

    schema_rules = [
        *theory.strict_rules,
        *theory.defeasible_rules,
        *theory.defeaters,
    ]
    input_rules = [rule for file in rule_files for rule in file.rules]

    for schema_rule, rule_doc in zip(schema_rules, input_rules):
        parsed_body_predicates = [
            parse_atom_text(item).predicate for item in schema_rule.body
        ]
        expected = [atom.predicate for atom in rule_doc.body]
        assert parsed_body_predicates == expected


@given(
    rule_id=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
        min_size=1,
        max_size=8,
    ),
    kind=st.sampled_from(["strict", "defeasible", "defeater"]),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_translate_rule_kind_routes_to_matching_schema_slot(rule_id, kind) -> None:
    """Each authored rule kind lands in the matching gunray schema slot."""

    from propstore.grounding.translator import translate_to_theory

    head = _build_atom("flies", [_build_term_var("X")])
    body = _build_atom("bird", [_build_term_var("X")])
    rule = _build_rule_document(
        rule_id=rule_id,
        kind=kind,
        head=head,
        body=(body,),
    )
    rule_file = _build_rule_file([rule])
    theory = translate_to_theory([rule_file], (), _bird_registry())

    assert len(theory.strict_rules) == (1 if kind == "strict" else 0)
    assert len(theory.defeasible_rules) == (1 if kind == "defeasible" else 0)
    assert len(theory.defeaters) == (1 if kind == "defeater" else 0)


@given(
    facts=st.deferred(ground_fact_tuples),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_translate_fact_atoms_preserved(facts) -> None:
    """For every input ``GroundAtom``, a matching row appears in the
    output theory's ``facts`` map under the atom's predicate.

    Diller, Borg, Bex 2025 §3 Definition 7: a Datalog fact base is
    keyed by predicate id with tuple-valued argument rows. The
    translator must preserve each input atom's predicate and argument
    vector verbatim — the schema stores them as plain tuples the
    gunray parser can later ingest. Garcia & Simari 2004 §3 fixes the
    same shape at the Herbrand level.
    """

    from propstore.grounding.translator import translate_to_theory

    theory = translate_to_theory([], facts, _bird_registry())

    for atom in facts:
        rows = list(theory.facts.get(atom.predicate, ()))
        assert tuple(atom.arguments) in [tuple(row) for row in rows]


# ── Concrete example tests ─────────────────────────────────────────


def test_translate_empty_inputs_produces_empty_theory() -> None:
    """Empty rule files and empty facts produce a ``DefeasibleTheory``
    with empty fact and rule sets.

    Degenerate case — pins the boundary. Diller, Borg, Bex 2025 §3:
    the empty program has an empty Herbrand base; Garcia & Simari
    2004 §3 treats ``(∅, ∅, ∅)`` as a well-formed DeLP program.
    """

    from gunray import schema

    from propstore.grounding.translator import translate_to_theory

    theory = translate_to_theory([], (), _bird_registry())

    assert isinstance(theory, schema.DefeasibleTheory)
    assert theory.defeasible_rules == []
    assert theory.strict_rules == []
    assert theory.defeaters == []
    assert theory.superiority == []
    assert theory.conflicts == []
    # facts is a dict keyed by predicate; empty input means no keys
    # carry any rows.
    total_rows = sum(len(list(rows)) for rows in theory.facts.values())
    assert total_rows == 0


def test_translate_delp_birds_fly_example() -> None:
    """Garcia & Simari 2004 §3 canonical example: birds fly.

    Input:
    - 1 RuleDocument: ``flies(X) -< bird(X)``, ``kind=defeasible``
    - 1 fact: ``bird(tweety)``

    Output ``DefeasibleTheory`` has:
    - 1 defeasible schema rule whose parsed head atom is
      ``flies(X)`` (predicate ``flies``, single variable ``X``)
    - 1 defeasible schema rule whose parsed body atom is
      ``bird(X)`` (predicate ``bird``, single variable ``X``)
    - 1 row under ``facts["bird"]`` equal to ``("tweety",)``

    Parsing round-trip uses ``gunray.parser.parse_atom_text`` because
    the schema stores string surface syntax, not structured atoms
    (Diller, Borg, Bex 2025 §3).
    """

    from gunray.parser import parse_atom_text
    from gunray.types import Variable

    from propstore.aspic import GroundAtom
    from propstore.grounding.translator import translate_to_theory

    rule = _build_rule_document(
        rule_id="delp_birds_fly",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])

    fact = GroundAtom("bird", ("tweety",))

    theory = translate_to_theory([rule_file], (fact,), _bird_registry())

    # Exactly one defeasible rule.
    assert len(theory.defeasible_rules) == 1
    schema_rule = theory.defeasible_rules[0]

    # Parsed head: flies(X).
    head_atom = parse_atom_text(schema_rule.head)
    assert head_atom.predicate == "flies"
    assert len(head_atom.terms) == 1
    assert head_atom.terms[0] == Variable(name="X")

    # Parsed body: [bird(X)].
    assert len(schema_rule.body) == 1
    body_atom = parse_atom_text(schema_rule.body[0])
    assert body_atom.predicate == "bird"
    assert len(body_atom.terms) == 1
    assert body_atom.terms[0] == Variable(name="X")

    # Exactly one fact row under ``bird``.
    bird_rows = [tuple(row) for row in theory.facts.get("bird", ())]
    assert bird_rows == [("tweety",)]


def test_translate_multiple_facts_same_predicate() -> None:
    """Input: rule ``flies(X) -< bird(X)`` + facts ``{bird(tweety),
    bird(opus)}``. Output: one schema rule, two schema fact rows.

    Grounding is NOT done here — that is gunray's job (Diller, Borg,
    Bex 2025 §3 Definition 9). Garcia & Simari 2004 §3.1 treats the
    Herbrand instances as a gunray-side concern once the fact base is
    populated.
    """

    from propstore.aspic import GroundAtom
    from propstore.grounding.translator import translate_to_theory

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

    theory = translate_to_theory([rule_file], facts, _bird_registry())

    assert len(theory.defeasible_rules) == 1
    bird_rows = {tuple(row) for row in theory.facts.get("bird", ())}
    assert bird_rows == {("tweety",), ("opus",)}


def test_translate_strict_rule_populates_strict_rules() -> None:
    """A ``kind=strict`` RuleDocument populates ``strict_rules``."""

    from propstore.grounding.translator import translate_to_theory

    rule = _build_rule_document(
        rule_id="strict_bird",
        kind="strict",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])

    theory = translate_to_theory([rule_file], (), _bird_registry())
    assert [rule.id for rule in theory.strict_rules] == ["strict_bird"]
    assert theory.defeasible_rules == []
    assert theory.defeaters == []


def test_translate_defeater_rule_populates_defeaters() -> None:
    """A ``kind=defeater`` RuleDocument populates ``defeaters``."""

    from propstore.grounding.translator import translate_to_theory

    rule = _build_rule_document(
        rule_id="defeater_penguin",
        kind="defeater",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("penguin", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])

    theory = translate_to_theory([rule_file], (), _bird_registry())
    assert [rule.id for rule in theory.defeaters] == ["defeater_penguin"]
    assert theory.strict_rules == []
    assert theory.defeasible_rules == []


def test_translate_strongly_negated_head_preserves_surface_negation() -> None:
    """Strong-negated heads must round-trip as ``~predicate(...)`` text."""

    from gunray.parser import parse_atom_text

    from propstore.grounding.translator import translate_to_theory

    head = _build_atom("flies", [_build_term_var("X")])
    head.negated = True
    rule = _build_rule_document(
        rule_id="strong_neg_head",
        kind="defeasible",
        head=head,
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])

    theory = translate_to_theory([rule_file], (), _bird_registry())

    assert theory.defeasible_rules[0].head == "~flies(X)"
    assert parse_atom_text(theory.defeasible_rules[0].head).predicate == "~flies"


def test_translate_strongly_negated_body_atom_preserves_surface_negation() -> None:
    """Strong-negated body atoms must round-trip as ``~predicate(...)`` text."""

    from gunray.parser import parse_atom_text

    from propstore.grounding.translator import translate_to_theory

    body_atom = _build_atom("bird", [_build_term_var("X")])
    body_atom.negated = True
    rule = _build_rule_document(
        rule_id="strong_neg_body",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(body_atom,),
    )
    rule_file = _build_rule_file([rule])

    theory = translate_to_theory([rule_file], (), _bird_registry())

    assert theory.defeasible_rules[0].body == ["~bird(X)"]
    assert parse_atom_text(theory.defeasible_rules[0].body[0]).predicate == "~bird"


def test_translate_preserves_authored_superiority_pairs() -> None:
    """Rule-file superiority flows into the gunray theory unchanged.

    The authored surface uses Garcia & Simari's ``superior > inferior``
    orientation, matching the gunray schema's ``(superior, inferior)``
    pair shape.
    """
    from quire.documents import LoadedDocument
    from propstore.artifacts.documents.rules import (
        RuleSourceDocument,
        RulesFileDocument,
    )
    from propstore.rule_files import LoadedRuleFile
    from propstore.grounding.translator import translate_to_theory

    generic = _build_rule_document(
        rule_id="r1",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    specific = _build_rule_document(
        rule_id="r2",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("penguin", [_build_term_var("X")]),),
    )
    loaded = LoadedDocument(
        filename="superiority.yaml",
        source_path=None,
        knowledge_root=None,
        document=RulesFileDocument(
            source=RuleSourceDocument(paper="Garcia_2004_DefeasibleLogicProgramming"),
            rules=(generic, specific),
            superiority=(("r2", "r1"),),
        ),
    )
    rule_file = LoadedRuleFile.from_loaded_document(loaded)

    theory = translate_to_theory([rule_file], (), _bird_registry())

    assert theory.superiority == [("r2", "r1")]


def test_translate_string_constant_round_trips_control_characters() -> None:
    """String constants with control characters must stay parseable.

    The translator emits Gunray surface syntax, so a string constant with
    embedded newline/tab characters must be encoded as a valid string literal,
    not injected verbatim into the output surface.
    """

    from gunray.parser import parse_atom_text
    from gunray.types import Constant

    from propstore.grounding.translator import translate_to_theory

    constant_value = "line1\nline2\tquoted"
    rule = _build_rule_document(
        rule_id="control_chars",
        kind="defeasible",
        head=_build_atom("label", [_build_term_const(constant_value)]),
        body=(),
    )
    rule_file = _build_rule_file([rule])
    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="label",
                arity=1,
                arg_types=("Concept",),
                derived_from=None,
            )
        ]
    )

    theory = translate_to_theory([rule_file], (), registry)

    assert theory.defeasible_rules[0].head == 'label("line1\\nline2\\tquoted")'
    parsed_head = parse_atom_text(theory.defeasible_rules[0].head)
    assert parsed_head.terms == (Constant(value=constant_value),)
