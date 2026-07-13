"""Typed ontology-identity classification and durable alignment documents."""

from __future__ import annotations

from pathlib import Path

from doxa import Opinion
import pytest

from propstore.core.lemon import OntologyReference
from propstore.families.alignment import AlignmentArgument
from propstore.source.alignment import (
    build_alignment_artifact,
    classify_relation,
    load_alignment_artifact,
    save_alignment_artifact,
)


def _argument(
    *,
    argument_id: str,
    name: str,
    definition: str,
    ontology_uri: str | None,
    origin: str = "repo-a",
) -> AlignmentArgument:
    return AlignmentArgument(
        id=argument_id,
        repository_origin=origin,
        source_commit="a" * 40,
        import_branch=f"import/{origin}",
        import_commit="b" * 40,
        concept_id=f"ps:concept:{argument_id}",
        canonical_name=name,
        ontology_reference=(
            None if ontology_uri is None else OntologyReference(uri=ontology_uri)
        ),
        definition=definition,
    )


def test_distinct_ontology_identities_do_not_attack_even_when_names_match() -> None:
    left = _argument(
        argument_id="left",
        name="Mass",
        definition="Quantity of matter.",
        ontology_uri="https://example.org/ontology-a#mass",
    )
    right = _argument(
        argument_id="right",
        name="Mass",
        definition="Resistance to acceleration.",
        ontology_uri="https://example.org/ontology-b#mass",
        origin="repo-b",
    )

    assert classify_relation(left, right) == "non_attack"


def test_shared_ontology_identity_with_conflicting_definitions_attacks() -> None:
    shared_uri = "https://example.org/shared#mass"
    left = _argument(
        argument_id="left",
        name="Mass",
        definition="Quantity of matter.",
        ontology_uri=shared_uri,
    )
    right = _argument(
        argument_id="right",
        name="Masse",
        definition="Resistance to acceleration.",
        ontology_uri=shared_uri,
        origin="repo-b",
    )

    assert classify_relation(left, right) == "attack"


def test_shared_ontology_identity_with_matching_definitions_is_non_attack() -> None:
    shared_uri = "https://example.org/shared#mass"
    left = _argument(
        argument_id="left",
        name="Mass",
        definition="Quantity of matter.",
        ontology_uri=shared_uri,
    )
    right = _argument(
        argument_id="right",
        name="Masse",
        definition="Quantity of matter.",
        ontology_uri=shared_uri,
        origin="repo-b",
    )

    assert classify_relation(left, right) == "non_attack"


def test_vacuous_opinion_is_ignorance() -> None:
    shared_uri = "https://example.org/shared#mass"
    left = _argument(
        argument_id="left",
        name="Mass",
        definition="Quantity of matter.",
        ontology_uri=shared_uri,
    )
    right = _argument(
        argument_id="right",
        name="Masse",
        definition="Resistance to acceleration.",
        ontology_uri=shared_uri,
        origin="repo-b",
    )

    assert (
        classify_relation(left, right, opinion=Opinion(0.0, 0.0, 1.0, 0.5))
        == "ignorance"
    )


def test_build_alignment_artifact_is_order_independent_and_open() -> None:
    left = _argument(
        argument_id="left",
        name="Mass",
        definition="Quantity of matter.",
        ontology_uri="https://example.org/ontology-a#mass",
    )
    right = _argument(
        argument_id="right",
        name="Mass",
        definition="Resistance to acceleration.",
        ontology_uri="https://example.org/ontology-b#mass",
        origin="repo-b",
    )

    forward = build_alignment_artifact([left, right])
    reverse = build_alignment_artifact([right, left])

    assert forward == reverse
    assert forward.decision.status == "open"
    assert forward.framework.attacks == ()
    assert len(forward.framework.non_attacks) == 4
    assert set(forward.queries.credulous_acceptance) == {"left", "right"}
    assert set(forward.queries.skeptical_acceptance) == {"left", "right"}
    assert forward.sources == ("repo-a", "repo-b")


def test_build_alignment_artifact_records_symmetric_attack() -> None:
    shared_uri = "https://example.org/shared#mass"
    left = _argument(
        argument_id="left",
        name="Mass",
        definition="Quantity of matter.",
        ontology_uri=shared_uri,
    )
    right = _argument(
        argument_id="right",
        name="Masse",
        definition="Resistance to acceleration.",
        ontology_uri=shared_uri,
        origin="repo-b",
    )

    artifact = build_alignment_artifact([left, right])

    assert set(artifact.framework.attacks) == {
        ("left", "right"),
        ("right", "left"),
    }


def test_build_alignment_artifact_requires_an_argument() -> None:
    with pytest.raises(ValueError, match="at least one"):
        build_alignment_artifact([])


def test_alignment_artifact_round_trips_through_codec(tmp_path: Path) -> None:
    artifact = build_alignment_artifact(
        [
            _argument(
                argument_id="left",
                name="Mass",
                definition="Quantity of matter.",
                ontology_uri="https://example.org/ontology-a#mass",
            ),
            _argument(
                argument_id="right",
                name="Mass",
                definition="Resistance to acceleration.",
                ontology_uri="https://example.org/ontology-b#mass",
                origin="repo-b",
            ),
        ]
    )
    path = tmp_path / "alignment.yaml"
    save_alignment_artifact(artifact, path)

    assert load_alignment_artifact(path) == artifact
