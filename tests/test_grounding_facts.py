"""Tests for the propstore concept-graph -> Datalog fact extractor.

These tests describe the contract for the Phase-1 fact extractor that
will live in ``propstore/grounding/facts.py``. The module does not
exist yet — every import is deferred (into strategy bodies and test
bodies) so pytest can collect this file cleanly while every test fails
at run time with ``ModuleNotFoundError: No module named
'propstore.grounding.facts'``.

Concept-graph data structure (verified by reading
``propstore/core/concepts.py`` and ``propstore/sidecar/build.py``):

    The propstore concept graph is a flat sequence of ``LoadedConcept``
    envelopes — exactly what ``load_concepts(knowledge_root /
    "concepts")`` returns and what ``sidecar/build.py`` passes around.
    Each ``LoadedConcept`` wraps a frozen ``ConceptRecord`` whose
    ``relationships`` field is a ``tuple[ConceptRelationship, ...]``.
    Each ``ConceptRelationship`` is a frozen dataclass with
    ``relationship_type: str`` (the relation name, e.g. ``"is_a"``),
    ``target: ConceptId`` (a NewType-wrapped string identifying the
    target concept, e.g. ``ConceptId("Bird")``), an optional tuple of
    condition strings, and an optional note. Relationships are
    *outgoing* edges from the source concept (``concept_record``) to
    the target concept identified by the ``target`` string. The Phase-1
    extractor walks every relationship on every loaded concept,
    matches the ``relationship_type`` and ``target`` against each
    predicate's parsed ``DerivedFromSpec`` (kind ==
    ``"concept_relation"``), and emits one ``GroundAtom`` per matching
    edge whose single argument is the source concept's
    ``canonical_name`` (the user-facing token like ``"tweety"`` from
    Garcia & Simari 2004 §3).

Theoretical sources:
    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (p.3): a Datalog program's fact base is a set of
      ground atoms ``p(c_1,...,c_n)`` whose terms are constants drawn
      from the underlying domain. The grounding pipeline produces this
      fact base from external data via a deterministic, total
      function: same inputs, same outputs, no side effects.
    - Section 3 (Definition 9): ground substitutions are produced as a
      function of the program and its fact base; the substitution set
      is therefore stable across repeated runs.
    - Section 4: every ground atom must reference a declared predicate
      and respect the declared arity; the extractor cannot invent
      predicates.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): the unary ``bird/1`` predicate is the
      canonical defeasible-reasoning toy example; ``bird(tweety)`` is
      the ground literal derived from a fact base entry asserting that
      tweety is a bird.
    - Section 3.1: the ground instances of a program are obtained by
      replacing each variable in a rule head/body with a constant
      drawn from the Herbrand base — the fact base supplies those
      constants.
    - Section 3.2: rule heads and bodies are atoms whose term-tuple
      length must equal the declared predicate arity for grounding to
      be well-defined.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


# ── Hypothesis strategies ───────────────────────────────────────────
#
# Strategies live in this file per the chunk constraint: no conftest.py,
# no shared helper module. Imports of propstore types are deferred into
# strategy bodies so the file collects without
# ``propstore.grounding.facts``.


_CONCEPT_NAMES = st.sampled_from(
    ["tweety", "opus", "polly", "rocky", "sammy"]
)
_RELATION_NAMES = st.sampled_from(["is_a", "part_of", "kind_of"])
_TARGET_NAMES = st.sampled_from(["Bird", "Penguin", "Mammal"])


def _build_concept_record(canonical_name: str, relationships):
    """Construct a minimal ``ConceptRecord`` for one concept.

    Diller et al. 2025 §3 treats the concept graph as the source of
    ground atoms; the extractor only reads the canonical name and
    relationships, so this helper supplies just enough additional
    fields to satisfy ``ConceptRecord``'s frozen-dataclass invariants
    without invoking the heavier ``parse_concept_record`` normaliser.
    """

    from propstore.core.concepts import ConceptRecord
    from propstore.core.id_types import to_concept_id
    from propstore.core.id_types import LogicalId

    artifact_id = to_concept_id(f"ps:concept:{canonical_name}")
    logical_id = LogicalId(namespace="propstore", value=canonical_name)
    return ConceptRecord(
        artifact_id=artifact_id,
        canonical_name=canonical_name,
        status="active",
        definition=f"Test concept named {canonical_name}.",
        form="Entity",
        logical_ids=(logical_id,),
        version_id=f"v-{canonical_name}",
        relationships=tuple(relationships),
    )


def _build_loaded_concept(canonical_name: str, relationships):
    """Wrap a ConceptRecord in a LoadedConcept envelope.

    ``sidecar/build.py`` consumes ``Sequence[LoadedConcept]`` from
    ``load_concepts``; the extractor must accept the same shape.
    """

    from propstore.core.concepts import LoadedConcept

    record = _build_concept_record(canonical_name, relationships)
    return LoadedConcept(
        filename=f"{canonical_name}.yaml",
        source_path=None,
        knowledge_root=None,
        record=record,
    )


def _build_concept_relationship(relation: str, target: str):
    """Build a single outgoing concept relationship.

    Mirrors the shape produced by ``parse_concept_record`` for entries
    in a concept's ``relationships`` block (Garcia & Simari 2004 §3.1
    treats these as the ground-fact-bearing edges of the concept
    graph).
    """

    from propstore.core.concepts import ConceptRelationship
    from propstore.core.id_types import to_concept_id

    return ConceptRelationship(
        relationship_type=relation,
        target=to_concept_id(target),
        conditions=(),
        note=None,
    )


def _build_predicate_document(
    predicate_id: str,
    arity: int,
    arg_types,
    derived_from,
):
    """Construct a ``PredicateDocument`` with the supplied fields."""

    from propstore.artifacts.documents.predicates import PredicateDocument

    return PredicateDocument(
        id=predicate_id,
        arity=arity,
        arg_types=tuple(arg_types),
        derived_from=derived_from,
        description=None,
    )


def _build_registry(predicates):
    """Wrap predicate documents in a populated PredicateRegistry."""

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


def concept_relationship_graphs() -> st.SearchStrategy:
    """Strategy producing small concept relationship graphs.

    Each element is a ``Sequence[LoadedConcept]``, mirroring the shape
    that ``propstore.core.concepts.load_concepts`` produces and that
    ``propstore.sidecar.build`` passes through the build pipeline.
    Each generated concept carries zero or more outgoing
    ``ConceptRelationship`` edges drawn from a small fixed pool of
    relation names and target tokens (Garcia & Simari 2004 §3:
    ``is_a:Bird`` is the canonical defeasible-reasoning example).
    Concept canonical_names are unique per draw so the resulting
    LoadedConcept sequence has no duplicate sources.
    """

    @st.composite
    def _build(draw):
        names = draw(
            st.lists(
                _CONCEPT_NAMES,
                min_size=0,
                max_size=5,
                unique=True,
            )
        )
        concepts = []
        for name in names:
            edge_count = draw(st.integers(min_value=0, max_value=3))
            edges = []
            for _ in range(edge_count):
                relation = draw(_RELATION_NAMES)
                target = draw(_TARGET_NAMES)
                edges.append(_build_concept_relationship(relation, target))
            concepts.append(_build_loaded_concept(name, edges))
        return concepts

    return _build()


def predicate_registries_with_is_a_derivations() -> st.SearchStrategy:
    """Strategy producing PredicateRegistry instances with at least one
    ``concept.relation:is_a:<target>`` derivation.

    Diller et al. 2025 §3 fixes the ``derived_from`` DSL as the only
    sanctioned bridge between propstore data and the Datalog fact
    base; this strategy guarantees every drawn registry exposes at
    least one ``is_a`` derivation so the extractor has something to do.
    Predicate ids are unique per draw so the registry build does not
    raise ``DuplicatePredicateError``.
    """

    @st.composite
    def _build(draw):
        targets = draw(
            st.lists(_TARGET_NAMES, min_size=1, max_size=3, unique=True)
        )
        docs = []
        for index, target in enumerate(targets):
            predicate_id = f"{target.lower()}_{index}"
            docs.append(
                _build_predicate_document(
                    predicate_id=predicate_id,
                    arity=1,
                    arg_types=("Concept",),
                    derived_from=f"concept.relation:is_a:{target}",
                )
            )
        # Optionally add a non-derived predicate to verify the extractor
        # ignores predicates without a derived_from.
        if draw(st.booleans()):
            docs.append(
                _build_predicate_document(
                    predicate_id="undeclared_source",
                    arity=0,
                    arg_types=(),
                    derived_from=None,
                )
            )
        return _build_registry(docs)

    return _build()


# ── Property tests ─────────────────────────────────────────────────


@given(
    graph=st.deferred(concept_relationship_graphs),
    registry=st.deferred(predicate_registries_with_is_a_derivations),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_extract_facts_idempotent(graph, registry) -> None:
    """``extract_facts(X, R) == extract_facts(X, R)``.

    Fact extraction must be a pure function of its inputs (Diller,
    Borg, Bex 2025 §3, Definition 9: the ground substitution set is a
    function of the program and the fact base — same inputs, same
    outputs, no side effects). Garcia & Simari 2004 §3.1 makes the
    same point at the Herbrand-base level.
    """

    from propstore.grounding.facts import extract_facts

    first = extract_facts(graph, registry)
    second = extract_facts(graph, registry)
    assert first == second


@given(
    graph=st.deferred(concept_relationship_graphs),
    registry=st.deferred(predicate_registries_with_is_a_derivations),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_extracted_facts_match_registry_arity(graph, registry) -> None:
    """Every emitted ``GroundAtom`` has arity matching its declared
    predicate signature.

    Diller et al. 2025 §3 (Definition 7) and §4: a Datalog ground atom
    is ``p(t_1,...,t_n)`` where ``n`` is the predicate's declared
    arity; arity mismatches are schema errors. Garcia & Simari 2004
    §3.2 enforces the same invariant on the Herbrand base.
    """

    from propstore.grounding.facts import extract_facts

    atoms = extract_facts(graph, registry)
    for atom in atoms:
        declaration = registry.lookup(atom.predicate)
        assert len(atom.arguments) == declaration.arity


@given(
    graph=st.deferred(concept_relationship_graphs),
    registry=st.deferred(predicate_registries_with_is_a_derivations),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_extracted_facts_reference_registered_predicates(
    graph, registry
) -> None:
    """Every emitted ``GroundAtom``'s predicate name is in the registry.

    Diller et al. 2025 §3-§4: the extractor only materialises ground
    atoms for predicates that the Datalog schema already declares; it
    cannot invent predicate symbols. Garcia & Simari 2004 §3.2 makes
    the same point — an undeclared predicate has no signature and
    therefore no Herbrand semantics.
    """

    from propstore.grounding.facts import extract_facts

    atoms = extract_facts(graph, registry)
    declared_ids = {p.id for p in registry.all_predicates()}
    for atom in atoms:
        assert atom.predicate in declared_ids


@given(
    graph=st.deferred(concept_relationship_graphs),
    registry=st.deferred(predicate_registries_with_is_a_derivations),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_extract_facts_no_duplicates(graph, registry) -> None:
    """``extract_facts`` returns each ``GroundAtom`` at most once.

    Diller et al. 2025 §3 (Definition 7): the Datalog fact base is a
    *set* of ground atoms — duplicate entries are semantically
    redundant. Garcia & Simari 2004 §3.1 likewise treats the ground
    instances as a set. The same ``(C, is_a, Bird)`` edge contributes
    one ``bird(C)`` atom, not multiple, regardless of how the
    extractor walks the graph.
    """

    from propstore.grounding.facts import extract_facts

    atoms = extract_facts(graph, registry)
    assert len(atoms) == len(set(atoms))


@given(
    graph=st.deferred(concept_relationship_graphs),
    registry=st.deferred(predicate_registries_with_is_a_derivations),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_extract_facts_returns_tuple(graph, registry) -> None:
    """``extract_facts`` returns a tuple of ``GroundAtom`` instances.

    Diller et al. 2025 §3: the Datalog fact base is a finite, ordered
    collection of ground atoms; downstream consumers (the gunray
    translator and the sidecar populate stage) consume an immutable
    tuple. Returning a list or generator would break their stable-order
    guarantees.
    """

    from argumentation.aspic import GroundAtom
    from propstore.grounding.facts import extract_facts

    atoms = extract_facts(graph, registry)
    assert isinstance(atoms, tuple)
    for atom in atoms:
        assert isinstance(atom, GroundAtom)


# ── Concrete example tests ─────────────────────────────────────────


def test_extract_facts_concept_relation_is_a_minimal() -> None:
    """Concrete example: one concept, one relationship, one predicate.

    Garcia & Simari 2004 §3 (p.3-4): ``bird(tweety)`` is the canonical
    ground literal derived from the fact base. Given a graph with a
    single ``(tweety, is_a, Bird)`` edge and a registry declaring
    ``bird`` with ``derived_from='concept.relation:is_a:Bird'``,
    ``extract_facts`` must return exactly
    ``(GroundAtom('bird', ('tweety',)),)`` — Diller et al. 2025 §3
    Definition 7 fixes the ``p(t_1,...,t_n)`` shape this asserts.
    """

    from argumentation.aspic import GroundAtom
    from propstore.grounding.facts import extract_facts

    concept = _build_loaded_concept(
        "tweety",
        [_build_concept_relationship("is_a", "Bird")],
    )
    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="bird",
                arity=1,
                arg_types=("Concept",),
                derived_from="concept.relation:is_a:Bird",
            )
        ]
    )

    atoms = extract_facts([concept], registry)
    assert atoms == (GroundAtom("bird", ("tweety",)),)


def test_extract_facts_multiple_concepts_same_predicate() -> None:
    """Multiple concepts sharing an ``is_a`` target produce ground atoms
    for the same predicate.

    Garcia & Simari 2004 §3.1: the ground instances of a program enum
    every constant whose Herbrand-base entry satisfies the rule body.
    Given ``{(tweety, is_a, Bird), (opus, is_a, Bird)}`` and predicate
    ``bird`` derived from ``concept.relation:is_a:Bird``,
    ``extract_facts`` must return both ``bird(tweety)`` and
    ``bird(opus)``. Order is asserted as a set so this test does not
    over-specify the deterministic ordering tested elsewhere.
    """

    from argumentation.aspic import GroundAtom
    from propstore.grounding.facts import extract_facts

    concepts = [
        _build_loaded_concept(
            "tweety",
            [_build_concept_relationship("is_a", "Bird")],
        ),
        _build_loaded_concept(
            "opus",
            [_build_concept_relationship("is_a", "Bird")],
        ),
    ]
    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="bird",
                arity=1,
                arg_types=("Concept",),
                derived_from="concept.relation:is_a:Bird",
            )
        ]
    )

    atoms = extract_facts(concepts, registry)
    assert set(atoms) == {
        GroundAtom("bird", ("tweety",)),
        GroundAtom("bird", ("opus",)),
    }


def test_extract_facts_unmatched_relation_produces_nothing() -> None:
    """A graph with no matching ``derived_from`` target produces no atoms.

    Diller et al. 2025 §3: the extractor only materialises atoms when
    the concept-relation target matches the predicate's declared
    target. Given ``{(tweety, is_a, Mammal)}`` and predicate ``bird``
    derived from ``concept.relation:is_a:Bird``, ``extract_facts``
    returns an empty tuple — no other predicate is declared, so no
    atoms exist. Garcia & Simari 2004 §3.1 makes the same point: the
    Herbrand base only includes constants reachable from the rule body.
    """

    from propstore.grounding.facts import extract_facts

    concept = _build_loaded_concept(
        "tweety",
        [_build_concept_relationship("is_a", "Mammal")],
    )
    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="bird",
                arity=1,
                arg_types=("Concept",),
                derived_from="concept.relation:is_a:Bird",
            )
        ]
    )

    atoms = extract_facts([concept], registry)
    assert atoms == ()


def test_extract_facts_unmatched_relation_name_produces_nothing() -> None:
    """A graph with the right target but the wrong relation name
    produces no atoms.

    Diller et al. 2025 §3 fixes both the relation name *and* the
    target as discriminants of the ``concept.relation`` DSL form;
    matching only the target would silently merge unrelated edges into
    the same predicate. Given ``{(tweety, kind_of, Bird)}`` and
    predicate ``bird`` derived from ``concept.relation:is_a:Bird``,
    ``extract_facts`` returns an empty tuple.
    """

    from propstore.grounding.facts import extract_facts

    concept = _build_loaded_concept(
        "tweety",
        [_build_concept_relationship("kind_of", "Bird")],
    )
    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="bird",
                arity=1,
                arg_types=("Concept",),
                derived_from="concept.relation:is_a:Bird",
            )
        ]
    )

    atoms = extract_facts([concept], registry)
    assert atoms == ()


def test_extract_facts_empty_graph_empty_result() -> None:
    """Empty concept graph produces an empty tuple.

    Diller et al. 2025 §3: with an empty fact base the Datalog ground
    instance set is empty regardless of the program; Garcia & Simari
    2004 §3.1 makes the same observation about the Herbrand base.
    """

    from propstore.grounding.facts import extract_facts

    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="bird",
                arity=1,
                arg_types=("Concept",),
                derived_from="concept.relation:is_a:Bird",
            )
        ]
    )

    atoms = extract_facts([], registry)
    assert atoms == ()


def test_extract_facts_no_derived_from_predicates_empty_result() -> None:
    """A registry with no ``derived_from`` declarations produces an
    empty tuple regardless of the concept graph.

    Diller et al. 2025 §3: the ``derived_from`` DSL is the *only*
    sanctioned bridge from propstore data into the Datalog fact base.
    Without any declarations, nothing tells the extractor where to
    look. Garcia & Simari 2004 §3 admits no other extension points.
    """

    from propstore.grounding.facts import extract_facts

    concepts = [
        _build_loaded_concept(
            "tweety",
            [_build_concept_relationship("is_a", "Bird")],
        ),
        _build_loaded_concept(
            "opus",
            [_build_concept_relationship("is_a", "Bird")],
        ),
    ]
    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="bird",
                arity=1,
                arg_types=("Concept",),
                derived_from=None,
            )
        ]
    )

    atoms = extract_facts(concepts, registry)
    assert atoms == ()


def test_extract_facts_ignores_non_is_a_derivations() -> None:
    """Phase 1 supports only ``concept.relation:is_a:X``.

    Predicates declared with ``claim.attribute:X`` or
    ``claim.condition:X`` produce no facts — they belong to later
    phases (Diller et al. 2025 §4 lists all three sanctioned source
    kinds; Garcia & Simari 2004 §3 supplies the canonical examples).
    The extractor must not raise on the unsupported kinds; it just
    returns nothing for them. **When Phase 2 lands and these kinds
    start producing facts, this test will start failing — that
    failure is the deliberate signal to extend the extractor and
    update this expectation.**
    """

    from propstore.grounding.facts import extract_facts

    concept = _build_loaded_concept(
        "tweety",
        [_build_concept_relationship("is_a", "Bird")],
    )
    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="is_bird_attr",
                arity=0,
                arg_types=(),
                derived_from="claim.attribute:is_bird",
            ),
            _build_predicate_document(
                predicate_id="tweety_present",
                arity=0,
                arg_types=(),
                derived_from="claim.condition:tweety_present",
            ),
        ]
    )

    atoms = extract_facts([concept], registry)
    assert atoms == ()


def test_extract_facts_deterministic_order() -> None:
    """Fact extraction is deterministic across repeated runs.

    Diller et al. 2025 §3 (Definition 9): ground substitutions are a
    function of the program and the fact base. Garcia & Simari 2004
    §3.1 makes the same point. Downstream consumers (the gunray
    translator and the sidecar populate stage) rely on stable
    ordering for reproducible builds — running ``extract_facts``
    twice on the same input must return tuples in the same order.
    """

    from propstore.grounding.facts import extract_facts

    concepts = [
        _build_loaded_concept(
            "tweety",
            [_build_concept_relationship("is_a", "Bird")],
        ),
        _build_loaded_concept(
            "opus",
            [_build_concept_relationship("is_a", "Bird")],
        ),
        _build_loaded_concept(
            "polly",
            [_build_concept_relationship("is_a", "Bird")],
        ),
    ]
    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="bird",
                arity=1,
                arg_types=("Concept",),
                derived_from="concept.relation:is_a:Bird",
            )
        ]
    )

    first = extract_facts(concepts, registry)
    second = extract_facts(concepts, registry)
    third = extract_facts(concepts, registry)
    assert first == second == third


def test_extract_facts_mixed_derived_from_only_emits_supported() -> None:
    """A registry mixing supported and unsupported ``derived_from``
    forms emits facts only for the supported ones.

    Diller et al. 2025 §3 lists three sanctioned source kinds; Phase 1
    only implements ``concept_relation``. Garcia & Simari 2004 §3.2:
    rule bodies that reference unsupported predicates contribute
    nothing to the Herbrand base. The extractor must not raise on the
    unsupported kinds and must still emit facts for the supported
    ones from the same graph.
    """

    from argumentation.aspic import GroundAtom
    from propstore.grounding.facts import extract_facts

    concept = _build_loaded_concept(
        "tweety",
        [_build_concept_relationship("is_a", "Bird")],
    )
    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="bird",
                arity=1,
                arg_types=("Concept",),
                derived_from="concept.relation:is_a:Bird",
            ),
            _build_predicate_document(
                predicate_id="is_bird_attr",
                arity=0,
                arg_types=(),
                derived_from="claim.attribute:is_bird",
            ),
        ]
    )

    atoms = extract_facts([concept], registry)
    assert atoms == (GroundAtom("bird", ("tweety",)),)


def test_extract_facts_rejects_non_unary_concept_relation_predicate() -> None:
    """``concept.relation`` facts must respect the declared predicate arity.

    The current extractor materialises a single source-concept constant for
    each matching relation edge. If a predicate declaration claims the same
    ``derived_from`` surface but an arity other than 1, the extractor must fail
    loudly instead of emitting a wrong-shaped ground atom.
    """

    from propstore.grounding.facts import extract_facts
    from propstore.grounding.predicates import PredicateArityMismatchError

    concept = _build_loaded_concept(
        "tweety",
        [_build_concept_relationship("is_a", "Bird")],
    )
    registry = _build_registry(
        [
            _build_predicate_document(
                predicate_id="bird_pair",
                arity=2,
                arg_types=("Concept", "Concept"),
                derived_from="concept.relation:is_a:Bird",
            )
        ]
    )

    with pytest.raises(PredicateArityMismatchError):
        extract_facts([concept], registry)
