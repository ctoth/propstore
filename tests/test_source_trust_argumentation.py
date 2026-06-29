"""Argumentation-backed source-trust projection (the repository-free core).

Trust rules fire against a source's metadata; the firings are projected into a
Dung framework where attacks defeat supports; the grounded extension decides
which survive; and the survivors map to a subjective-logic opinion — support to
``b``, attack to ``d``, the rest to ``u``, mean base rate to ``a``. When no rule
fires the prior is honestly defaulted, never fabricated.
"""

from __future__ import annotations

import pytest
from doxa import Opinion

from propstore.provenance import ProvenanceStatus
from propstore.source_trust_argumentation import (
    RuleFiring,
    SourceTrustResult,
    project_source_trust,
)

_RULES = [
    {
        "id": "osc-direct-replication",
        "effect": "support",
        "weight": 0.6,
        "base_rate": 0.4,
        "conditions": {"domain": "psychology", "design": "direct"},
    },
    {
        "id": "ioannidis-low-power",
        "effect": "attack",
        "weight": 0.2,
        "base_rate": 0.4,
        "conditions": {"domain": "psychology", "design": "direct"},
    },
]


def test_attack_defeats_support_in_grounded_projection() -> None:
    result = project_source_trust(
        _RULES,
        {"domain": "psychology", "design": "direct"},
        world_snapshot_sha="snapshot",
    )
    assert result.status is ProvenanceStatus.CALIBRATED
    # The attacker survives the grounded extension and defeats the supporter, so
    # belief stays 0, disbelief carries the attacker weight, the rest is unknown.
    assert result.prior_base_rate == Opinion(0.0, 0.2, 0.8, 0.4)
    assert {firing.rule_id for firing in result.derived_from} == {
        "osc-direct-replication",
        "ioannidis-low-power",
    }
    assert all(isinstance(firing, RuleFiring) for firing in result.derived_from)
    assert result.world_snapshot_sha == "snapshot"
    assert result.kernel_version


def test_no_matching_rule_defaults_to_vacuous_prior() -> None:
    result = project_source_trust(_RULES, {"domain": "physics"})
    assert result.status is ProvenanceStatus.DEFAULTED
    assert result.prior_base_rate == Opinion.vacuous(0.5)
    assert result.derived_from == ()


def test_support_only_firing_yields_belief() -> None:
    result = project_source_trust(
        [
            {
                "id": "only-support",
                "effect": "support",
                "weight": 0.7,
                "base_rate": 0.3,
                "conditions": {"domain": "psychology"},
            }
        ],
        {"domain": "psychology"},
    )
    assert result.status is ProvenanceStatus.CALIBRATED
    assert result.prior_base_rate.b == pytest.approx(0.7)
    assert result.prior_base_rate.d == pytest.approx(0.0)
    assert result.prior_base_rate.u == pytest.approx(0.3)
    assert result.prior_base_rate.base_rate == pytest.approx(0.3)


def test_result_is_a_source_trust_result() -> None:
    result = project_source_trust([], {})
    assert isinstance(result, SourceTrustResult)
    assert result.status is ProvenanceStatus.DEFAULTED
