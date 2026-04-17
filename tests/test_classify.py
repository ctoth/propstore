"""Tests for propstore.classify — classifier extraction from relate.py.

Tests the LLM stance classifier as a pure function: (claim_a, claim_b, context) -> [forward, reverse].
Verifies structural invariants, error handling, opinion algebra wiring, enrichment context,
and bidirectional completeness.

Literature grounding:
- Josang 2001 (p.8, Def 9): vacuous opinion (0,0,1,a) = total ignorance
- Josang 2001 (p.5, Def 6): E(w) = b + a*u
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from propstore.stances import VALID_STANCE_TYPES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_claim(id_: str, text: str = "some claim", source: str = "paper") -> dict:
    return {"id": id_, "text": text, "source_paper": source}


def _mock_bidirectional_response(forward: dict, reverse: dict) -> MagicMock:
    """Build a mock litellm response returning bidirectional JSON."""
    resp = MagicMock()
    msg = MagicMock()
    msg.content = json.dumps({"forward": forward, "reverse": reverse})
    choice = MagicMock()
    choice.message = msg
    resp.choices = [choice]
    return resp


def _mock_llm_response(payload: dict) -> MagicMock:
    """Build a mock litellm response returning the given JSON payload."""
    resp = MagicMock()
    msg = MagicMock()
    msg.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = msg
    resp.choices = [choice]
    return resp


def _run(coro):
    return asyncio.run(coro)


def _default_forward():
    return {"type": "supports", "strength": "strong", "note": "corroborates", "conditions_differ": None}


def _default_reverse():
    return {"type": "none", "strength": "weak", "note": "unrelated", "conditions_differ": None}


# ---------------------------------------------------------------------------
# Example tests: bidirectional output
# ---------------------------------------------------------------------------

class TestClassifyReturnsBidirectional:
    """classify_stance_async returns list of two stance dicts (forward + reverse)."""

    def test_returns_two_stances(self):
        from propstore.classify import classify_stance_async

        resp = _mock_bidirectional_response(_default_forward(), _default_reverse())
        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "test-model", sem,
            ))

        assert isinstance(results, list)
        assert len(results) == 2

    def test_forward_targets_b(self):
        from propstore.classify import classify_stance_async

        resp = _mock_bidirectional_response(_default_forward(), _default_reverse())
        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "test-model", sem,
            ))

        assert results[0]["target"] == "b"

    def test_reverse_targets_a(self):
        from propstore.classify import classify_stance_async

        resp = _mock_bidirectional_response(_default_forward(), _default_reverse())
        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "test-model", sem,
            ))

        assert results[1]["target"] == "a"

    def test_each_has_required_keys(self):
        from propstore.classify import classify_stance_async

        resp = _mock_bidirectional_response(_default_forward(), _default_reverse())
        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "test-model", sem,
            ))

        required = {"target", "type", "strength", "note", "conditions_differ", "resolution"}
        for r in results:
            assert required.issubset(r.keys()), f"Missing keys: {required - r.keys()}"

    def test_resolution_has_opinion_keys(self):
        from propstore.classify import classify_stance_async

        fwd = {"type": "rebuts", "strength": "moderate", "note": "contradicts", "conditions_differ": None}
        rev = {"type": "supports", "strength": "weak", "note": "partial", "conditions_differ": None}
        resp = _mock_bidirectional_response(fwd, rev)
        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "test-model", sem,
            ))

        for r in results:
            if r["type"] != "none":
                res = r["resolution"]
                assert set(res["opinion"]) == {"b", "d", "u", "a"}


# ---------------------------------------------------------------------------
# Example tests: error handling (returns two error stances)
# ---------------------------------------------------------------------------

class TestClassifyErrorOnApiFailure:
    def test_api_exception_returns_error_type(self):
        from propstore.classify import classify_stance_async

        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(side_effect=ConnectionError("timeout"))
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "test-model", sem,
            ))

        assert isinstance(results, list)
        assert len(results) == 2
        for r in results:
            assert r["type"] == "error"
            assert r["resolution"]["confidence"] == 0.0

    def test_unexpected_runtime_error_propagates(self):
        from propstore.classify import classify_stance_async

        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(side_effect=RuntimeError("boom"))
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            with pytest.raises(RuntimeError, match="boom"):
                _run(classify_stance_async(
                    _make_claim("a"), _make_claim("b"), "test-model", sem,
                    embedding_model="embed-model",
                    embedding_distance=0.5,
                ))


class TestClassifyErrorOnBadJson:
    def test_json_parse_failure_returns_error(self):
        from propstore.classify import classify_stance_async

        resp = MagicMock()
        msg = MagicMock()
        msg.content = "not json at all {{"
        choice = MagicMock()
        choice.message = msg
        resp.choices = [choice]

        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "test-model", sem,
            ))

        assert isinstance(results, list)
        for r in results:
            assert r["type"] == "error"


class TestClassifyNoneGetsZeroConfidence:
    def test_none_type_zero_confidence(self):
        from propstore.classify import classify_stance_async

        fwd = {"type": "none", "strength": "weak", "note": "unrelated", "conditions_differ": None}
        rev = {"type": "none", "strength": "weak", "note": "unrelated", "conditions_differ": None}
        resp = _mock_bidirectional_response(fwd, rev)
        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "test-model", sem,
            ))

        for r in results:
            assert r["type"] == "none"
            assert r["resolution"]["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Enrichment context tests
# ---------------------------------------------------------------------------

class TestEnrichmentContext:
    """Pure function tests for _build_enrichment_context."""

    def test_enrichment_present_when_close(self):
        from propstore.classify import build_enrichment_context
        ctx = build_enrichment_context(distance=0.3, threshold=0.75, shared_concept_ids=[])
        assert "highly similar" in ctx.lower()
        assert "0.3000" in ctx

    def test_enrichment_absent_when_distant(self):
        from propstore.classify import build_enrichment_context
        ctx = build_enrichment_context(distance=0.9, threshold=0.75, shared_concept_ids=[])
        assert ctx == ""

    def test_shared_concepts_in_enrichment(self):
        from propstore.classify import build_enrichment_context
        ctx = build_enrichment_context(distance=0.3, threshold=0.75, shared_concept_ids=["thermal_conductivity"])
        assert "thermal_conductivity" in ctx

    def test_no_distance_means_no_enrichment(self):
        from propstore.classify import build_enrichment_context
        ctx = build_enrichment_context(distance=None, threshold=0.75, shared_concept_ids=[])
        assert ctx == ""


# ---------------------------------------------------------------------------
# Hypothesis property tests
# ---------------------------------------------------------------------------

class TestEnrichmentMonotonicity:
    """Enrichment context is non-empty iff distance < threshold."""

    @given(
        distance=st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
        threshold=st.floats(min_value=0.01, max_value=2.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_enrichment_iff_below_threshold(self, distance, threshold):
        from propstore.classify import build_enrichment_context
        ctx = build_enrichment_context(distance=distance, threshold=threshold, shared_concept_ids=[])
        if distance < threshold:
            assert ctx != "", f"Expected enrichment for distance={distance} < threshold={threshold}"
        else:
            assert ctx == "", f"Expected no enrichment for distance={distance} >= threshold={threshold}"


class TestBidirectionalCompleteness:
    """For any claim pair, classifier returns exactly 2 stances with correct targets."""

    @given(
        text_a=st.text(min_size=1, max_size=50),
        text_b=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=30)
    def test_always_two_results_with_correct_targets(self, text_a, text_b):
        from propstore.classify import classify_stance_async

        resp = _mock_bidirectional_response(_default_forward(), _default_reverse())
        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a", text_a), _make_claim("b", text_b), "m", sem,
            ))

        assert len(results) == 2
        assert results[0]["target"] == "b"
        assert results[1]["target"] == "a"


class TestClassifierOutputStructureInvariant:
    """For any valid type/strength from the LLM, output structure is always complete."""

    @given(
        fwd_type=st.sampled_from(sorted(VALID_STANCE_TYPES)),
        fwd_strength=st.sampled_from(["strong", "moderate", "weak"]),
        rev_type=st.sampled_from(sorted(VALID_STANCE_TYPES)),
        rev_strength=st.sampled_from(["strong", "moderate", "weak"]),
    )
    @settings(max_examples=50)
    def test_output_always_has_required_keys(self, fwd_type, fwd_strength, rev_type, rev_strength):
        from propstore.classify import classify_stance_async

        resp = _mock_bidirectional_response(
            {"type": fwd_type, "strength": fwd_strength, "note": "test", "conditions_differ": None},
            {"type": rev_type, "strength": rev_strength, "note": "test", "conditions_differ": None},
        )
        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "m", sem,
            ))

        for r in results:
            assert r["type"] in VALID_STANCE_TYPES | {"error"}
            assert r["strength"] in {"strong", "moderate", "weak"}
            assert "resolution" in r
            assert "confidence" in r["resolution"]


class TestOpinionAlgebraInvariant:
    """For non-none stances: confidence == b + a*u and b + d + u ~= 1.0."""

    @given(
        strength=st.sampled_from(["strong", "moderate", "weak"]),
    )
    @settings(max_examples=30)
    def test_confidence_equals_expectation_and_opinion_sums_to_one(self, strength):
        from propstore.classify import classify_stance_async

        fwd = {"type": "supports", "strength": strength, "note": "test", "conditions_differ": None}
        rev = {"type": "rebuts", "strength": strength, "note": "test", "conditions_differ": None}
        resp = _mock_bidirectional_response(fwd, rev)
        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            results = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "m", sem,
            ))

        for r in results:
            if r["type"] == "none":
                continue
            res = r["resolution"]
            opinion = res["opinion"]
            b = opinion["b"]
            d = opinion["d"]
            u = opinion["u"]
            a = opinion["a"]

            # b + d + u == 1.0 (Josang 2001, Def 1)
            assert b + d + u == pytest.approx(1.0, abs=1e-9)

            # confidence == E(w) = b + a*u (Josang 2001, Def 6)
            assert res["confidence"] == pytest.approx(b + a * u, abs=1e-9)


class TestCorpusCalibrationReducesUncertainty:
    """When reference_distances provided, fused uncertainty <= categorical uncertainty.

    Direct consequence of consensus fusion (Josang 2001, Theorem 7).
    """

    @given(
        distances=st.lists(
            st.floats(min_value=0.01, max_value=1.5, allow_nan=False, allow_infinity=False),
            min_size=3, max_size=20,
        ),
        embedding_distance=st.floats(min_value=0.01, max_value=1.5, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=30)
    def test_uncertainty_decreases_with_corpus_data(self, distances, embedding_distance):
        from propstore.classify import classify_stance_async

        fwd = {"type": "supports", "strength": "strong", "note": "test", "conditions_differ": None}
        rev = {"type": "none", "strength": "weak", "note": "n/a", "conditions_differ": None}
        resp = _mock_bidirectional_response(fwd, rev)

        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            # With reference_distances
            results_with = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "m", sem,
                embedding_distance=embedding_distance,
                reference_distances=distances,
            ))

        with patch("propstore.classify._require_litellm") as mock_req:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=resp)
            mock_req.return_value = mock_litellm

            sem = asyncio.Semaphore(1)
            # Without reference_distances
            results_without = _run(classify_stance_async(
                _make_claim("a"), _make_claim("b"), "m", sem,
                embedding_distance=embedding_distance,
            ))

        # Forward stance (non-none) should have lower uncertainty with corpus data
        u_with = results_with[0]["resolution"]["opinion"]["u"]
        u_without = results_without[0]["resolution"]["opinion"]["u"]
        assert u_with <= u_without + 1e-9
