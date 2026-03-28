"""Red tests: PRAF worldline argumentation state capture.

Phase 6: worldline_runner.py captures argumentation state for claim_graph,
structured_projection, and atms backends but has NO branch for praf.
When reasoning_backend="praf", the argumentation_state is None.

These tests assert that when a worldline uses reasoning_backend="praf"
with strategy="argumentation", the result's argumentation field contains
acceptance probabilities per Li et al. (2011, Def 2, Eq 2).

Both tests should FAIL until the praf branch is implemented in
worldline_runner.py (around lines 250-257).
"""

from __future__ import annotations

import pytest

from propstore.world.types import DerivedResult, ValueResult
from propstore.worldline import WorldlineDefinition
from propstore.worldline_runner import run_worldline


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

    Provides the interface that worldline_runner.run_worldline() requires:
    bind, resolve_concept, get_concept, get_claim, has_table, stances_between.
    """

    def __init__(self):
        self._claims = {
            "claim_a": {
                "id": "claim_a",
                "concept": "concept1",
                "value": 10.0,
                "content_hash": "hash-a",
            },
            "claim_b": {
                "id": "claim_b",
                "concept": "concept1",
                "value": 20.0,
                "content_hash": "hash-b",
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

    Currently FAILS because worldline_runner.py has branches for
    claim_graph, structured_projection, and atms but not praf.
    """

    def test_praf_argumentation_state_captured(self):
        """PRAF backend must populate argumentation state with required keys.

        Per Li et al. (2011, Def 2): PrAF = (A, P_A, D, P_D).
        The worldline should capture at minimum:
        - backend: "praf"
        - acceptance_probs: dict mapping claim IDs to floats
        - strategy_used: string (e.g. "mc", "exact", "dfquad_quad", "dfquad_baf")
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

        # The argumentation field must not be None — this is the core assertion
        # that fails because worldline_runner.py has no praf branch.
        assert result.argumentation is not None, (
            "PRAF backend produced no argumentation state; "
            "worldline_runner.py needs a branch for reasoning_backend='praf'"
        )
        assert result.argumentation.get("backend") == "praf", (
            f"Expected backend='praf', got {result.argumentation.get('backend')!r}"
        )
        assert "acceptance_probs" in result.argumentation, (
            "PRAF argumentation state must include acceptance_probs "
            "(Li et al. 2011, Eq 2: acceptance probability per argument)"
        )
        assert isinstance(result.argumentation["acceptance_probs"], dict)
        assert "strategy_used" in result.argumentation, (
            "PRAF argumentation state must report which strategy was used "
            "(mc, exact, dfquad_quad, or dfquad_baf)"
        )
        assert isinstance(result.argumentation["strategy_used"], str)
        assert "semantics" in result.argumentation, (
            "PRAF argumentation state must report the Dung semantics used"
        )
        assert isinstance(result.argumentation["semantics"], str)

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

        probs = result.argumentation.get("acceptance_probs", {})

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
