"""Phase 6d ``SameAs`` charter: the graded-identity vocabulary, the columns that
fall out of the one charter, and the defeasible opinion round-trip.

Rewritten from the reference ``test_sameas_family_schema`` to the rewrite's charter
shape: there is no ``PROPSTORE_FAMILY_REGISTRY`` / ``DocumentStruct`` / ``to_payload``
second spelling — the family name and the sidecar columns come straight off the
charter, exactly as for ``Stance``.
"""

from __future__ import annotations

from doxa import Opinion

from propstore.families.sameas import SameAs, SameAsRelation


def test_sameas_family_name_is_same_as_assertion() -> None:
    assert SameAs.__charter__.family.artifact_family.name == "same_as_assertion"


def test_sameas_relation_exposes_graded_identity_vocab() -> None:
    assert {relation.value for relation in SameAsRelation} == {
        "sim:sameIndividual",
        "sim:claimsIdentical",
        "sim:almostSameAs",
    }


def test_sameas_columns_fall_out_of_the_charter() -> None:
    schema_object = SameAs.__charter__.to_schema_object()
    column_names = {field.name for field in schema_object.fields}
    assert {
        "sameas_id",
        "left_artifact_id",
        "right_artifact_id",
        "relation",
        "evidence_source",
        "opinion_belief",
        "opinion_disbelief",
        "opinion_uncertainty",
        "opinion_base_rate",
    } <= column_names


def test_sameas_assertion_carries_relation_and_evidence() -> None:
    assertion = SameAs(
        sameas_id="ps:sameas:edge",
        left_artifact_id="ps:claim:left",
        right_artifact_id="ps:claim:right",
        relation=SameAsRelation.CLAIMS_IDENTICAL,
        evidence_source="paper_a",
    )

    assert assertion.relation is SameAsRelation.CLAIMS_IDENTICAL
    assert assertion.evidence_source == "paper_a"
    # defeasible: no fabricated strength when none was authored
    assert assertion.opinion() is None


def test_sameas_opinion_rebuilds_doxa_opinion() -> None:
    assertion = SameAs(
        sameas_id="ps:sameas:edge",
        left_artifact_id="ps:claim:left",
        right_artifact_id="ps:claim:right",
        relation=SameAsRelation.ALMOST_SAME_AS,
        opinion_belief=0.6,
        opinion_disbelief=0.2,
        opinion_uncertainty=0.2,
        opinion_base_rate=0.5,
    )

    assert assertion.opinion() == Opinion(0.6, 0.2, 0.2, 0.5)


def test_partial_sameas_opinion_is_treated_as_absent() -> None:
    assertion = SameAs(
        sameas_id="ps:sameas:edge",
        left_artifact_id="ps:claim:left",
        right_artifact_id="ps:claim:right",
        opinion_belief=0.6,
    )

    assert assertion.opinion() is None
