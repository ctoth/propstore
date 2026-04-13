"""End-to-end integration tests for the Phase-1 gunray pipeline (RED).

Chunk 1.8a of the gunray workstream: prove the whole pipeline, from
programmatically-built propstore inputs (concepts, predicates, rules)
through the grounder bundle, through the ASPIC+ bridge, to
backward-chained argument construction via ``query_claim`` /
``build_aspic_projection``.

This is the Phase-1 MVP proof for the tweety-the-bird canonical
example. Every test in this file is **expected to fail** at run time
until Chunk 1.8b wires ``grounded_rules_to_rules`` through
``build_bridge_csaf`` / ``build_aspic_projection`` / ``query_claim``.

Construction of every input is inline here (no shared fixtures, no
conftest.py, no helper modules — same constraint as
``tests/test_grounding_facts.py`` and
``tests/test_grounding_grounder.py``). Imports of propstore types are
deferred into test bodies so pytest collection does not depend on the
1.8b symbols existing.

Theoretical sources:
    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): the canonical DeLP example. A fact base
      entry asserting ``bird(tweety)`` combined with the defeasible
      rule ``flies(X) -< bird(X)`` yields the ground instance
      ``flies(tweety) -< bird(tweety)``. The ASPIC+ argument built
      from that instance uses the ground fact as a premise and the
      rule as the top-level step. This test file reproduces that
      textbook derivation end-to-end.
    - Section 3.1 (p.4): ground instances are obtained by replacing
      each variable with a constant drawn from the Herbrand base; the
      grounder enumerates over the propstore concept graph.
    - Section 4 (p.25): four-valued answer system — the bundle always
      exposes all four sections even when some are empty. The bridge
      must therefore never collapse the bundle silently.

    Modgil, S. & Prakken, H. (2018). A general account of
    argumentation with preferences. Artificial Intelligence, 248,
    51-104.
    - Definition 2 (p.8): an argumentation system is
      ``AS = (L, bar, R_s, R_d, n)``. The defeasible-rule set R_d
      produced by Chunk 1.8b must contain one ASPIC+ rule per ground
      instance emitted by the grounder bundle, otherwise build_arguments
      cannot reach the corresponding conclusion.
    - Definition 5 (pp.9-10): argument construction. A defeasible
      rule whose antecedents are all derivable yields a DefeasibleArg
      whose conclusion is the rule head. In the tweety case, the
      single fact ``bird(tweety)`` grounds ``flies(X) -< bird(X)``
      into exactly one DefeasibleArg with conclusion
      ``Literal(GroundAtom('flies', ('tweety',)))``.
    - Definition 10 (p.13): grounded extension. Not directly asserted
      here (1.8a pins the projection-level structural shape), but the
      single defeasible argument with no attackers is in the grounded
      extension by vacuous defense.

    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (Definition 7, p.3): a Datalog fact base is a finite
      set of ground atoms. The bundle's positive sections are
      exactly that set.
    - Section 3 (Definition 9): the ground substitution set is a
      deterministic function of program plus fact base; the bridge
      must therefore thread the bundle (not just the rule text)
      through so the ASPIC+ rule set is reproducible from the same
      inputs.
    - Section 4: ground instances as a deterministic function of
      program plus fact base; the bridge must iterate over the
      bundle's sections rather than re-grounding independently.
"""

from __future__ import annotations

import inspect


# ── Inline construction helpers (not fixtures — module-private) ────
#
# These are module-private builder functions, not pytest fixtures and
# not a shared helper module. The chunk constraint is: no conftest.py,
# no helper file. Each test calls them directly inside its body. The
# helpers live at module level only because duplicating identical
# multi-line record construction across six tests would obscure the
# test intent; Garcia & Simari 2004 §3 uses the same minimal shape
# across the canonical tweety examples.


def _build_concept_relationship(relation: str, target: str):
    """Build a single outgoing ``ConceptRelationship``.

    Garcia & Simari 2004 §3.1 (p.4): concept-graph edges ground the
    Herbrand base. The Phase-1 fact extractor matches
    ``relationship_type`` against the parsed ``derived_from`` spec's
    relation and ``target`` against its target string.
    """

    from propstore.core.concepts import ConceptRelationship
    from propstore.core.id_types import to_concept_id

    return ConceptRelationship(
        relationship_type=relation,
        target=to_concept_id(target),
        conditions=(),
        note=None,
    )


def _build_loaded_concept(canonical_name: str, relationships):
    """Wrap a minimal ``ConceptRecord`` in a ``LoadedConcept`` envelope.

    Garcia & Simari 2004 §3: the canonical name is the token the
    grounder emits as the ground-atom argument (``tweety`` in
    ``bird(tweety)``). ``ConceptRecord``'s frozen-dataclass invariants
    require a handful of metadata fields; only ``canonical_name`` and
    ``relationships`` carry test-meaningful content.
    """

    from propstore.core.concepts import ConceptRecord, LoadedConcept
    from propstore.core.id_types import LogicalId, to_concept_id

    artifact_id = to_concept_id(f"ps:concept:{canonical_name}")
    logical_id = LogicalId(namespace="propstore", value=canonical_name)
    record = ConceptRecord(
        artifact_id=artifact_id,
        canonical_name=canonical_name,
        status="active",
        definition=f"Test concept named {canonical_name}.",
        form="Entity",
        logical_ids=(logical_id,),
        version_id=f"v-{canonical_name}",
        relationships=tuple(relationships),
    )
    return LoadedConcept(
        filename=f"{canonical_name}.yaml",
        source_path=None,
        knowledge_root=None,
        record=record,
    )


def _build_predicate_document(
    predicate_id: str,
    arity: int,
    arg_types,
    derived_from,
):
    """Build one ``PredicateDocument`` for the registry.

    Diller, Borg, Bex 2025 §3 (p.3): a Datalog predicate has a fixed
    arity and per-position typed arguments.
    """

    from propstore.predicate_documents import PredicateDocument

    return PredicateDocument(
        id=predicate_id,
        arity=arity,
        arg_types=tuple(arg_types),
        derived_from=derived_from,
        description=None,
    )


def _build_registry(predicates):
    """Wrap predicates in a populated ``PredicateRegistry``.

    Mirrors the envelope-building pattern used in
    ``tests/test_grounding_facts.py`` — go through
    ``LoadedPredicateFile.from_loaded_document`` so the registry sees
    the same authoring order it would see from disk.
    """

    from propstore.grounding.predicates import PredicateRegistry
    from propstore.loaded import LoadedDocument
    from propstore.predicate_documents import (
        LoadedPredicateFile,
        PredicatesFileDocument,
    )

    file_doc = PredicatesFileDocument(predicates=tuple(predicates))
    loaded = LoadedDocument(
        filename="generated.yaml",
        source_path=None,
        knowledge_root=None,
        document=file_doc,
    )
    predicate_file = LoadedPredicateFile.from_loaded_document(loaded)
    return PredicateRegistry.from_files([predicate_file])


def _build_var(name: str):
    """Build a DeLP variable term.

    Garcia & Simari 2004 §3 (p.3-4): variables are uppercase
    identifiers the Herbrand grounding pass substitutes with
    constants drawn from the fact base.
    """

    from propstore.rule_documents import TermDocument

    return TermDocument(kind="var", name=name, value=None)


def _build_atom(predicate: str, terms):
    """Build a positive (non-negated) ``AtomDocument``.

    Diller, Borg, Bex 2025 §3 (p.3): ``p(t_1,...,t_n)`` is the
    surface shape both the translator and the grounder consume after
    stringification.
    """

    from propstore.rule_documents import AtomDocument

    return AtomDocument(
        predicate=predicate,
        terms=tuple(terms),
        negated=False,
    )


def _build_defeasible_rule(rule_id: str, head, body):
    """Build a defeasible ``RuleDocument`` (``head -< body``).

    Garcia & Simari 2004 §3 (p.3): defeasible rules carry the DeLP
    ``-<`` arrow. Phase 1 of the grounder and the bridge only process
    defeasible rules with an empty ``negative_body``.
    """

    from propstore.rule_documents import RuleDocument

    return RuleDocument(
        id=rule_id,
        kind="defeasible",
        head=head,
        body=tuple(body),
        negative_body=(),
    )


def _build_rule_file(rules):
    """Wrap rule documents in a ``LoadedRuleFile``.

    Garcia & Simari 2004 §3: a rules file is a flat tuple of rules
    anchored to a paper source; order is preserved because Modgil &
    Prakken 2018 Def 13 (last-link preference) can read meaning out
    of authored order.
    """

    from propstore.loaded import LoadedDocument
    from propstore.rule_documents import (
        LoadedRuleFile,
        RulesFileDocument,
        RuleSourceDocument,
    )

    file_doc = RulesFileDocument(
        source=RuleSourceDocument(paper="gunray_integration_test"),
        rules=tuple(rules),
    )
    loaded = LoadedDocument(
        filename="generated.yaml",
        source_path=None,
        knowledge_root=None,
        document=file_doc,
    )
    return LoadedRuleFile.from_loaded_document(loaded)


def _build_tweety_world():
    """Construct the canonical tweety inputs.

    Garcia & Simari 2004 §3 (p.3-4): the textbook defeasible-reasoning
    example is a single-concept fact base ``bird(tweety)`` together
    with the single defeasible rule ``flies(X) -< bird(X)``. The
    returned tuple is ``(concepts, registry, rule_files)`` — exactly
    the shape the fact extractor and the grounder consume.
    """

    # Concept graph: {Bird (root), tweety -is_a-> Bird}.
    # The Bird concept is a bare root without outgoing edges; the
    # tweety concept carries the outgoing ``is_a:Bird`` edge that
    # the extractor materialises as ``bird(tweety)``.
    bird_concept = _build_loaded_concept("Bird", ())
    tweety_concept = _build_loaded_concept(
        "tweety",
        [_build_concept_relationship("is_a", "Bird")],
    )
    concepts = [bird_concept, tweety_concept]

    # Predicate schema: bird/1 derived from concept.relation:is_a:Bird.
    # Diller, Borg, Bex 2025 §4: the ``derived_from`` DSL is the sole
    # bridge from propstore data to the Datalog fact base.
    bird_predicate = _build_predicate_document(
        predicate_id="bird",
        arity=1,
        arg_types=("Bird",),
        derived_from="concept.relation:is_a:Bird",
    )
    # flies/1 is derived from no propstore data — it only appears in
    # rule heads, and the grounder materialises ground instances by
    # enumerating over the fact base. Diller, Borg, Bex 2025 §3: a
    # predicate with ``derived_from is None`` contributes zero facts.
    flies_predicate = _build_predicate_document(
        predicate_id="flies",
        arity=1,
        arg_types=("Bird",),
        derived_from=None,
    )
    registry = _build_registry([bird_predicate, flies_predicate])

    # Rule: flies(X) -< bird(X). Garcia & Simari 2004 §3 canonical
    # defeasible rule.
    variable_x = _build_var("X")
    head = _build_atom("flies", [variable_x])
    body = [_build_atom("bird", [variable_x])]
    rule = _build_defeasible_rule("r_flies_bird", head, body)
    rule_files = [_build_rule_file([rule])]

    return concepts, registry, rule_files


# ── Signature-pinning tests ────────────────────────────────────────
#
# The three tests below pin the *future* signature of the bridge
# functions. In the current 1.7-finished state, none of these
# functions accept a ``bundle``/``grounded_rules`` parameter, so
# inspect-based assertions fail loudly with the exact parameter name
# missing. This is the red target for 1.8b.


def test_build_bridge_csaf_signature_requires_grounded_rules_bundle() -> None:
    """``build_bridge_csaf`` must accept a ``GroundedRulesBundle``.

    Diller, Borg, Bex 2025 §3 Definition 9: the grounded ASPIC+ rule
    set is a deterministic function of program plus fact base. The
    bridge must therefore take the bundle as an explicit parameter
    so the same inputs reproduce the same rule set across runs.
    Modgil & Prakken 2018 Def 2 (p.8) treats R_d as part of the
    argumentation system; threading the bundle in is what lets the
    Phase-1 pipeline materialise R_d from the concept graph.

    Red until Chunk 1.8b: ``inspect.signature(build_bridge_csaf)``
    has no ``bundle`` / ``grounded_rules`` parameter today.
    """

    from propstore.aspic_bridge import build_bridge_csaf

    sig = inspect.signature(build_bridge_csaf)
    assert "bundle" in sig.parameters, (
        "build_bridge_csaf must accept a `bundle: GroundedRulesBundle` "
        "parameter so Chunk 1.8b can thread grounded rules through the "
        "T2.5 stage (Diller, Borg, Bex 2025 §3 Def 9). Current "
        f"parameters: {list(sig.parameters)}"
    )


def test_build_aspic_projection_threads_grounded_rules() -> None:
    """``build_aspic_projection`` must accept a ``GroundedRulesBundle``.

    Same requirement as ``build_bridge_csaf``: the public projection
    entry point is what ``structured_projection.py`` calls from the
    render layer, so it must expose the bundle parameter for the
    Phase-1 pipeline to work end-to-end. Diller, Borg, Bex 2025 §3
    Def 9: determinism requires the bundle travel with the call.
    Modgil & Prakken 2018 Def 5 (pp.9-10): the bundle supplies the
    ground defeasible rules that argument construction consumes.
    """

    from propstore.aspic_bridge import build_aspic_projection

    sig = inspect.signature(build_aspic_projection)
    assert "bundle" in sig.parameters, (
        "build_aspic_projection must accept a "
        "`bundle: GroundedRulesBundle | None` parameter. Current "
        f"parameters: {list(sig.parameters)}"
    )


def test_query_claim_threads_grounded_rules() -> None:
    """``query_claim`` must accept a ``GroundedRulesBundle``.

    Modgil & Prakken 2018 Def 5 (pp.9-10) and Def 10 (p.13):
    goal-directed argument construction backward-chains from a
    literal to premises; the rule set it chains over must include
    the ground defeasible rules from the bundle. 1.8b wires the
    bundle through so ``query_claim('flies(tweety)', ..., bundle=b)``
    can reach ``bird(tweety)`` via the ground instance of
    ``flies(X) -< bird(X)``.
    """

    from propstore.aspic_bridge import query_claim

    sig = inspect.signature(query_claim)
    assert "bundle" in sig.parameters, (
        "query_claim must accept a `bundle: GroundedRulesBundle | None` "
        f"parameter. Current parameters: {list(sig.parameters)}"
    )


# ── Primary end-to-end test: tweety via query_claim ────────────────


def test_tweety_end_to_end_via_query_claim() -> None:
    """End-to-end Phase-1 proof: concept graph → grounder → ASPIC+ argument.

    Garcia & Simari 2004 §3 (p.3-4): the canonical DeLP textbook
    example. Given the fact base ``{bird(tweety)}`` and the
    defeasible rule ``flies(X) -< bird(X)``, the ground program
    derives ``flies(tweety)`` by a single defeasible rule
    application. Modgil & Prakken 2018 Def 5 (pp.9-10) formalises
    the same step in ASPIC+: one DefeasibleArg whose conclusion is
    ``Literal(GroundAtom('flies', ('tweety',)))`` and whose
    sub-argument is a PremiseArg for ``bird(tweety)``.

    Pipeline:
        1. Build concept graph, predicate registry, and rule files
           via the inline helpers above.
        2. ``extract_facts(concepts, registry)`` -> ``(bird(tweety),)``.
        3. ``ground(rule_files, facts, registry)`` -> bundle whose
           ``definitely`` section contains ``{'bird': {('tweety',)}}``
           and whose ``defeasibly`` section contains
           ``{'flies': {('tweety',)}}``.
        4. ``query_claim('flies(tweety)', active_claims=[],
           justifications=[], stances=[], bundle=bundle)`` returns a
           ``ClaimQueryResult`` with exactly one argument supporting
           the queried literal.
        5. The argument's conclusion equals
           ``Literal(GroundAtom('flies', ('tweety',)))``.
        6. The argument is a ``DefeasibleArg`` (Modgil & Prakken
           2018 Def 5 clause 3, p.10).
        7. The rule name encodes the substitution
           ``X=tweety`` — unique per Modgil & Prakken 2018 Def 2
           (p.8) n(r) requirement.

    Red until 1.8b: ``query_claim`` does not accept ``bundle``
    today; the call raises ``TypeError`` at step 4.
    """

    from propstore.aspic import DefeasibleArg, GroundAtom, Literal, conc
    from propstore.aspic_bridge import query_claim
    from propstore.grounding.facts import extract_facts
    from propstore.grounding.grounder import ground

    concepts, registry, rule_files = _build_tweety_world()

    facts = extract_facts(concepts, registry)
    # Garcia & Simari 2004 §3: the fact extractor must materialise
    # exactly ``bird(tweety)``.
    assert len(facts) == 1
    assert facts[0] == GroundAtom(predicate="bird", arguments=("tweety",))

    bundle = ground(rule_files, facts, registry)
    # Diller, Borg, Bex 2025 §3: the bundle must carry the four
    # sections; the definitely section echoes the input facts and the
    # defeasibly section contains the ground rule head.
    assert ("tweety",) in bundle.sections["definitely"].get(
        "bird", frozenset()
    )
    assert ("tweety",) in bundle.sections["defeasibly"].get(
        "flies", frozenset()
    )

    # The query literal key matches ``repr(GroundAtom('flies',
    # ('tweety',)))`` -> ``"flies(tweety)"``. See
    # ``propstore/aspic_bridge.py:_literal_for_atom`` for the
    # canonical keying rule.
    result = query_claim(
        "flies(tweety)",
        active_claims=[],
        justifications=[],
        stances=[],
        bundle=bundle,
    )

    expected_goal = Literal(
        atom=GroundAtom(predicate="flies", arguments=("tweety",)),
        negated=False,
    )
    assert result.goal == expected_goal

    # Modgil & Prakken 2018 Def 5 clause 3 (p.10): exactly one
    # defeasible argument supports the goal in this single-rule,
    # single-fact world.
    assert len(result.arguments_for) == 1
    (argument,) = tuple(result.arguments_for)
    assert conc(argument) == expected_goal
    assert isinstance(argument, DefeasibleArg)

    # Modgil & Prakken 2018 Def 2 (p.8): the defeasible-rule name
    # n(r) must be unique per ground instance. The grounder bridge now
    # encodes the substitution structurally after ``<rule_id>#`` so
    # delimiter characters inside constants cannot collide.
    assert argument.rule.name.startswith('r_flies_bird#{"X":')
    assert '"type":"str"' in argument.rule.name
    assert '"value":"tweety"' in argument.rule.name

    # No attackers in this world: ``arguments_against`` is empty.
    assert result.arguments_against == frozenset()


# ── Supporting tests ───────────────────────────────────────────────


def test_tweety_no_rules_produces_no_grounded_arguments() -> None:
    """Empty rule file pins the zero-rules edge case.

    Same fact base as the primary test (one concept with an
    ``is_a:Bird`` edge) but zero rules in the rule file. Diller, Borg,
    Bex 2025 §3 Def 7: the empty Datalog program is legal and
    produces only the input fact base. Garcia & Simari 2004 §3
    treats an empty rule set as a trivial program; no defeasible
    conclusions are derivable.

    Expected bundle shape:
        - ``definitely['bird']`` still contains ``('tweety',)``
          (facts are preserved).
        - ``defeasibly`` contains no entry for ``flies``.

    Expected query result: ``query_claim('flies(tweety)', ...,
    bundle=bundle)`` yields an empty ``arguments_for`` set because
    there is no rule to back-chain from. Modgil & Prakken 2018
    Def 5 (pp.9-10): argument construction requires a rule whose
    conclusion matches the goal; no rule, no argument.

    Red until 1.8b: the ``bundle`` keyword does not exist on
    ``query_claim`` yet — ``TypeError`` at call time.
    """

    from propstore.aspic import GroundAtom
    from propstore.aspic_bridge import query_claim
    from propstore.grounding.facts import extract_facts
    from propstore.grounding.grounder import ground

    concepts, registry, _original_rule_files = _build_tweety_world()
    # Rebuild the rule file with zero rules; all other inputs are
    # identical to the canonical tweety setup.
    empty_rule_files = [_build_rule_file([])]

    facts = extract_facts(concepts, registry)
    bundle = ground(empty_rule_files, facts, registry)

    # Facts are still present: Diller, Borg, Bex 2025 §3 Def 7.
    assert ("tweety",) in bundle.sections["definitely"].get(
        "bird", frozenset()
    )
    # No derived ``flies`` entry — the defeasibly section has no
    # row for a predicate that no rule references.
    assert bundle.sections["defeasibly"].get("flies", frozenset()) == frozenset()

    # Querying a literal with no supporting rule yields no
    # arguments. Garcia & Simari 2004 §3: an empty rule set has no
    # defeasible derivations.
    _unused = GroundAtom  # silence unused-import in red state
    result = query_claim(
        "flies(tweety)",
        active_claims=[],
        justifications=[],
        stances=[],
        bundle=bundle,
    )
    assert result.arguments_for == frozenset()


def test_tweety_multiple_birds_produces_multiple_arguments() -> None:
    """Two birds → two ground rule instances → two defeasible arguments.

    Garcia & Simari 2004 §3.1 (p.4): the ground instances of a
    defeasible rule are obtained by substituting each variable with
    every constant drawn from the Herbrand base. With two concepts
    (``tweety``, ``opus``) each ``is_a:Bird``, the fact base contains
    ``{bird(tweety), bird(opus)}`` and the ground rule set contains
    both ``flies(tweety) -< bird(tweety)`` and
    ``flies(opus) -< bird(opus)``. Modgil & Prakken 2018 Def 5
    (pp.9-10) then builds one DefeasibleArg per ground rule.

    Expected projection via ``build_aspic_projection`` (or the CSAF
    built by ``build_bridge_csaf``): two defeasible arguments, one
    whose conclusion is ``flies(tweety)`` and one whose conclusion is
    ``flies(opus)``.

    Red until 1.8b: ``build_bridge_csaf`` does not accept a
    ``bundle`` keyword today.
    """

    from propstore.aspic import DefeasibleArg, GroundAtom, Literal, conc
    from propstore.aspic_bridge import build_bridge_csaf
    from propstore.grounding.facts import extract_facts
    from propstore.grounding.grounder import ground

    _bird_root = _build_loaded_concept("Bird", ())
    tweety = _build_loaded_concept(
        "tweety",
        [_build_concept_relationship("is_a", "Bird")],
    )
    opus = _build_loaded_concept(
        "opus",
        [_build_concept_relationship("is_a", "Bird")],
    )
    concepts = [_bird_root, tweety, opus]

    bird_predicate = _build_predicate_document(
        predicate_id="bird",
        arity=1,
        arg_types=("Bird",),
        derived_from="concept.relation:is_a:Bird",
    )
    flies_predicate = _build_predicate_document(
        predicate_id="flies",
        arity=1,
        arg_types=("Bird",),
        derived_from=None,
    )
    registry = _build_registry([bird_predicate, flies_predicate])

    variable_x = _build_var("X")
    rule = _build_defeasible_rule(
        "r_flies_bird",
        _build_atom("flies", [variable_x]),
        [_build_atom("bird", [variable_x])],
    )
    rule_files = [_build_rule_file([rule])]

    facts = extract_facts(concepts, registry)
    # Both birds show up as facts (deterministic sorted order —
    # Diller, Borg, Bex 2025 §3 Def 9).
    assert GroundAtom(predicate="bird", arguments=("opus",)) in facts
    assert GroundAtom(predicate="bird", arguments=("tweety",)) in facts

    bundle = ground(rule_files, facts, registry)
    flies_rows = bundle.sections["defeasibly"].get("flies", frozenset())
    assert ("tweety",) in flies_rows
    assert ("opus",) in flies_rows

    csaf = build_bridge_csaf(
        active_claims=[],
        justifications=[],
        stances=[],
        bundle=bundle,
    )

    flies_tweety = Literal(
        atom=GroundAtom(predicate="flies", arguments=("tweety",)),
        negated=False,
    )
    flies_opus = Literal(
        atom=GroundAtom(predicate="flies", arguments=("opus",)),
        negated=False,
    )
    conclusions = {conc(arg) for arg in csaf.arguments}
    assert flies_tweety in conclusions
    assert flies_opus in conclusions

    defeasible_for_tweety = [
        arg
        for arg in csaf.arguments
        if isinstance(arg, DefeasibleArg) and conc(arg) == flies_tweety
    ]
    defeasible_for_opus = [
        arg
        for arg in csaf.arguments
        if isinstance(arg, DefeasibleArg) and conc(arg) == flies_opus
    ]
    # Exactly one defeasible argument per ground rule instance —
    # Garcia & Simari 2004 §3.1 ground-instance uniqueness; Modgil &
    # Prakken 2018 Def 5 clause 3 (p.10).
    assert len(defeasible_for_tweety) == 1
    assert len(defeasible_for_opus) == 1


def test_tweety_rule_body_fact_missing_produces_zero_arguments() -> None:
    """Rule body unsatisfied by the fact base → no ground instances → no arguments.

    Garcia & Simari 2004 §3.1 (p.4): grounding enumerates over the
    Herbrand base. When a rule body atom has no matching fact, the
    substitution set is empty and no ground rule is emitted. Diller,
    Borg, Bex 2025 §3 Def 9: the substitution set is a function of
    program plus fact base — an empty fact base for the relevant
    predicate yields an empty substitution set.

    Setup:
        - Concept ``fido`` with ``is_a:Mammal`` (no ``Bird`` edge).
        - Predicate ``bird/1`` derived from ``is_a:Bird``.
        - Rule ``flies(X) -< bird(X)``.
    Expected: zero ``bird/...`` facts, zero ground instances of
    ``flies``, zero defeasible arguments.

    Red until 1.8b: ``build_bridge_csaf`` does not accept ``bundle``
    yet.
    """

    from propstore.aspic import DefeasibleArg
    from propstore.aspic_bridge import build_bridge_csaf
    from propstore.grounding.facts import extract_facts
    from propstore.grounding.grounder import ground

    fido = _build_loaded_concept(
        "fido",
        [_build_concept_relationship("is_a", "Mammal")],
    )
    concepts = [fido]

    bird_predicate = _build_predicate_document(
        predicate_id="bird",
        arity=1,
        arg_types=("Bird",),
        derived_from="concept.relation:is_a:Bird",
    )
    flies_predicate = _build_predicate_document(
        predicate_id="flies",
        arity=1,
        arg_types=("Bird",),
        derived_from=None,
    )
    registry = _build_registry([bird_predicate, flies_predicate])

    variable_x = _build_var("X")
    rule = _build_defeasible_rule(
        "r_flies_bird",
        _build_atom("flies", [variable_x]),
        [_build_atom("bird", [variable_x])],
    )
    rule_files = [_build_rule_file([rule])]

    facts = extract_facts(concepts, registry)
    # No fact matches ``is_a:Bird`` — Diller, Borg, Bex 2025 §3 Def 7:
    # the empty fact base is legal.
    assert facts == ()

    bundle = ground(rule_files, facts, registry)
    # The defeasibly section has no ``flies`` entry because there is
    # nothing to substitute ``X`` with.
    assert bundle.sections["defeasibly"].get("flies", frozenset()) == frozenset()

    csaf = build_bridge_csaf(
        active_claims=[],
        justifications=[],
        stances=[],
        bundle=bundle,
    )

    # Modgil & Prakken 2018 Def 5 (pp.9-10): without a usable
    # defeasible rule, no DefeasibleArg can be constructed.
    defeasible_args = [
        arg for arg in csaf.arguments if isinstance(arg, DefeasibleArg)
    ]
    assert defeasible_args == []


# End of test module. The red-state behaviour across all seven tests
# above pins the missing 1.8b integration point: every test either
# raises ``TypeError`` (on ``bundle=`` not being accepted) or fails
# an inspect-based signature assertion.
