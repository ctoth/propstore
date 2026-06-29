"""Phase 6d concept-alignment math: classification by lemon identity (never string
tokens), the PAF-backed alignment artifact, and repo-free serialization.

The default classification keeps distinct proposals non-attacking and only conflicts
proposals that share a lemon identity but disagree on definition — vocabulary
reconciliation by identity, per CLAUDE.md. A vacuous opinion yields honest
``ignorance`` rather than a fabricated verdict.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from doxa import Opinion

from propstore.source.alignment import (
    build_alignment_artifact,
    classify_relation,
    load_alignment_artifact,
    save_alignment_artifact,
)


def _proposal(
    *,
    handle: str,
    name: str,
    definition: str,
    uri: str | None = None,
    source: str = "paper",
    form: str = "structural",
) -> dict[str, str]:
    payload = {
        "local_handle": handle,
        "proposed_name": name,
        "definition": definition,
        "form": form,
        "source": source,
    }
    if uri is not None:
        payload["proposed_uri"] = uri
    return payload


def test_alignment_default_keeps_distinct_conflicting_proposals_non_attacking() -> None:
    left = _proposal(
        handle="velocity",
        name="velocity",
        definition="Distance traveled per unit time.",
    )
    right = _proposal(
        handle="speed",
        name="speed",
        definition="A scalar magnitude without direction.",
    )

    assert classify_relation(left, right) == "non_attack"


def test_alignment_shared_reference_classifies_conflicting_definitions_as_attack() -> None:
    shared_uri = "tag:example.org,2026:concept/motion"
    left = _proposal(
        handle="motion_a",
        name="motion a",
        definition="A vector-valued rate of change.",
        uri=shared_uri,
    )
    right = _proposal(
        handle="motion_b",
        name="motion b",
        definition="A scalar displacement magnitude.",
        uri=shared_uri,
    )

    assert classify_relation(left, right) == "attack"


def test_alignment_shared_reference_with_matching_definitions_is_non_attack() -> None:
    shared_uri = "tag:example.org,2026:concept/motion"
    left = _proposal(
        handle="motion_a",
        name="motion a",
        definition="A vector-valued rate of change.",
        uri=shared_uri,
    )
    right = _proposal(
        handle="motion_b",
        name="motion b",
        definition="A vector-valued rate of change.",
        uri=shared_uri,
    )

    assert classify_relation(left, right) == "non_attack"


def test_classification_uses_identity_not_token_overlap() -> None:
    # Heavily overlapping tokens but distinct lemon identity (different name, handle,
    # and minted reference) must NOT attack: reconciliation is by identity, never
    # by Jaccard/token similarity.
    left = _proposal(
        handle="signal_to_noise_ratio",
        name="signal to noise ratio",
        definition="Ratio of signal power to noise power.",
    )
    right = _proposal(
        handle="signal_to_noise_margin",
        name="signal to noise margin",
        definition="Headroom of signal over noise.",
    )

    assert classify_relation(left, right) == "non_attack"


def test_vacuous_opinion_relation_is_ignorance() -> None:
    shared_uri = "tag:example.org,2026:concept/motion"
    relation = {
        "left": _proposal(
            handle="motion_a",
            name="motion a",
            definition="A vector-valued rate of change.",
            uri=shared_uri,
        ),
        "right": _proposal(
            handle="motion_b",
            name="motion b",
            definition="A scalar displacement magnitude.",
            uri=shared_uri,
        ),
        "opinion": Opinion(0.0, 0.0, 1.0, 0.5),
    }

    assert classify_relation(relation) == "ignorance"


def test_build_alignment_artifact_partitions_pairs_and_records_acceptance() -> None:
    velocity = _proposal(
        handle="velocity",
        name="velocity",
        definition="Distance per unit time.",
        source="paper_a",
    )
    speed = _proposal(
        handle="speed",
        name="speed",
        definition="A scalar magnitude.",
        source="paper_b",
    )

    artifact = build_alignment_artifact([velocity, speed])

    assert artifact.alignment_id == "align:velocity"
    arg_ids = {argument.id for argument in artifact.arguments}
    assert arg_ids == {"alt_velocity", "alt_speed"}
    # distinct words never attack; every pair is non-attack (incl. the two self pairs)
    assert artifact.framework.attacks == ()
    assert len(artifact.framework.non_attacks) == 4
    assert set(artifact.queries.credulous_acceptance) == arg_ids
    assert set(artifact.queries.skeptical_acceptance) == arg_ids
    assert set(artifact.queries.operator_scores) == {"sum", "max", "leximax"}
    assert artifact.decision.status == "open"
    # proposal-only: the artifact records both rivals, collapses neither
    assert set(artifact.sources) == {"paper_a", "paper_b"}


def test_build_alignment_artifact_attacks_conflicting_shared_reference() -> None:
    shared = "tag:example.org,2026:concept/motion"
    left = _proposal(
        handle="motion",
        name="motion",
        definition="A vector-valued rate of change.",
        uri=shared,
        source="paper_a",
    )
    right = _proposal(
        handle="motion",
        name="motion",
        definition="A scalar displacement magnitude.",
        uri=shared,
        source="paper_b",
    )

    artifact = build_alignment_artifact([left, right])

    # same handle -> ids collide and are disambiguated
    assert [argument.id for argument in artifact.arguments] == [
        "alt_motion",
        "alt_motion_2",
    ]
    assert set(artifact.framework.attacks) == {
        ("alt_motion", "alt_motion_2"),
        ("alt_motion_2", "alt_motion"),
    }


def test_build_alignment_artifact_requires_a_proposal() -> None:
    with pytest.raises(ValueError, match="at least one proposal"):
        build_alignment_artifact([])


def test_alignment_artifact_round_trips_through_codec(tmp_path: Path) -> None:
    artifact = build_alignment_artifact(
        [
            _proposal(handle="velocity", name="velocity", definition="d/t"),
            _proposal(handle="speed", name="speed", definition="scalar"),
        ]
    )
    path = tmp_path / "alignment.yaml"
    save_alignment_artifact(artifact, path)

    assert load_alignment_artifact(path) == artifact
