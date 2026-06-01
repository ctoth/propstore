"""Adapter spec for ``propstore.opinion`` over the ``doxa`` pure kernel.

This file is the G3 tester deliverable for the ``doxa`` extraction. It
SPECIFIES the propstore-side adapter:

    class Opinion(doxa.Opinion):
        provenance: Provenance | None
        # every provenance-touching op overridden: super() for the math,
        # rewrap the result via compose_provenance.

The pure subjective-logic algebra (negation, conjunction, fusion, ...) is
owned and tested by the standalone ``doxa`` kernel (``doxa/tests/``). This
file does NOT re-test the algebra. It tests exactly the thing doxa cannot:
that ``propstore.opinion.Opinion`` threads ``Provenance`` through every
kernel operation, composing status the way the pre-extraction
``propstore/opinion.py`` did.

RED state: until the G3 coder pins ``doxa`` into ``pyproject.toml`` and
rewrites ``propstore/opinion.py`` as the adapter, ``import doxa`` raises
``ModuleNotFoundError: doxa`` and this whole module fails at collection.
That is the correct, expected red — see ``reports/doxa-g3-tester.md``.

The anti-silent-drop guarantee (decision 4 of ``notes/doxa-extraction.md``)
is enforced here by ``TestOperationEnumerationGuard``: it introspects the
live ``doxa.Opinion`` operation surface and ERRORs loudly if a kernel
operation that produces an ``Opinion`` has no provenance coverage in this
file. A hardcoded operation list would rot; this one cannot.

Grounding:
- Jøsang 2001, "A Logic for Uncertain Probabilities."
- van der Heijden et al. 2018, "Multi-Source Fusion Operations in
  Subjective Logic."
"""

from __future__ import annotations

import inspect

import pytest

import doxa

from propstore.opinion import BetaEvidence, Opinion
from propstore.provenance import (
    Provenance,
    ProvenanceStatus,
    ProvenanceWitness,
    compose_provenance,
)


# ── Provenance fixtures ────────────────────────────────────────────────
#
# Distinct statuses so composition is observable: compose_provenance picks
# the highest-ranked status across its inputs (provenance/__init__.py
# _STATUS_RANK: vacuous < stated < measured < calibrated < defaulted).


def _witness(name: str) -> ProvenanceWitness:
    return ProvenanceWitness(
        asserter=f"urn:agent:{name}",
        timestamp="2026-05-21T00:00:00Z",
        source_artifact_code=f"{name}:p1",
        method="stated",
    )


def _provenance(status: ProvenanceStatus, name: str) -> Provenance:
    return Provenance(
        status=status,
        witnesses=(_witness(name),),
        operations=(f"author:{name}",),
    )


# Two operands with different statuses. compose_provenance must surface
# the higher rank (CALIBRATED beats MEASURED).
PROV_MEASURED = _provenance(ProvenanceStatus.MEASURED, "left")
PROV_CALIBRATED = _provenance(ProvenanceStatus.CALIBRATED, "right")


def _op(b: float, d: float, u: float, a: float, prov: Provenance | None) -> Opinion:
    """A non-dogmatic propstore Opinion carrying ``prov``."""
    return (
        Opinion(b, d, u, a).with_provenance(prov)
        if prov is not None
        else Opinion(b, d, u, a)
    )


# Two provenance-bearing, non-dogmatic operands used across the suite.
LEFT = _op(0.5, 0.2, 0.3, 0.6, PROV_MEASURED)
RIGHT = _op(0.3, 0.3, 0.4, 0.4, PROV_CALIBRATED)


# ── The operation registry ─────────────────────────────────────────────
#
# Each entry maps a doxa.Opinion operation name to a zero-arg callable
# that invokes that operation THROUGH propstore.opinion.Opinion with
# provenance-bearing operands and returns the resulting Opinion. The
# enumeration guard cross-checks this registry against the live
# doxa.Opinion surface; any uncovered Opinion-producing operation makes
# the guard ERROR loudly.
#
# Value: (invoker, expected_status, composes)
#   invoker         -> () -> Opinion
#   expected_status -> the ProvenanceStatus the result must carry
#   composes        -> True if the op composes >=2 provenance records
#                      (status = max rank), False if it carries a single
#                      operand's provenance unchanged.


def _binary_max_status() -> ProvenanceStatus:
    """Status compose_provenance yields for LEFT (MEASURED) + RIGHT (CALIBRATED)."""
    return compose_provenance(PROV_MEASURED, PROV_CALIBRATED, operation="probe").status


_BINARY_STATUS = _binary_max_status()


OPERATION_REGISTRY: dict[str, tuple] = {
    # --- unary operators: carry self.provenance unchanged ---
    "__invert__": (lambda: ~LEFT, ProvenanceStatus.MEASURED, False),
    "maximize_uncertainty": (
        lambda: LEFT.maximize_uncertainty(),
        ProvenanceStatus.MEASURED,
        False,
    ),
    # --- binary operators: compose both operands' provenance ---
    "conjunction": (
        lambda: LEFT.conjunction(RIGHT),
        _BINARY_STATUS,
        True,
    ),
    "disjunction": (
        lambda: LEFT.disjunction(RIGHT),
        _BINARY_STATUS,
        True,
    ),
    "__and__": (lambda: LEFT & RIGHT, _BINARY_STATUS, True),
    "__or__": (lambda: LEFT | RIGHT, _BINARY_STATUS, True),
    "consensus_pair": (
        lambda: LEFT.consensus_pair(RIGHT),
        _BINARY_STATUS,
        True,
    ),
    "discount": (lambda: LEFT.discount(RIGHT), _BINARY_STATUS, True),
    # --- N-source classmethods: compose every operand's provenance ---
    "consensus": (
        lambda: Opinion.consensus(LEFT, RIGHT),
        _BINARY_STATUS,
        True,
    ),
    "wbf": (lambda: Opinion.wbf(LEFT, RIGHT), _BINARY_STATUS, True),
    "ccf": (lambda: Opinion.ccf(LEFT, RIGHT), _BINARY_STATUS, True),
    "fuse": (
        lambda: Opinion.fuse(LEFT, RIGHT, method="auto"),
        _BINARY_STATUS,
        True,
    ),
    # --- constructors: provenance flows in through an explicit kwarg ---
    "vacuous": (
        lambda: Opinion.vacuous(0.5, provenance=PROV_MEASURED),
        ProvenanceStatus.MEASURED,
        False,
    ),
    "dogmatic_true": (
        lambda: Opinion.dogmatic_true(0.5, provenance=PROV_MEASURED),
        ProvenanceStatus.MEASURED,
        False,
    ),
    "dogmatic_false": (
        lambda: Opinion.dogmatic_false(0.5, provenance=PROV_MEASURED),
        ProvenanceStatus.MEASURED,
        False,
    ),
    "from_evidence": (
        lambda: Opinion.from_evidence(7.0, 3.0, 0.5, provenance=PROV_MEASURED),
        ProvenanceStatus.MEASURED,
        False,
    ),
    "from_probability": (
        lambda: Opinion.from_probability(0.7, 10.0, 0.5, provenance=PROV_MEASURED),
        ProvenanceStatus.MEASURED,
        False,
    ),
}


def _doxa_opinion_producing_operations() -> set[str]:
    """Introspect ``doxa.Opinion`` for every operation that yields an Opinion.

    Walks every classmethod, staticmethod, plain instance method, and
    overloadable dunder declared on the kernel ``doxa.Opinion``. An
    operation "produces an Opinion" if invoking it via this file's
    registry returns a ``doxa.Opinion`` instance. Members with no
    registry entry are returned anyway (as a sentinel "uncovered" set)
    so the guard can fail on them — the whole point of the enumeration
    guard is that an UNcovered Opinion-producing op is loud, not silent.

    Non-Opinion-producing surface (``expectation`` -> float,
    ``uncertainty_interval`` -> tuple, ``to_beta_evidence`` ->
    BetaEvidence, ``__eq__``/``__lt__`` -> bool, the ``uncertainty`` /
    ``base_rate`` properties, ``__bool__`` which raises) is excluded:
    those carry no Opinion result whose provenance could be dropped.
    """
    # Names that are kernel surface but provably do not return an Opinion.
    non_opinion_surface = {
        "expectation",
        "uncertainty_interval",
        "to_beta_evidence",
        "uncertainty",
        "base_rate",
        "__bool__",
        "__eq__",
        "__hash__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
        "__post_init__",
        "_quantized",
        "_ordering_key",
        "__init__",
        "__repr__",
        "__setattr__",
        "__delattr__",
    }

    producing: set[str] = set()
    for name, member in inspect.getmembers(doxa.Opinion):
        if name in non_opinion_surface:
            continue
        if name.startswith("__") and name not in {
            "__invert__",
            "__and__",
            "__or__",
        }:
            # dunder noise (__class__, __module__, __dataclass_fields__, ...)
            continue
        # Only callables / descriptors count as operations.
        is_callable = callable(member) or isinstance(
            member, (classmethod, staticmethod)
        )
        if not is_callable:
            continue
        producing.add(name)
    return producing


class TestOperationEnumerationGuard:
    """Structural anti-silent-drop guard (decision 4, doxa-extraction.md).

    Introspects the live ``doxa.Opinion`` operation surface. Every kernel
    operation that produces an ``Opinion`` MUST be covered by
    ``OPERATION_REGISTRY`` with a provenance assertion. A new ``doxa``
    operation with no coverage makes this test ERROR loudly — the
    guarantee that the type system gave up when ``Opinion[P]`` was
    rejected is relocated here to CI time, at full strength.
    """

    def test_every_opinion_producing_doxa_op_is_covered(self):
        """No doxa.Opinion operation may escape provenance coverage.

        For each callable operation on ``doxa.Opinion``, decide whether
        it produces an ``Opinion`` by invoking it through the registry.
        If it does and is absent from ``OPERATION_REGISTRY`` -> fail
        loudly. If it does NOT produce an Opinion, it is exempt.
        """
        surface = _doxa_opinion_producing_operations()

        # Operations the registry knows about and that DO produce an Opinion.
        uncovered_opinion_ops: list[str] = []
        for name in sorted(surface):
            if name in OPERATION_REGISTRY:
                continue
            # Not in the registry. Is it Opinion-producing? We cannot
            # invoke an unknown-arity op blindly, so treat any callable
            # operation on doxa.Opinion that is missing from the registry
            # as a coverage gap UNLESS it is known non-Opinion surface
            # (already filtered above). Anything left here is either a
            # genuinely new Opinion op, or new non-Opinion surface the
            # tester must explicitly classify.
            uncovered_opinion_ops.append(name)

        assert not uncovered_opinion_ops, (
            "doxa.Opinion exposes operation(s) with NO provenance "
            f"coverage in OPERATION_REGISTRY: {uncovered_opinion_ops}. "
            "Either add a registry entry asserting provenance survives, "
            "or, if the op provably does not return an Opinion, add it "
            "to _doxa_opinion_producing_operations.non_opinion_surface. "
            "Silent coverage loss is the exact failure decision 4 of "
            "notes/doxa-extraction.md forbids."
        )

    def test_registry_only_names_real_doxa_operations(self):
        """Every registry key must name a real ``doxa.Opinion`` member.

        Guards the other direction: a registry entry for an operation
        the kernel no longer has is dead coverage and must fail.
        """
        members = dict(inspect.getmembers(doxa.Opinion))
        stale = [name for name in OPERATION_REGISTRY if name not in members]
        assert not stale, (
            f"OPERATION_REGISTRY names operations absent from doxa.Opinion: "
            f"{stale}. The kernel API changed; update the registry."
        )

    @pytest.mark.parametrize("op_name", sorted(OPERATION_REGISTRY))
    def test_registered_operation_preserves_provenance(self, op_name):
        """Every registered operation yields a provenance-bearing Opinion.

        Invokes the operation through ``propstore.opinion.Opinion`` with
        provenance-bearing operands and asserts:
        - the result is a ``propstore.opinion.Opinion`` (IS-A doxa.Opinion);
        - ``result.provenance`` is not None;
        - ``result.provenance.status`` is the expected composed/carried
          status.
        """
        invoker, expected_status, composes = OPERATION_REGISTRY[op_name]
        result = invoker()

        assert isinstance(result, Opinion), (
            f"{op_name} returned {type(result)!r}, not propstore Opinion"
        )
        assert isinstance(result, doxa.Opinion), (
            f"{op_name} result must IS-A doxa.Opinion"
        )
        assert result.provenance is not None, (
            f"{op_name} dropped provenance — result.provenance is None"
        )
        assert result.provenance.status == expected_status, (
            f"{op_name} composed status {result.provenance.status!r}, "
            f"expected {expected_status!r}"
        )
        if composes:
            # A composing op records the operation in the provenance chain.
            assert result.provenance.operations, (
                f"{op_name} composed provenance but recorded no operations"
            )


# ── Explicit per-operation provenance-preservation tests ───────────────
#
# These are the assertions the G2 tester stripped from the kernel suite,
# restored here as propstore adapter tests. They are explicit (not
# registry-driven) so a regression names the exact operation.


class TestNegationProvenance:
    """``~ω`` carries ``ω.provenance`` unchanged (Jøsang Theorem 6)."""

    def test_negation_carries_provenance(self):
        result = ~LEFT
        assert result.provenance is PROV_MEASURED

    def test_negation_of_provenanceless_is_none(self):
        result = ~Opinion(0.5, 0.2, 0.3, 0.6)
        assert result.provenance is None


class TestConjunctionDisjunctionProvenance:
    """Conjunction / disjunction COMPOSE both operands' provenance."""

    def test_conjunction_composes_provenance(self):
        result = LEFT.conjunction(RIGHT)
        assert result.provenance is not None
        assert result.provenance.status == _BINARY_STATUS
        assert "conjunction" in result.provenance.operations

    def test_disjunction_composes_provenance(self):
        result = LEFT.disjunction(RIGHT)
        assert result.provenance is not None
        assert result.provenance.status == _BINARY_STATUS
        assert "disjunction" in result.provenance.operations

    def test_and_operator_composes_like_conjunction(self):
        assert (LEFT & RIGHT).provenance == LEFT.conjunction(RIGHT).provenance

    def test_or_operator_composes_like_disjunction(self):
        assert (LEFT | RIGHT).provenance == LEFT.disjunction(RIGHT).provenance

    def test_conjunction_with_one_provenanceless_operand(self):
        """Composition over the records that exist — a None operand drops out.

        Mirrors ``_compose_opinion_provenance`` in the pre-extraction
        module: it filters ``provenance is None`` operands, so a single
        surviving record means the result carries that record's status.
        """
        bare = Opinion(0.3, 0.3, 0.4, 0.4)
        result = LEFT.conjunction(bare)
        assert result.provenance is not None
        assert result.provenance.status == ProvenanceStatus.MEASURED

    def test_conjunction_of_two_provenanceless_is_none(self):
        a = Opinion(0.5, 0.2, 0.3, 0.6)
        b = Opinion(0.3, 0.3, 0.4, 0.4)
        assert a.conjunction(b).provenance is None


class TestDiscountProvenance:
    """``trust.discount(source)`` composes trust + source provenance."""

    def test_discount_composes_provenance(self):
        result = LEFT.discount(RIGHT)
        assert result.provenance is not None
        assert result.provenance.status == _BINARY_STATUS
        assert "discount" in result.provenance.operations


class TestConsensusProvenance:
    """``consensus_pair`` and ``consensus`` compose provenance via fusion."""

    def test_consensus_pair_composes_provenance(self):
        result = LEFT.consensus_pair(RIGHT)
        assert result.provenance is not None
        assert result.provenance.status == _BINARY_STATUS
        assert "fusion" in result.provenance.operations

    def test_consensus_fold_composes_all_provenance(self):
        third = _op(0.2, 0.2, 0.6, 0.5, _provenance(ProvenanceStatus.STATED, "third"))
        result = Opinion.consensus(LEFT, RIGHT, third)
        assert result.provenance is not None
        # Highest rank across MEASURED, CALIBRATED, STATED is CALIBRATED.
        assert result.provenance.status == ProvenanceStatus.CALIBRATED

    def test_consensus_single_opinion_keeps_its_provenance(self):
        result = Opinion.consensus(LEFT)
        assert result.provenance is PROV_MEASURED


class TestFusionProvenance:
    """WBF / CCF / fuse compose provenance across all sources."""

    def test_wbf_composes_provenance(self):
        result = Opinion.wbf(LEFT, RIGHT)
        assert result.provenance is not None
        assert result.provenance.status == _BINARY_STATUS
        assert "fusion" in result.provenance.operations

    def test_ccf_composes_provenance(self):
        result = Opinion.ccf(LEFT, RIGHT)
        assert result.provenance is not None
        assert result.provenance.status == _BINARY_STATUS
        assert "fusion" in result.provenance.operations

    def test_fuse_auto_composes_provenance(self):
        result = Opinion.fuse(LEFT, RIGHT, method="auto")
        assert result.provenance is not None
        assert result.provenance.status == _BINARY_STATUS

    def test_wbf_single_source_keeps_provenance(self):
        result = Opinion.wbf(LEFT)
        assert result.provenance is PROV_MEASURED

    def test_wbf_dogmatic_case_composes_provenance(self):
        """WBF Definition 4 Case 2 (dogmatic sources) still composes provenance."""
        dt = Opinion.dogmatic_true(0.5, provenance=PROV_MEASURED)
        df = Opinion.dogmatic_false(0.5, provenance=PROV_CALIBRATED)
        result = Opinion.wbf(dt, df)
        assert result.provenance is not None
        assert result.provenance.status == _BINARY_STATUS


class TestMaximizeUncertaintyProvenance:
    """``maximize_uncertainty`` carries ``self.provenance`` unchanged."""

    def test_maximize_uncertainty_carries_provenance(self):
        result = LEFT.maximize_uncertainty()
        assert result.provenance is PROV_MEASURED

    def test_maximize_uncertainty_provenanceless_stays_none(self):
        result = Opinion(0.5, 0.2, 0.3, 0.6).maximize_uncertainty()
        assert result.provenance is None


class TestConstructorProvenance:
    """The constructors accept a ``provenance=`` kwarg and store it."""

    def test_vacuous_stores_provenance(self):
        result = Opinion.vacuous(0.5, provenance=PROV_MEASURED)
        assert result.provenance is PROV_MEASURED

    def test_dogmatic_true_stores_provenance(self):
        result = Opinion.dogmatic_true(0.5, provenance=PROV_MEASURED)
        assert result.provenance is PROV_MEASURED

    def test_dogmatic_false_stores_provenance(self):
        result = Opinion.dogmatic_false(0.5, provenance=PROV_MEASURED)
        assert result.provenance is PROV_MEASURED

    def test_constructors_default_to_no_provenance(self):
        assert Opinion.vacuous(0.5).provenance is None
        assert Opinion.dogmatic_true(0.5).provenance is None
        assert Opinion.dogmatic_false(0.5).provenance is None

    def test_from_evidence_stores_provenance(self):
        result = Opinion.from_evidence(7.0, 3.0, 0.5, provenance=PROV_MEASURED)
        assert result.provenance is PROV_MEASURED

    def test_from_probability_stores_provenance(self):
        result = Opinion.from_probability(0.7, 10.0, 0.5, provenance=PROV_MEASURED)
        assert result.provenance is PROV_MEASURED

    def test_beta_evidence_to_opinion_accepts_provenance(self):
        result = BetaEvidence(7.0, 3.0, 0.5).to_opinion(provenance=PROV_MEASURED)
        assert isinstance(result, Opinion)
        assert result.provenance is PROV_MEASURED

    def test_beta_evidence_to_opinion_defaults_to_no_provenance(self):
        assert BetaEvidence(7.0, 3.0, 0.5).to_opinion().provenance is None


class TestToBetaEvidenceDropsProvenance:
    """``to_beta_evidence`` returns a kernel ``BetaEvidence`` — no provenance.

    ``BetaEvidence`` has no provenance field; an Opinion->Beta->Opinion
    roundtrip therefore loses provenance. This is documented in
    notes/doxa-extraction.md "Risks" as behavior to PRESERVE, not a bug
    to fix mid-extraction.
    """

    def test_roundtrip_through_beta_evidence_loses_provenance(self):
        evidence = LEFT.to_beta_evidence()
        assert not hasattr(evidence, "provenance")
        restored = evidence.to_opinion()
        assert restored.provenance is None


# ── Cross-type equality / hashing ──────────────────────────────────────


class TestCrossTypeEquality:
    """``propstore.opinion.Opinion`` IS-A ``doxa.Opinion``.

    The kernel ``__eq__`` does ``isinstance(other, doxa.Opinion)`` and
    compares only the quantized ``(b, d, u, a)`` grid — provenance is
    never part of identity. Equality and hashing must therefore behave
    between a propstore Opinion and a bare doxa Opinion carrying the
    same tuple.
    """

    def test_propstore_opinion_is_a_doxa_opinion(self):
        assert isinstance(Opinion(0.5, 0.2, 0.3, 0.6), doxa.Opinion)
        assert issubclass(Opinion, doxa.Opinion)

    def test_propstore_equals_bare_doxa_same_tuple(self):
        ps = Opinion(0.5, 0.2, 0.3, 0.6).with_provenance(PROV_MEASURED)
        kernel = doxa.Opinion(0.5, 0.2, 0.3, 0.6)
        assert ps == kernel
        assert kernel == ps

    def test_provenance_does_not_affect_equality(self):
        with_prov = Opinion(0.5, 0.2, 0.3, 0.6).with_provenance(PROV_MEASURED)
        without_prov = Opinion(0.5, 0.2, 0.3, 0.6)
        assert with_prov == without_prov

    def test_differing_provenance_still_equal(self):
        a = Opinion(0.5, 0.2, 0.3, 0.6).with_provenance(PROV_MEASURED)
        b = Opinion(0.5, 0.2, 0.3, 0.6).with_provenance(PROV_CALIBRATED)
        assert a == b

    def test_cross_type_hash_matches(self):
        ps = Opinion(0.5, 0.2, 0.3, 0.6).with_provenance(PROV_MEASURED)
        kernel = doxa.Opinion(0.5, 0.2, 0.3, 0.6)
        assert hash(ps) == hash(kernel)

    def test_cross_type_set_membership(self):
        ps = Opinion(0.5, 0.2, 0.3, 0.6).with_provenance(PROV_MEASURED)
        kernel = doxa.Opinion(0.5, 0.2, 0.3, 0.6)
        assert kernel in {ps}
        assert ps in {kernel}

    def test_cross_type_dict_lookup(self):
        ps = Opinion(0.5, 0.2, 0.3, 0.6).with_provenance(PROV_MEASURED)
        kernel = doxa.Opinion(0.5, 0.2, 0.3, 0.6)
        assert {ps: "value"}[kernel] == "value"

    def test_unequal_tuples_compare_unequal_across_types(self):
        ps = Opinion(0.5, 0.2, 0.3, 0.6)
        kernel = doxa.Opinion(0.3, 0.3, 0.4, 0.4)
        assert ps != kernel


# ── Provenance status / typing ─────────────────────────────────────────


class TestProvenanceStatusAndTyping:
    """``provenance_status`` and ``with_provenance`` behave as before."""

    def test_provenance_status_exposes_status(self):
        op = Opinion(0.5, 0.2, 0.3, 0.6).with_provenance(PROV_MEASURED)
        assert op.provenance_status == ProvenanceStatus.MEASURED

    def test_provenance_status_raises_without_provenance(self):
        op = Opinion(0.5, 0.2, 0.3, 0.6)
        with pytest.raises(ValueError, match="provenance"):
            _ = op.provenance_status

    def test_with_provenance_returns_new_opinion_with_provenance(self):
        bare = Opinion(0.5, 0.2, 0.3, 0.6)
        stamped = bare.with_provenance(PROV_MEASURED)
        assert stamped is not bare
        assert stamped.provenance is PROV_MEASURED
        assert bare.provenance is None

    def test_with_provenance_preserves_bdua(self):
        bare = Opinion(0.5, 0.2, 0.3, 0.6)
        stamped = bare.with_provenance(PROV_MEASURED)
        assert (stamped.b, stamped.d, stamped.u, stamped.a) == (
            bare.b,
            bare.d,
            bare.u,
            bare.a,
        )

    def test_with_provenance_preserves_allow_dogmatic(self):
        dogmatic = Opinion(1.0, 0.0, 0.0, 0.5, allow_dogmatic=True)
        stamped = dogmatic.with_provenance(PROV_MEASURED)
        assert stamped.allow_dogmatic is True
        assert stamped.provenance is PROV_MEASURED

    def test_provenance_status_reflects_calibrated(self):
        op = Opinion(0.5, 0.2, 0.3, 0.6).with_provenance(PROV_CALIBRATED)
        assert op.provenance_status == ProvenanceStatus.CALIBRATED
