"""Property tests for PredicateDocument / PredicatesFileDocument YAML schema.

These tests describe the contract for the typed predicate-declaration
documents that live in
`propstore/artifacts/documents/predicates.py`. Imports are deferred into
strategy and test bodies so the file still parses if the schema module
is unavailable at import time.

Theoretical sources:
    Diller, M. et al. (2025). Grounding Rule-Based Argumentation Using
    Datalog.
    - Section 3: predicate signatures ``p(t_1,...,t_n)`` carry a fixed
      arity and a per-position type, encoded into a Datalog schema so the
      grounding step can range each variable over the right concept set.
    - Section 4: ground substitutions are well-defined only when the
      predicate's declared arity matches every atom's term tuple length.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): predicate symbols, arity, the special case of
      0-ary predicates as propositional facts, and ground literals built
      from the Herbrand base.

DocumentStruct conventions mirrored from
`propstore/artifacts/documents/rules.py`
and `propstore/artifacts/documents/claims.py`:
    - ``msgspec.Struct`` with ``kw_only=True, forbid_unknown_fields=True``.
    - List-valued fields use ``tuple[T, ...] = ()`` for immutability.
    - Round-tripping through ``msgspec.yaml.{encode,decode}`` is idempotent
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
# Strategies live in this file per the chunk constraint: no conftest.py,
# no shared helper module. Every strategy closes over deferred imports so
# the file parses without `propstore.artifacts.documents.predicates`.


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
    """Build a predicate id with optional namespace prefix and salt suffix.

    Diller et al. 2025 §3 treats predicate identifiers opaquely; the
    schema only needs to round-trip arbitrary lowercase identifiers
    optionally namespaced with a colon prefix. The integer salt makes
    Hypothesis able to generate enough distinct ids for ``unique_by``
    constraints in the registry tests without exhausting the sample pool.
    """

    base = f"{head}_{salt}" if salt else head
    if namespace:
        return f"{namespace}:{base}"
    return base


def predicate_documents() -> st.SearchStrategy:
    """Strategy producing well-formed PredicateDocument instances.

    Diller et al. 2025 §3 fixes the predicate-declaration shape: an id,
    an arity, and a per-position type list whose length must match the
    arity. This strategy enforces ``len(arg_types) == arity`` by drawing
    the arity first and then drawing exactly that many type names. The
    optional ``derived_from`` slot tracks the DSL surface defined for the
    registry layer (``concept.relation:...`` / ``claim.attribute:...`` /
    ``claim.condition:...``); ``description`` is a free-text annotation.
    """

    from propstore.artifacts.documents.predicates import PredicateDocument  # noqa: E402

    @st.composite
    def _build(draw: st.DrawFn) -> "PredicateDocument":
        head = draw(_PREDICATE_ID_HEAD)
        namespace = draw(_PREDICATE_ID_NAMESPACE)
        salt = draw(st.integers(min_value=0, max_value=999))
        predicate_id = _make_predicate_id(namespace, head, salt)
        arity = draw(st.integers(min_value=0, max_value=5))
        arg_types = tuple(draw(st.lists(_ARG_TYPE_NAMES, min_size=arity, max_size=arity)))
        derived_from = draw(_DERIVED_FROM_FORMS)
        description = draw(
            st.one_of(
                st.none(),
                st.text(
                    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd", "Zs")),
                    min_size=0,
                    max_size=20,
                ),
            )
        )
        return PredicateDocument(
            id=predicate_id,
            arity=arity,
            arg_types=arg_types,
            derived_from=derived_from,
            description=description,
        )

    return _build()


def predicates_file_documents() -> st.SearchStrategy:
    """Strategy producing well-formed PredicatesFileDocument envelopes.

    Mirrors the ``RulesFileDocument`` envelope shape from
    ``propstore/rule_documents.py``: a flat ordered tuple of predicate
    documents. Order matters because authored order is the only stable
    way to anchor authoring intent across re-encoding.
    """

    from propstore.artifacts.documents.predicates import PredicatesFileDocument  # noqa: E402

    return st.builds(
        PredicatesFileDocument,
        predicates=st.lists(predicate_documents(), min_size=0, max_size=4).map(tuple),
    )


# ── Property tests ─────────────────────────────────────────────────


@given(doc=st.deferred(predicate_documents))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_predicate_document_yaml_round_trip(doc) -> None:
    """msgspec YAML round-trip is idempotent for PredicateDocument.

    Standard property required of every msgspec document type
    (Diller et al. 2025 §3 demands a stable predicate schema so the
    Datalog grounder can rely on the declarations across pipeline runs).
    """

    from propstore.artifacts.documents.predicates import PredicateDocument  # noqa: E402

    encoded = msgspec.yaml.encode(doc)
    decoded = msgspec.yaml.decode(encoded, type=PredicateDocument, strict=True)
    assert decoded == doc


@given(doc=st.deferred(predicates_file_documents))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_predicates_file_document_yaml_round_trip(doc) -> None:
    """File envelope round-trip is idempotent.

    Mirrors the ``RulesFileDocument`` round-trip property
    (``tests/test_rule_documents.py``); a fully-loaded predicates file
    must re-encode to a payload that decodes back to an equal document.
    """

    from propstore.artifacts.documents.predicates import PredicatesFileDocument  # noqa: E402

    encoded = msgspec.yaml.encode(doc)
    decoded = msgspec.yaml.decode(encoded, type=PredicatesFileDocument, strict=True)
    assert decoded == doc


@given(doc=st.deferred(predicate_documents))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_predicate_arg_types_length_matches_arity(doc) -> None:
    """Schema invariant: ``len(arg_types) == arity``.

    Diller et al. 2025 §3 declares each predicate as ``p(t_1,...,t_n)``
    with a fixed arity ``n`` and a typed argument vector of exactly that
    length. The strategy produces documents satisfying this invariant;
    the test pins it explicitly so any future relaxation of the strategy
    or the schema is caught at the property layer.
    """

    assert len(doc.arg_types) == doc.arity


@given(doc=st.deferred(predicate_documents))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_predicate_arg_types_are_strings(doc) -> None:
    """Each declared argument type is a non-empty string.

    Diller et al. 2025 §3: argument types name a sort/concept used by
    the grounder to enumerate ground substitutions. They must be present
    (non-``None``) and non-empty so the grounding lookup is well-defined.
    """

    for arg_type in doc.arg_types:
        assert isinstance(arg_type, str)
        assert arg_type != ""


def test_predicate_document_unknown_field_rejected() -> None:
    """DocumentStruct ``forbid_unknown_fields=True`` is honoured.

    Pattern inherited from ``propstore.document_schema.DocumentStruct``:
    a predicate declaration carrying an unknown field is an authoring
    error and must be rejected by strict msgspec decoding. Diller et al.
    2025 §3 treats predicate signatures as part of the program schema —
    silently dropping mystery fields would let typos pass.
    """

    from propstore.artifacts.documents.predicates import PredicateDocument  # noqa: E402

    yaml_with_extra = b"""
id: bird
arity: 1
arg_types: [Bird]
mystery_field: hello
"""
    with pytest.raises(msgspec.ValidationError):
        msgspec.yaml.decode(yaml_with_extra, type=PredicateDocument, strict=True)


def test_predicate_document_example_birds() -> None:
    """Concrete example: the ``bird`` predicate from Garcia & Simari 2004 §3.

    Garcia & Simari 2004 §3 (p.3-4) repeatedly uses the unary ``bird/1``
    predicate as the canonical defeasible-reasoning toy example. Pinning
    its YAML shape against a literal authored payload prevents the
    PredicateDocument surface from drifting silently.
    """

    from propstore.artifacts.documents.predicates import PredicateDocument  # noqa: E402

    yaml_text = b"""
id: bird
arity: 1
arg_types: [Bird]
derived_from: 'concept.relation:is_a:Bird'
description: "Unary predicate: X is a bird"
"""
    doc = msgspec.yaml.decode(yaml_text, type=PredicateDocument, strict=True)
    assert doc.id == "bird"
    assert doc.arity == 1
    assert doc.arg_types == ("Bird",)
    assert doc.derived_from == "concept.relation:is_a:Bird"
    assert doc.description == "Unary predicate: X is a bird"


def test_predicate_document_nullary() -> None:
    """Arity-0 predicates (propositional facts) are valid.

    Garcia & Simari 2004 §3 (p.3) treats facts as 0-ary ground literals;
    a predicate with ``arity: 0`` and an empty ``arg_types`` tuple must
    decode cleanly so propositional rules (e.g. ``raining``) survive
    round-trip. Diller et al. 2025 §3 likewise admits 0-ary atoms in
    Datalog programs.
    """

    from propstore.artifacts.documents.predicates import PredicateDocument  # noqa: E402

    yaml_text = b"""
id: raining
arity: 0
arg_types: []
description: "Propositional fact: it is raining"
"""
    doc = msgspec.yaml.decode(yaml_text, type=PredicateDocument, strict=True)
    assert doc.id == "raining"
    assert doc.arity == 0
    assert doc.arg_types == ()
    assert doc.derived_from is None


def test_predicate_document_omits_optional_fields() -> None:
    """``derived_from`` and ``description`` default to ``None``.

    The PredicateDocument schema must admit minimal authored payloads
    that omit the optional metadata. Diller et al. 2025 §3 only requires
    id/arity/arg_types in the predicate signature; provenance and
    documentation are layered on top.
    """

    from propstore.artifacts.documents.predicates import PredicateDocument  # noqa: E402

    yaml_text = b"""
id: flies
arity: 1
arg_types: [Bird]
"""
    doc = msgspec.yaml.decode(yaml_text, type=PredicateDocument, strict=True)
    assert doc.derived_from is None
    assert doc.description is None


def test_loaded_predicate_file_from_loaded_document() -> None:
    """LoadedPredicateFile wraps ``LoadedDocument[PredicatesFileDocument]``.

    Mirrors the ``LoadedRuleFile.from_loaded_document`` pattern from
    ``propstore/rule_files.py``: build a ``LoadedDocument`` directly,
    wrap it via the classmethod, and confirm metadata propagates plus
    the ``.predicates`` accessor returns the inner tuple unchanged. The
    Garcia & Simari 2004 §3 ``bird/1`` predicate is the payload.
    """

    from quire.documents import LoadedDocument
    from propstore.artifacts.documents.predicates import (  # noqa: E402
        PredicateDocument,
        PredicatesFileDocument,
    )
    from propstore.predicate_files import LoadedPredicateFile  # noqa: E402

    predicate = PredicateDocument(
        id="bird",
        arity=1,
        arg_types=("Bird",),
        derived_from="concept.relation:is_a:Bird",
        description="Unary predicate: X is a bird",
    )
    file_doc = PredicatesFileDocument(predicates=(predicate,))
    loaded = LoadedDocument(
        filename="birds",
        source_path=None,
        knowledge_root=None,
        document=file_doc,
    )
    wrapped = LoadedPredicateFile.from_loaded_document(loaded)

    assert wrapped.filename == "birds"
    assert wrapped.predicates == (predicate,)
    assert wrapped.document is file_doc


@given(file_doc=st.deferred(predicates_file_documents))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_predicates_file_document_preserves_order(file_doc) -> None:
    """Authored order of predicates survives YAML round-trip.

    Diller et al. 2025 §3 builds the Datalog schema in the order
    declarations are encountered; the file envelope therefore must
    preserve order across encode/decode so authoring intent does not
    silently scramble.
    """

    from propstore.artifacts.documents.predicates import PredicatesFileDocument  # noqa: E402

    encoded = msgspec.yaml.encode(file_doc)
    decoded = msgspec.yaml.decode(encoded, type=PredicatesFileDocument, strict=True)
    assert tuple(p.id for p in decoded.predicates) == tuple(p.id for p in file_doc.predicates)
