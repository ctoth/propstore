"""Property tests for PredicateRegistry and the ``derived_from`` DSL parser.

These tests describe the contract for the registry layer that will live
in ``propstore/grounding/predicates.py``. Neither the package nor the
module exists yet — every import is deferred into a strategy or test
body so pytest can collect this file cleanly while every test fails at
run time with ``ModuleNotFoundError``.

Theoretical sources:
    Diller, M. et al. (2025). Grounding Rule-Based Argumentation Using
    Datalog.
    - Section 3: a Datalog program is a set of declared predicates with
      typed argument vectors plus rules over those predicates. The
      registry layer materialises that declaration set so the grounder
      can validate atom shapes against the schema.
    - Section 4: the grounding step rejects atoms whose arity does not
      match the registered predicate signature; mismatched calls are not
      part of the Herbrand base.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3.2: predicates carry a fixed arity; rule heads and bodies
      are atoms whose term-tuple length must equal that arity for
      grounding to be well-defined.

The DSL surface ``parse_derived_from`` lifts a string of one of three
shapes into a typed ``DerivedFromSpec`` value:

    ``concept.relation:<relation>:<target>``  → kind="concept_relation"
    ``claim.attribute:<attribute>``           → kind="claim_attribute"
    ``claim.condition:<condition>``           → kind="claim_condition"

The exact dataclass shape is left to the implementation; these tests
only constrain the parsed ``kind`` discriminator and the round-trip
behaviour for the canonical examples.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st


# ── Hypothesis strategies ───────────────────────────────────────────
#
# Strategies live in this file per the chunk constraint: no conftest.py,
# no shared helper module. Imports are deferred into strategy bodies so
# the file collects without ``propstore.grounding.predicates``.


_PREDICATE_ID_HEAD = st.sampled_from(
    [
        "bird",
        "flies",
        "penguin",
        "raining",
        "is_a",
        "feathered",
        "supports",
        "attacks",
    ]
)
_PREDICATE_ID_NAMESPACE = st.sampled_from(["", "delp", "diller", "core", "test"])
_ARG_TYPE_NAMES = st.sampled_from(
    [
        "Bird",
        "Penguin",
        "Animal",
        "Person",
        "Claim",
        "Concept",
        "String",
        "Number",
    ]
)
_DERIVED_FROM_FORMS = st.sampled_from(
    [
        None,
        "concept.relation:is_a:Bird",
        "concept.relation:part_of:Wheel",
        "claim.attribute:is_bird",
        "claim.condition:tweety_present",
    ]
)


def _make_predicate_id(namespace: str, head: str, salt: int) -> str:
    """Stable id constructor used by the predicate strategy.

    Diller et al. 2025 §3 treats predicate identifiers opaquely; the
    integer salt makes Hypothesis able to generate enough distinct ids
    for ``unique_by`` filters in registry-shaped tests.
    """

    base = f"{head}_{salt}" if salt else head
    if namespace:
        return f"{namespace}:{base}"
    return base


def predicate_documents() -> st.SearchStrategy:
    """Strategy producing well-formed PredicateDocument instances.

    Diller et al. 2025 §3 fixes the predicate-declaration shape: id,
    arity, and a typed argument vector whose length equals the arity.
    The strategy enforces ``len(arg_types) == arity`` by construction so
    every generated document is admissible to the registry layer.
    """

    from propstore.families.documents.predicates import PredicateDocument  # noqa: E402

    @st.composite
    def _build(draw: st.DrawFn) -> "PredicateDocument":
        head = draw(_PREDICATE_ID_HEAD)
        namespace = draw(_PREDICATE_ID_NAMESPACE)
        salt = draw(st.integers(min_value=0, max_value=999))
        predicate_id = _make_predicate_id(namespace, head, salt)
        arity = draw(st.integers(min_value=0, max_value=5))
        arg_types = tuple(draw(st.lists(_ARG_TYPE_NAMES, min_size=arity, max_size=arity)))
        derived_from = draw(_DERIVED_FROM_FORMS)
        return PredicateDocument(
            id=predicate_id,
            arity=arity,
            arg_types=arg_types,
            derived_from=derived_from,
            description=None,
        )

    return _build()


def loaded_predicate_files_from(docs) -> "list":
    """Wrap a list of PredicateDocument values in a single LoadedPredicateFile.

    The registry's public ``from_files`` constructor consumes a sequence
    of LoadedPredicateFile envelopes (one per authored YAML file). For
    Hypothesis tests we synthesise a single envelope holding the drawn
    documents so the registry sees the entire population at once.
    """

    from quire.documents import LoadedDocument
    from propstore.families.documents.predicates import PredicatesFileDocument  # noqa: E402
    from propstore.predicate_files import LoadedPredicateFile  # noqa: E402

    file_doc = PredicatesFileDocument(predicates=tuple(docs))
    loaded = LoadedDocument(
        filename="generated",
        source_path=None,
        knowledge_root=None,
        document=file_doc,
    )
    return [LoadedPredicateFile.from_loaded_document(loaded)]


# ── Property tests: PredicateRegistry ──────────────────────────────


@pytest.mark.property
@given(
    docs=st.deferred(
        lambda: st.lists(
            predicate_documents(),
            min_size=1,
            max_size=6,
            unique_by=lambda d: d.id,
        )
    )
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_registry_lookup_returns_matching_document(docs) -> None:
    """For every document stored, ``lookup(doc.id)`` returns it intact.

    Diller et al. 2025 §3 treats the predicate schema as an indexed
    namespace; once a predicate is declared, the grounder retrieves its
    full typed signature by id. The registry must therefore round-trip
    each declared document under lookup.
    """

    from propstore.grounding.predicates import PredicateRegistry  # noqa: E402

    registry = PredicateRegistry.from_files(loaded_predicate_files_from(docs))
    for doc in docs:
        assert registry.lookup(doc.id) == doc


@pytest.mark.property
@given(
    docs=st.deferred(
        lambda: st.lists(
            predicate_documents(),
            min_size=1,
            max_size=6,
            unique_by=lambda d: d.id,
        )
    )
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_registry_lookup_missing_predicate_raises(docs) -> None:
    """Lookup of an unknown predicate id raises.

    Diller et al. 2025 §4: the grounder must reject atoms whose
    predicate is not part of the declared schema, otherwise the Herbrand
    base over that program is undefined. ``KeyError`` (or a dedicated
    ``PredicateNotRegisteredError`` subclass thereof) is the failure
    mode the registry surfaces. Garcia & Simari 2004 §3.2 makes the same
    point: an undeclared predicate has no arity and therefore no
    grounding semantics.
    """

    from propstore.grounding.predicates import PredicateRegistry  # noqa: E402

    registry = PredicateRegistry.from_files(loaded_predicate_files_from(docs))
    known_ids = {d.id for d in docs}
    missing_id = "definitely_not_a_real_predicate_xyz_404"
    assume(missing_id not in known_ids)
    with pytest.raises(KeyError):
        registry.lookup(missing_id)


@pytest.mark.property
@given(
    docs=st.deferred(
        lambda: st.lists(
            predicate_documents(),
            min_size=1,
            max_size=6,
            unique_by=lambda d: d.id,
        )
    ),
    wrong_arity=st.integers(min_value=0, max_value=10),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_registry_validate_atom_rejects_wrong_arity(docs, wrong_arity) -> None:
    """``validate_atom`` rejects arity that mismatches the registration.

    Diller et al. 2025 §4: ground substitutions are well-defined only
    when the atom's term-tuple length equals the declared predicate
    arity; the grounder treats arity mismatches as schema errors.
    Garcia & Simari 2004 §3.2 enforces the same constraint at the
    Herbrand-base level. Equal-arity draws are skipped via ``assume``
    because they exercise the accept path covered by the next test.
    """

    from propstore.grounding.predicates import PredicateAtom, PredicateRegistry  # noqa: E402

    registry = PredicateRegistry.from_files(loaded_predicate_files_from(docs))
    target = docs[0]
    assume(wrong_arity != target.arity)
    atom = PredicateAtom(
        predicate_id=target.id,
        arguments=tuple(f"arg_{index}" for index in range(wrong_arity)),
        argument_types=tuple("Concept" for _ in range(wrong_arity)),
    )
    with pytest.raises(Exception):
        registry.validate_atom(atom)


@pytest.mark.property
@given(
    docs=st.deferred(
        lambda: st.lists(
            predicate_documents(),
            min_size=1,
            max_size=6,
            unique_by=lambda d: d.id,
        )
    )
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_registry_validate_atom_accepts_matching_arity(docs) -> None:
    """``validate_atom`` accepts arity that matches the registration.

    Diller et al. 2025 §4 calls out the matching-arity case as the only
    well-formed grounding input; the registry's validator must therefore
    return cleanly (no exception, no return value contract) when the
    declared and observed arities agree.
    """

    from propstore.grounding.predicates import PredicateAtom, PredicateRegistry  # noqa: E402

    registry = PredicateRegistry.from_files(loaded_predicate_files_from(docs))
    for doc in docs:
        # Should not raise.
        registry.validate_atom(
            PredicateAtom(
                predicate_id=doc.id,
                arguments=tuple(f"arg_{index}" for index in range(doc.arity)),
                argument_types=doc.arg_types,
            )
        )


@pytest.mark.property
@given(
    docs=st.deferred(
        lambda: st.lists(
            predicate_documents(),
            min_size=1,
            max_size=6,
            unique_by=lambda d: d.id,
        )
    )
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_registry_all_predicates_returns_every_declaration(docs) -> None:
    """``all_predicates()`` exposes every loaded declaration.

    Diller et al. 2025 §3: the Datalog schema is the full set of
    declared predicates. The registry must therefore expose them all so
    downstream pipeline stages (the fact extractor in chunk 1.3, the
    grounder in chunk 2.x) can iterate over the complete schema.
    """

    from propstore.grounding.predicates import PredicateRegistry  # noqa: E402

    registry = PredicateRegistry.from_files(loaded_predicate_files_from(docs))
    all_ids = {p.id for p in registry.all_predicates()}
    assert all_ids == {d.id for d in docs}


def test_registry_duplicate_predicate_id_rejected() -> None:
    """Two files declaring the same predicate id must raise on build.

    Diller et al. 2025 §3 makes the predicate id the unique key into the
    Datalog schema; two declarations for the same id are ambiguous
    because the grounder cannot decide which arity/arg-type vector to
    use. Garcia & Simari 2004 §3.2 likewise treats predicate signatures
    as a flat function from id to arity. The registry surfaces this as a
    build-time error so authoring mistakes do not silently shadow.
    """

    from propstore.grounding.predicates import PredicateRegistry  # noqa: E402
    from quire.documents import LoadedDocument
    from propstore.families.documents.predicates import (  # noqa: E402
        PredicateDocument,
        PredicatesFileDocument,
    )
    from propstore.predicate_files import LoadedPredicateFile  # noqa: E402

    duplicate_id = "bird"
    doc_a = PredicateDocument(
        id=duplicate_id,
        arity=1,
        arg_types=("Bird",),
        derived_from=None,
        description=None,
    )
    doc_b = PredicateDocument(
        id=duplicate_id,
        arity=2,
        arg_types=("Bird", "Person"),
        derived_from=None,
        description=None,
    )

    def _wrap(doc: PredicateDocument, name: str) -> LoadedPredicateFile:
        file_doc = PredicatesFileDocument(predicates=(doc,))
        loaded = LoadedDocument(
            filename=name,
            source_path=None,
            knowledge_root=None,
            document=file_doc,
        )
        return LoadedPredicateFile.from_loaded_document(loaded)

    files = [_wrap(doc_a, "first"), _wrap(doc_b, "second")]
    with pytest.raises(Exception):
        PredicateRegistry.from_files(files)


# ── Property tests: parse_derived_from DSL ─────────────────────────


def test_parse_derived_from_concept_relation() -> None:
    """Parse ``'concept.relation:is_a:Bird'`` into a typed spec.

    Diller et al. 2025 §3 anchors predicates to the underlying knowledge
    graph via concept relations; the DSL form encodes the relation name
    and the target concept. The parser must surface ``kind ==
    'concept_relation'`` and round-trip the canonical
    ``is_a:Bird`` example used throughout Garcia & Simari 2004 §3.
    """

    from propstore.grounding.predicates import parse_derived_from  # noqa: E402

    spec = parse_derived_from("concept.relation:is_a:Bird")
    assert spec.kind == "concept_relation"
    assert spec.relation == "is_a"
    assert spec.target == "Bird"


def test_parse_derived_from_concept_relation_artifact_target() -> None:
    """Artifact-id targets with embedded ``:`` parse intact.

    Propstore concept relationships use canonical artifact ids as
    targets, so the ``concept.relation`` target segment must round-trip
    values such as ``ps:concept:...`` without truncation.
    """

    from propstore.grounding.predicates import parse_derived_from  # noqa: E402

    spec = parse_derived_from(
        "concept.relation:related:ps:concept:45fa8536a97bc81d"
    )
    assert spec.kind == "concept_relation"
    assert spec.relation == "related"
    assert spec.target == "ps:concept:45fa8536a97bc81d"


def test_parse_derived_from_claim_attribute() -> None:
    """Parse ``'claim.attribute:is_bird'`` into a typed spec.

    Diller et al. 2025 §4 lets predicates derive from claim attributes
    so a fact extractor can pull boolean (or boolean-coerced) values out
    of the claim store. The parser must surface ``kind ==
    'claim_attribute'`` and expose the attribute name.
    """

    from propstore.grounding.predicates import parse_derived_from  # noqa: E402

    spec = parse_derived_from("claim.attribute:is_bird")
    assert spec.kind == "claim_attribute"
    assert spec.attribute == "is_bird"


def test_parse_derived_from_claim_condition() -> None:
    """Parse ``'claim.condition:tweety'`` into a typed spec.

    Diller et al. 2025 §4 also admits claim-side conditions as
    predicate sources; the DSL form names the condition. ``kind ==
    'claim_condition'`` is the discriminant and the parsed value must
    expose the condition name.
    """

    from propstore.grounding.predicates import parse_derived_from  # noqa: E402

    spec = parse_derived_from("claim.condition:tweety")
    assert spec.kind == "claim_condition"
    assert spec.condition == "tweety"


def test_parse_derived_from_unknown_kind_raises() -> None:
    """Unknown DSL prefixes raise a clear error.

    Diller et al. 2025 §3 fixes the source kinds the grounder knows
    about; an unknown prefix is an authoring typo and must be rejected.
    Garcia & Simari 2004 §3 admits no other extension points at the
    schema layer.
    """

    from propstore.grounding.predicates import parse_derived_from  # noqa: E402

    with pytest.raises(Exception):
        parse_derived_from("nonsense.prefix:foo:bar")


def test_parse_derived_from_malformed_raises() -> None:
    """Missing separators and empty segments raise.

    Diller et al. 2025 §3 demands a fixed grammar for the
    ``derived_from`` DSL; loose decoding would let typos pass and
    silently misroute fact extraction. Each malformed shape exercised
    here corresponds to a separate authoring failure mode.
    """

    from propstore.grounding.predicates import parse_derived_from  # noqa: E402

    malformed_inputs = [
        "",  # empty string
        "concept.relation",  # missing relation and target
        "concept.relation:is_a",  # missing target
        "claim.attribute",  # missing attribute name
        "claim.attribute:",  # empty attribute name
        "claim.condition",  # missing condition name
        "claim.condition:",  # empty condition name
        "concept.relation::Bird",  # empty relation
        "concept.relation:is_a:",  # empty target
    ]
    for spec in malformed_inputs:
        with pytest.raises(Exception):
            parse_derived_from(spec)


@pytest.mark.property
@given(
    spec_and_kind=st.sampled_from(
        [
            ("concept.relation:is_a:Bird", "concept_relation"),
            ("concept.relation:part_of:Wheel", "concept_relation"),
            ("claim.attribute:is_bird", "claim_attribute"),
            ("claim.condition:tweety_present", "claim_condition"),
        ]
    )
)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_parse_derived_from_round_trips(spec_and_kind) -> None:
    """Every canonical DSL form parses into its declared kind.

    Diller et al. 2025 §3-§4 lists the three sanctioned DSL prefixes;
    the parser must accept the canonical form for each one and tag the
    parsed result with the matching kind discriminant. Garcia & Simari
    2004 §3 birds/penguins examples are used as the payload tokens.
    """

    from propstore.grounding.predicates import parse_derived_from  # noqa: E402

    spec_text, expected_kind = spec_and_kind
    parsed = parse_derived_from(spec_text)
    assert parsed.kind == expected_kind
