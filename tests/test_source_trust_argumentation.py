from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.registry import SourceRef
from propstore.opinion import Opinion
from propstore.provenance import ProvenanceStatus
from propstore.repository import Repository
from propstore.source import init_source_branch


def _source(repo: Repository, name: str, metadata: dict[str, object] | None = None) -> None:
    init_source_branch(
        repo,
        name,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value=name,
    )
    if metadata is not None:
        repo.families.source_metadata.save(
            SourceRef(name),
            metadata,
            message=f"Write metadata for {name}",
        )


def test_calibrate_source_trust_uses_stubbed_argumentation_rules(tmp_path: Path) -> None:
    from propstore.source_trust_argumentation import (
        RuleFiring,
        SourceTrustResult,
        calibrate_source_trust,
    )

    repo = Repository.init(tmp_path / "knowledge")
    _source(repo, "rule_satisfying", {"domain": "psychology", "replication": "direct"})
    _source(repo, "no_rule", {"domain": "physics"})

    rules = (
        {
            "id": "ioannidis-low-power",
            "effect": "attack",
            "conditions": {"domain": "psychology", "replication": "direct"},
            "weight": 0.2,
            "base_rate": 0.4,
        },
        {
            "id": "osc-direct-replication",
            "effect": "support",
            "conditions": {"domain": "psychology", "replication": "direct"},
            "weight": 0.6,
            "base_rate": 0.4,
        },
    )

    calibrated = calibrate_source_trust(repo, "rule_satisfying", rule_corpus=rules)
    defaulted = calibrate_source_trust(repo, "no_rule", rule_corpus=rules)

    assert isinstance(calibrated, SourceTrustResult)
    assert calibrated.status is ProvenanceStatus.CALIBRATED
    assert calibrated.prior_base_rate == Opinion(0.0, 0.2, 0.8, 0.4)
    assert {firing.rule_id for firing in calibrated.derived_from} == {
        "ioannidis-low-power",
        "osc-direct-replication",
    }
    assert all(isinstance(firing, RuleFiring) for firing in calibrated.derived_from)
    assert calibrated.world_snapshot_sha
    assert calibrated.kernel_version

    assert defaulted.status is ProvenanceStatus.DEFAULTED
    assert defaulted.prior_base_rate == Opinion.vacuous(0.5)
    assert defaulted.derived_from == ()


@pytest.mark.property
@given(
    domain=st.sampled_from(["psychology", "medicine", "economics"]),
    replication=st.sampled_from(["direct", "conceptual"]),
    effect=st.sampled_from(["support", "attack"]),
    weight=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
    base_rate=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=32)
def test_generated_source_trust_rules_emit_provenanced_argumentation_output(
    domain: str,
    replication: str,
    effect: str,
    weight: float,
    base_rate: float,
) -> None:
    """WS-K property: trust is calibrated by rule firings with provenance."""
    from propstore.source_trust_argumentation import calibrate_source_trust

    with tempfile.TemporaryDirectory() as directory:
        repo = Repository.init(Path(directory) / "knowledge")
        _source(repo, "generated", {"domain": domain, "replication": replication})

        result = calibrate_source_trust(
            repo,
            "generated",
            rule_corpus=(
                {
                    "id": "generated-rule",
                    "effect": effect,
                    "conditions": {"domain": domain, "replication": replication},
                    "weight": weight,
                    "base_rate": base_rate,
                },
            ),
        )

    assert result.status is ProvenanceStatus.CALIBRATED
    assert result.derived_from
    assert result.derived_from[0].rule_id == "generated-rule"
    assert result.derived_from[0].effect == effect
    assert isinstance(result.prior_base_rate, Opinion)
    assert result.prior_base_rate.a == pytest.approx(base_rate)
    assert result.world_snapshot_sha
    assert result.kernel_version
