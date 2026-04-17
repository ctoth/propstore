"""Tests for PRAF worldline argumentation state capture.

When reasoning_backend="praf" and strategy="argumentation", the
result's argumentation field must contain acceptance probabilities
per Li et al. (2011, Def 2, Eq 2).
"""

from __future__ import annotations

import pytest

from propstore.world.types import DerivedResult, ValueResult
from propstore.worldline import WorldlineDefinition, run_worldline


# ── Shared fakes ─────────────────────────────────────────────────────


class FakeBound:
    """Minimal BoundWorld stub for PRAF worldline tests."""

    def __init__(self, claims):
        self._claims = claims
        self._bindings = {}

    def value_of(self, concept_id):
        return ValueResult(
            concept_id=concept_id,
            status="conflicted",
            claims=self._claims,
        )

    def derived_value(self, concept_id, override_values=None):
        return DerivedResult(concept_id=concept_id, status="no_relationship")

    def active_claims(self, concept_id=None):
        return list(self._claims)


class FakeWorld:
    """Minimal WorldModel stub with two conflicting claims and stances.

    Provides the interface that worldline.run_worldline() requires:
    bind, resolve_concept, get_concept, get_claim, has_table, stances_between.
    """

    def __init__(self):
        self._claims = {
            "claim_a": {
                "id": "claim_a",
                "concept": "concept1",
                "value": 10.0,
                "content_hash": "hash-a",
                "claim_probability": 1.0,
                "effective_sample_size": 10,
            },
            "claim_b": {
                "id": "claim_b",
                "concept": "concept1",
                "value": 20.0,
                "content_hash": "hash-b",
                "claim_probability": 1.0,
                "effective_sample_size": 10,
            },
        }

    def bind(self, environment=None, *, policy=None, **conditions):
        claims = [self._claims["claim_a"], self._claims["claim_b"]]
        return FakeBound(claims)

    def resolve_concept(self, name):
        return "concept1" if name == "target" else None

    def get_concept(self, concept_id):
        if concept_id == "concept1":
            return {"id": concept_id, "canonical_name": "target"}
        return None

    def get_claim(self, claim_id):
        return self._claims.get(claim_id)

    def has_table(self, name):
        return name == "relation_edge"

    def claims_by_ids(self, claim_ids):
        return {
            cid: self._claims[cid]
            for cid in claim_ids
            if cid in self._claims
        }

    def stances_between(self, claim_ids):
        if {"claim_a", "claim_b"}.issubset(claim_ids):
            return [
                {
                    "claim_id": "claim_b",
                    "target_claim_id": "claim_a",
                    "stance_type": "rebuts",
                    "confidence": 0.8,
                    "note": "rebuts-note",
                },
            ]
        return []


# ── Tests ────────────────────────────────────────────────────────────


class TestPrafWorldlineStateCapture:
    """Worldline runner must capture PRAF argumentation state.

    When reasoning_backend="praf" and strategy="argumentation", the
    worldline result's argumentation field must contain structured
    PRAF output — not None.

    This is a regression test for the dedicated PRAF capture path.
    """

    def test_praf_argumentation_state_captured(self):
        """PRAF backend must populate argumentation state with required keys.

        Per Li et al. (2011, Def 2): PrAF = (A, P_A, D, P_D).
        The worldline should capture at minimum:
        - backend: "praf"
        - acceptance_probs: dict mapping claim IDs to floats
        - strategy_used: string (e.g. "mc", "exact_enum", "dfquad_quad", "dfquad_baf")
        - semantics: string (e.g. "grounded")
        """
        wl = WorldlineDefinition.from_dict({
            "id": "praf_state_test",
            "targets": ["target"],
            "policy": {
                "strategy": "argumentation",
                "reasoning_backend": "praf",
                "semantics": "grounded",
            },
        })

        world = FakeWorld()
        result = run_worldline(wl, world)

        assert result.argumentation is not None, (
            "PRAF backend produced no argumentation state"
        )
        assert result.argumentation.backend == "praf", (
            f"Expected backend='praf', got {result.argumentation.backend!r}"
        )
        assert isinstance(result.argumentation.acceptance_probs, dict)
        assert isinstance(result.argumentation.strategy_used, str)
        assert isinstance(result.argumentation.semantics, str)

    def test_praf_argumentation_state_has_acceptance_probs(self):
        """PRAF acceptance_probs must contain entries for active claims.

        Per Li et al. (2011, Eq 2): P_PrAF(X) = sum over all inducible
        DAFs of P_PrAF(AF) * xi^S(AF, X). Each claim's acceptance
        probability must be in [0.0, 1.0].
        """
        wl = WorldlineDefinition.from_dict({
            "id": "praf_probs_test",
            "targets": ["target"],
            "policy": {
                "strategy": "argumentation",
                "reasoning_backend": "praf",
                "semantics": "grounded",
            },
        })

        world = FakeWorld()
        result = run_worldline(wl, world)

        # Guard: argumentation state must exist (same failure as test 1)
        assert result.argumentation is not None, (
            "PRAF backend produced no argumentation state"
        )

        probs = result.argumentation.acceptance_probs

        # Both active claims must have acceptance probabilities
        assert "claim_a" in probs, (
            "acceptance_probs missing entry for claim_a"
        )
        assert "claim_b" in probs, (
            "acceptance_probs missing entry for claim_b"
        )

        # Acceptance probabilities must be floats in [0.0, 1.0]
        # (Li et al. 2011, Proposition 1: probabilities form a proper distribution)
        for claim_id, prob in probs.items():
            assert isinstance(prob, float), (
                f"acceptance_probs[{claim_id!r}] should be float, got {type(prob).__name__}"
            )
            assert 0.0 <= prob <= 1.0, (
                f"acceptance_probs[{claim_id!r}] = {prob} is outside [0, 1]"
            )
