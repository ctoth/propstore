from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.core.lemon import (
    CausalAccount,
    CausalConnectionAssertion,
    CoreferenceQuery,
    DescriptionClaim,
    DescriptionKind,
    GradedEntailment,
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
    TypeConstraint,
    causal_transitivity_allowed,
    coerce_via_qualia,
    coreference_query,
    coreference_argument,
    predicted_subject_role,
    proto_agent_weight,
    purposive_chain,
    validate_slot_bindings,
)
from propstore.dung import ArgumentationFramework
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness


_uri_text = st.text(
    alphabet=st.sampled_from(tuple("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:/#._-")),
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
                source_artifact_code="tests:test_lemon_phase3_semantics",
                method=method,
            ),
        ),
    )


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
        GradedEntailment(property=ProtoPatientProperty.AFFECTED, value=value)  # type: ignore[call-arg]


@pytest.mark.parametrize("bad_value", [-0.01, 1.01])
def test_proto_role_entailment_value_bounds_are_enforced(bad_value: float) -> None:
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        GradedEntailment(
            property=ProtoPatientProperty.AFFECTED,
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
                property=ProtoPatientProperty.AFFECTED,
                value=0.8,
                provenance=_provenance("dowty"),
            ),
        )
    )

    assert predicted_subject_role({"observer": observer, "observed": observed}) == "observer"


def test_lexical_sense_carries_phase3_semantic_structure() -> None:
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
    assert isinstance(query.framework, ArgumentationFramework)
    assert query.merge_arguments == (first_second, first_rival)
    assert query.clusters(semantics="grounded") == ()
    assert set(query.clusters(semantics="preferred")) == {
        frozenset({"ps:claim:first", "ps:claim:second"}),
        frozenset({"ps:claim:first", "ps:claim:rival"}),
    }
    assert query.merge_arguments == (first_second, first_rival)


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
