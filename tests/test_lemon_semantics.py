"""Sense-level lemon semantics: Pustejovsky qualia, Dowty proto-roles,
description-kind slots, render-time Dung coreference, Allen temporal via
condition-ir, and account-sensitive causal transitivity.

Ported (behavioral) from the May-16 reference ``test_lemon_phase3_semantics.py``,
repointed to ``propstore.core.lemon`` + the substrate packages
(``argumentation``, ``condition-ir``). The coreference test asserts the central
non-commitment law: coreference clusters CHANGE with the render policy
(argumentation semantics), proving coreference is resolved at render, not stored.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from argumentation.core.dung import ArgumentationFramework

from propstore.core.lemon import (
    AllenRelation,
    AllenVerdict,
    CausalAccount,
    CausalConnectionAssertion,
    CoreferenceQuery,
    DescriptionClaim,
    DescriptionKind,
    DescriptionKindMergeProtocol,
    DescriptionTemporalAnchor,
    GradedEntailment,
    HappensBeforeEdge,
    LexicalSense,
    OntologyReference,
    ParticipantSlot,
    ProtoAgentProperty,
    ProtoPatientProperty,
    ProtoRoleBundle,
    QualiaReference,
    QualiaRole,
    QualiaStructure,
    SlotBinding,
    TemporalFrame,
    TemporalOrderVerdict,
    TypeConstraint,
    causal_transitivity_allowed,
    coerce_via_qualia,
    coreference_argument,
    coreference_query,
    description_temporal_relation,
    predicted_subject_role,
    proto_agent_weight,
    purposive_chain,
    temporal_order,
    validate_slot_bindings,
)
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness


_uri_text = st.text(
    alphabet=st.sampled_from(
        tuple("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:/#._-")
    ),
    min_size=1,
    max_size=30,
)


def _ref(uri: str) -> OntologyReference:
    return OntologyReference(uri=uri)


def _provenance(method: str = "stated") -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(
            ProvenanceWitness(
                asserter="tests",
                timestamp="2026-04-17T00:00:00Z",
                source_artifact_code="tests:test_lemon_semantics",
                method=method,
            ),
        ),
    )


# --- Pustejovsky qualia -----------------------------------------------------


@pytest.mark.property
@given(source_uri=_uri_text, target_uri=_uri_text)
@settings(deadline=None)
def test_qualia_coercion_returns_view_satisfying_target_type(
    source_uri: str,
    target_uri: str,
) -> None:
    if source_uri == target_uri:
        return
    target_type = TypeConstraint(reference=_ref(target_uri))
    qualia = QualiaStructure(
        telic=(
            QualiaReference(
                reference=_ref(source_uri),
                type_constraint=target_type,
                provenance=_provenance("telic"),
            ),
        )
    )

    coerced = coerce_via_qualia(qualia, target_type)

    assert coerced is not None
    assert coerced.target_type.reference.uri == target_uri
    assert coerced.reference.uri == source_uri
    assert coerced.role_path == (QualiaRole.TELIC,)
    assert "qualia_coercion:telic" in coerced.provenance.operations


@pytest.mark.property
@given(first_uri=_uri_text, second_uri=_uri_text, third_uri=_uri_text)
@settings(deadline=None)
def test_telic_qualia_chain_is_recoverable(
    first_uri: str,
    second_uri: str,
    third_uri: str,
) -> None:
    if len({first_uri, second_uri, third_uri}) < 3:
        return
    graph = {
        first_uri: QualiaStructure(
            telic=(QualiaReference(reference=_ref(second_uri), provenance=_provenance("telic")),)
        ),
        second_uri: QualiaStructure(
            telic=(QualiaReference(reference=_ref(third_uri), provenance=_provenance("telic")),)
        ),
    }

    assert purposive_chain(_ref(first_uri), graph) == (_ref(second_uri), _ref(third_uri))


# --- Dowty proto-roles ------------------------------------------------------


@pytest.mark.property
@given(value=st.floats(allow_nan=False, allow_infinity=False, min_value=0.0, max_value=1.0))
@settings(deadline=None)
def test_proto_role_entailments_are_graded_and_provenance_bearing(value: float) -> None:
    entailment = GradedEntailment(
        property=ProtoAgentProperty.VOLITION,
        value=value,
        provenance=_provenance("dowty"),
    )
    bundle = ProtoRoleBundle(proto_agent_entailments=(entailment,))

    assert proto_agent_weight(bundle) == value
    with pytest.raises(TypeError):
        GradedEntailment(property=ProtoPatientProperty.CAUSALLY_AFFECTED, value=value)  # type: ignore[call-arg]


@pytest.mark.parametrize("bad_value", [-0.01, 1.01])
def test_proto_role_entailment_value_bounds_are_enforced(bad_value: float) -> None:
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        GradedEntailment(
            property=ProtoPatientProperty.CAUSALLY_AFFECTED,
            value=bad_value,
            provenance=_provenance("dowty"),
        )


def test_dowty_argument_selection_prefers_highest_proto_agent_weight() -> None:
    observer = ProtoRoleBundle(
        proto_agent_entailments=(
            GradedEntailment(
                property=ProtoAgentProperty.SENTIENCE,
                value=0.7,
                provenance=_provenance("dowty"),
            ),
            GradedEntailment(
                property=ProtoAgentProperty.VOLITION,
                value=0.2,
                provenance=_provenance("dowty"),
            ),
        )
    )
    observed = ProtoRoleBundle(
        proto_patient_entailments=(
            GradedEntailment(
                property=ProtoPatientProperty.CAUSALLY_AFFECTED,
                value=0.8,
                provenance=_provenance("dowty"),
            ),
        )
    )

    assert predicted_subject_role({"observer": observer, "observed": observed}) == "observer"


# --- description kinds + sense semantic content -----------------------------


def test_lexical_sense_carries_semantic_structure() -> None:
    target_type = TypeConstraint(reference=_ref("tag:propstore:test:type/activity"))
    qualia = QualiaStructure(
        telic=(
            QualiaReference(
                reference=_ref("tag:propstore:test/activity/measure"),
                type_constraint=target_type,
                provenance=_provenance("pustejovsky"),
            ),
        )
    )
    bundle = ProtoRoleBundle(
        proto_agent_entailments=(
            GradedEntailment(
                property=ProtoAgentProperty.CAUSATION,
                value=0.8,
                provenance=_provenance("dowty"),
            ),
        )
    )
    description_kind = DescriptionKind(
        name="Measurement",
        reference=_ref("tag:propstore:test/description-kind/measurement"),
        slots=(
            ParticipantSlot(
                name="instrument",
                type_constraint=_ref("tag:propstore:test/type/instrument"),
                proto_role_bundle=bundle,
            ),
        ),
    )

    sense = LexicalSense(
        reference=_ref("tag:propstore:test/concept/measurement"),
        qualia=qualia,
        description_kind=description_kind,
        role_bundles={"instrument": bundle},
    )

    assert sense.qualia is qualia
    assert sense.description_kind is description_kind
    assert sense.role_bundles == {"instrument": bundle}


def test_description_kind_slot_bindings_enforce_type_constraints() -> None:
    kind = DescriptionKind(
        name="Measurement",
        reference=_ref("tag:propstore:test:description-kind/measurement"),
        slots=(
            ParticipantSlot(
                name="instrument",
                type_constraint=_ref("tag:propstore:test:type/instrument"),
            ),
        ),
    )
    valid = SlotBinding(
        slot="instrument",
        value=_ref("tag:propstore:test:instrument/caliper"),
        value_type=_ref("tag:propstore:test:type/instrument"),
        provenance=_provenance("measurement"),
    )
    invalid = SlotBinding(
        slot="instrument",
        value=_ref("tag:propstore:test:person/alice"),
        value_type=_ref("tag:propstore:test:type/person"),
        provenance=_provenance("measurement"),
    )

    assert validate_slot_bindings(kind, (valid,)).ok
    assert not validate_slot_bindings(kind, (invalid,)).ok


# --- coreference: an argument, not a fact; clusters depend on render policy --


def test_coreference_between_description_claims_is_an_argument_not_a_fact() -> None:
    kind = DescriptionKind(
        name="Observation",
        reference=_ref("tag:propstore:test:description-kind/observation"),
        slots=(),
    )
    first = DescriptionClaim(
        claim_id="ps:claim:first",
        kind=kind,
        bindings=(),
        provenance=_provenance("observation"),
    )
    second = DescriptionClaim(
        claim_id="ps:claim:second",
        kind=kind,
        bindings=(),
        provenance=_provenance("observation"),
    )

    argument = coreference_argument(
        first,
        second,
        argument_id="arg:merge:first-second",
        provenance=_provenance("merge-hypothesis"),
    )

    assert argument.description_claim_ids == ("ps:claim:first", "ps:claim:second")
    assert argument.supports == ("ps:claim:first", "ps:claim:second")


def test_coreference_query_is_dung_argumentation_with_policy_dependent_clusters() -> None:
    kind = DescriptionKind(
        name="Observation",
        reference=_ref("tag:propstore:test:description-kind/observation"),
        slots=(),
    )
    first = DescriptionClaim(
        claim_id="ps:claim:first",
        kind=kind,
        bindings=(),
        provenance=_provenance("observation"),
    )
    second = DescriptionClaim(
        claim_id="ps:claim:second",
        kind=kind,
        bindings=(),
        provenance=_provenance("observation"),
    )
    rival = DescriptionClaim(
        claim_id="ps:claim:rival",
        kind=kind,
        bindings=(),
        provenance=_provenance("observation"),
    )
    first_second = coreference_argument(
        first,
        second,
        argument_id="arg:first-second",
        provenance=_provenance("merge-hypothesis"),
    )
    first_rival = coreference_argument(
        first,
        rival,
        argument_id="arg:first-rival",
        provenance=_provenance("merge-hypothesis"),
    )

    query = coreference_query(
        (first_second, first_rival),
        attacks=(("arg:first-second", "arg:first-rival"), ("arg:first-rival", "arg:first-second")),
    )

    assert isinstance(query, CoreferenceQuery)
    assert isinstance(query.protocol, DescriptionKindMergeProtocol)
    assert isinstance(query.framework, ArgumentationFramework)
    assert query.merge_arguments == (first_second, first_rival)

    # Sceptical (grounded): mutually-attacking merges support NO coreference.
    assert query.clusters(semantics="grounded") == ()
    # Credulous (preferred): the SAME stored arguments yield rival clusters.
    assert set(query.clusters(semantics="preferred")) == {
        frozenset({"ps:claim:first", "ps:claim:second"}),
        frozenset({"ps:claim:first", "ps:claim:rival"}),
    }
    # The render computed both; storage was never collapsed to one.
    assert query.merge_arguments == (first_second, first_rival)


# --- Allen temporal reduces to TIMEPOINT/Z3 via condition-ir ----------------


def _frame(frame_id: str) -> TemporalFrame:
    return TemporalFrame(
        frame_id=frame_id,
        description=f"declared frame {frame_id}",
        provenance=_provenance("temporal-frame"),
    )


@pytest.mark.property
@given(
    start=st.floats(allow_nan=False, allow_infinity=False, min_value=-1_000_000, max_value=1_000_000),
    first_width=st.floats(allow_nan=False, allow_infinity=False, min_value=1.0, max_value=10_000.0),
    gap=st.floats(allow_nan=False, allow_infinity=False, min_value=1.0, max_value=10_000.0),
    second_width=st.floats(allow_nan=False, allow_infinity=False, min_value=1.0, max_value=10_000.0),
)
@settings(deadline=None, max_examples=25)
def test_fully_bound_same_frame_reproduces_allen_truths(
    start: float,
    first_width: float,
    gap: float,
    second_width: float,
) -> None:
    """(1) Fully-bound same-frame anchors reproduce the old HOLDS/FAILS truths."""

    frame = _frame("clock-A")
    first = DescriptionTemporalAnchor(
        claim_id="ps:claim:first",
        frame=frame,
        valid_from=start,
        valid_until=start + first_width,
        provenance=_provenance("temporal-anchor"),
    )
    second = DescriptionTemporalAnchor(
        claim_id="ps:claim:second",
        frame=frame,
        valid_from=start + first_width + gap,
        valid_until=start + first_width + gap + second_width,
        provenance=_provenance("temporal-anchor"),
    )

    assert (
        description_temporal_relation(first, second, AllenRelation.BEFORE)
        is AllenVerdict.HOLDS
    )
    assert (
        description_temporal_relation(first, second, AllenRelation.OVERLAPS)
        is AllenVerdict.FAILS
    )


def test_missing_bound_yields_undecided_where_bounds_do_not_decide() -> None:
    """(2a) A fully-open right anchor leaves BEFORE undecided."""

    frame = _frame("clock-A")
    left = DescriptionTemporalAnchor(
        claim_id="ps:claim:left",
        frame=frame,
        valid_from=0.0,
        valid_until=3.0,
        provenance=_provenance("temporal-anchor"),
    )
    right = DescriptionTemporalAnchor(
        claim_id="ps:claim:right",
        frame=frame,
        provenance=_provenance("temporal-anchor"),
    )

    assert (
        description_temporal_relation(left, right, AllenRelation.BEFORE)
        is AllenVerdict.UNDECIDED
    )


def test_partial_bounds_can_still_decide_holds() -> None:
    """(2b) left_until=3, right_from=5 decides BEFORE HOLDS with the other two free."""

    frame = _frame("clock-A")
    left = DescriptionTemporalAnchor(
        claim_id="ps:claim:left",
        frame=frame,
        valid_until=3.0,
        provenance=_provenance("temporal-anchor"),
    )
    right = DescriptionTemporalAnchor(
        claim_id="ps:claim:right",
        frame=frame,
        valid_from=5.0,
        provenance=_provenance("temporal-anchor"),
    )

    assert (
        description_temporal_relation(left, right, AllenRelation.BEFORE)
        is AllenVerdict.HOLDS
    )


def test_partial_bounds_can_still_decide_fails() -> None:
    """(2c) left_from=5, right_until=3 decides BEFORE FAILS with the other two free."""

    frame = _frame("clock-A")
    left = DescriptionTemporalAnchor(
        claim_id="ps:claim:left",
        frame=frame,
        valid_from=5.0,
        provenance=_provenance("temporal-anchor"),
    )
    right = DescriptionTemporalAnchor(
        claim_id="ps:claim:right",
        frame=frame,
        valid_until=3.0,
        provenance=_provenance("temporal-anchor"),
    )

    assert (
        description_temporal_relation(left, right, AllenRelation.BEFORE)
        is AllenVerdict.FAILS
    )


def test_cross_frame_allen_query_raises() -> None:
    """(3) Allen relations are frame-local; a cross-frame query is a category error."""

    left = DescriptionTemporalAnchor(
        claim_id="ps:claim:left",
        frame=_frame("clock-A"),
        valid_from=0.0,
        valid_until=1.0,
        provenance=_provenance("temporal-anchor"),
    )
    right = DescriptionTemporalAnchor(
        claim_id="ps:claim:right",
        frame=_frame("clock-B"),
        valid_from=0.0,
        valid_until=1.0,
        provenance=_provenance("temporal-anchor"),
    )

    with pytest.raises(ValueError, match="frame-local"):
        description_temporal_relation(left, right, AllenRelation.BEFORE)


def test_authored_edges_transitively_order_across_frames() -> None:
    """(4) Authored happens-before edges + transitivity yield BEFORE / AFTER cross-frame."""

    a_before_b = HappensBeforeEdge(
        edge_id="e:ab",
        earlier_claim_id="ps:claim:a",
        later_claim_id="ps:claim:b",
        provenance=_provenance("happens-before"),
    )
    b_before_c = HappensBeforeEdge(
        edge_id="e:bc",
        earlier_claim_id="ps:claim:b",
        later_claim_id="ps:claim:c",
        provenance=_provenance("happens-before"),
    )
    edges = (a_before_b, b_before_c)

    assert (
        temporal_order("ps:claim:a", "ps:claim:c", anchors=(), edges=edges)
        is TemporalOrderVerdict.BEFORE
    )
    assert (
        temporal_order("ps:claim:c", "ps:claim:a", anchors=(), edges=edges)
        is TemporalOrderVerdict.AFTER
    )


def test_cyclic_edges_are_conflicted() -> None:
    """(5) Rival orderings (a->b and b->a) surface as CONFLICTED, never tie-broken."""

    edges = (
        HappensBeforeEdge(
            edge_id="e:ab",
            earlier_claim_id="ps:claim:a",
            later_claim_id="ps:claim:b",
            provenance=_provenance("happens-before"),
        ),
        HappensBeforeEdge(
            edge_id="e:ba",
            earlier_claim_id="ps:claim:b",
            later_claim_id="ps:claim:a",
            provenance=_provenance("happens-before"),
        ),
    )

    assert (
        temporal_order("ps:claim:a", "ps:claim:b", anchors=(), edges=edges)
        is TemporalOrderVerdict.CONFLICTED
    )


def test_overlapping_same_frame_intervals_are_concurrent() -> None:
    """(6) Overlapping bounded intervals prove CONCURRENT even open-world."""

    frame = _frame("clock-A")
    left = DescriptionTemporalAnchor(
        claim_id="ps:claim:left",
        frame=frame,
        valid_from=0.0,
        valid_until=10.0,
        provenance=_provenance("temporal-anchor"),
    )
    right = DescriptionTemporalAnchor(
        claim_id="ps:claim:right",
        frame=frame,
        valid_from=5.0,
        valid_until=15.0,
        provenance=_provenance("temporal-anchor"),
    )

    assert (
        temporal_order(
            "ps:claim:left",
            "ps:claim:right",
            anchors=(left, right),
            edges=(),
            assume_complete=False,
        )
        is TemporalOrderVerdict.CONCURRENT
    )


def test_cross_frame_no_edges_is_unknown_but_concurrent_when_complete() -> None:
    """(7) Cross-frame with no evidence: UNKNOWN by default, CONCURRENT when declared complete."""

    left = DescriptionTemporalAnchor(
        claim_id="ps:claim:left",
        frame=_frame("clock-A"),
        valid_from=0.0,
        valid_until=1.0,
        provenance=_provenance("temporal-anchor"),
    )
    right = DescriptionTemporalAnchor(
        claim_id="ps:claim:right",
        frame=_frame("clock-B"),
        valid_from=0.0,
        valid_until=1.0,
        provenance=_provenance("temporal-anchor"),
    )
    anchors = (left, right)

    assert (
        temporal_order(
            "ps:claim:left", "ps:claim:right", anchors=anchors, edges=()
        )
        is TemporalOrderVerdict.UNKNOWN
    )
    assert (
        temporal_order(
            "ps:claim:left",
            "ps:claim:right",
            anchors=anchors,
            edges=(),
            assume_complete=True,
        )
        is TemporalOrderVerdict.CONCURRENT
    )


def test_one_sided_bounds_construct_but_misorder_raises() -> None:
    """(8) Only-from / only-until anchors construct; both-present misorder still raises."""

    frame = _frame("clock-A")
    DescriptionTemporalAnchor(
        claim_id="ps:claim:from-only",
        frame=frame,
        valid_from=5.0,
        provenance=_provenance("temporal-anchor"),
    )
    DescriptionTemporalAnchor(
        claim_id="ps:claim:until-only",
        frame=frame,
        valid_until=5.0,
        provenance=_provenance("temporal-anchor"),
    )

    with pytest.raises(ValueError, match="valid_from <= valid_until"):
        DescriptionTemporalAnchor(
            claim_id="ps:claim:misordered",
            frame=frame,
            valid_from=10.0,
            valid_until=1.0,
            provenance=_provenance("temporal-anchor"),
        )


def test_happens_before_edge_rejects_self_loop() -> None:
    """A happens-before posit must relate two distinct descriptions."""

    with pytest.raises(ValueError, match="distinct"):
        HappensBeforeEdge(
            edge_id="e:self",
            earlier_claim_id="ps:claim:a",
            later_claim_id="ps:claim:a",
            provenance=_provenance("happens-before"),
        )


# --- causal transitivity is account-sensitive -------------------------------


def test_causal_connection_transitivity_is_account_sensitive() -> None:
    stated_one = CausalConnectionAssertion(
        cause_description_id="a",
        effect_description_id="b",
        account=CausalAccount.STATED,
        provenance=_provenance("causal"),
    )
    stated_two = CausalConnectionAssertion(
        cause_description_id="b",
        effect_description_id="c",
        account=CausalAccount.STATED,
        provenance=_provenance("causal"),
    )
    mechanistic_two = CausalConnectionAssertion(
        cause_description_id="b",
        effect_description_id="c",
        account=CausalAccount.MECHANISTIC,
        provenance=_provenance("causal"),
    )
    mechanistic_one = CausalConnectionAssertion(
        cause_description_id="a",
        effect_description_id="b",
        account=CausalAccount.MECHANISTIC,
        provenance=_provenance("causal"),
    )

    assert not causal_transitivity_allowed(stated_one, stated_two)
    assert not causal_transitivity_allowed(stated_one, mechanistic_two)
    assert causal_transitivity_allowed(mechanistic_one, mechanistic_two)
