"""Tests for opinion algebra wiring in classify.py.

Verifies that the fabricated _CONFIDENCE_MAP lookup table has been replaced
by categorical_to_opinion() from calibrate.py, and that stance opinions
flow through top-level relation fields, stance YAML, and sidecar correctly.

Literature grounding:
- Josang 2001 (p.8, Def 9): vacuous opinion (0,0,1,a) = total ignorance
- Josang 2001 (p.5, Def 6): E(w) = b + a*u
- Guo et al. 2017 (p.0): raw neural scores are miscalibrated
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock

import pytest
import yaml

from quire.documents import decode_document_path
from quire.references import FamilyReferenceIndex

from propstore.heuristic.calibrate import (
    CalibrationSource,
    CategoryPrior,
    CategoryPriorRegistry,
    categorical_to_opinion,
)
from propstore.core.base_rates import BaseRateUnresolved
from propstore.families.claims.declaration import ClaimDocument
from propstore.families.claims.references import (
    ClaimReferenceRecord,
    claim_reference_keys,
)
from propstore.families.contexts.declaration import ContextReferenceDocument
from propstore.families.stances.declaration import StanceDocument
from propstore.opinion import Opinion
from propstore.provenance import Provenance, ProvenanceStatus


def _vacuous_provenance_payload() -> dict:
    return {"status": "vacuous", "witnesses": []}


def _claim_reference_index() -> FamilyReferenceIndex[ClaimReferenceRecord]:
    records = (
        ClaimReferenceRecord(
            claim=ClaimDocument(
                context=ContextReferenceDocument(id="test"),
                artifact_id="c1",
                id="c1",
            ),
            source_paper="test",
        ),
        ClaimReferenceRecord(
            claim=ClaimDocument(
                context=ContextReferenceDocument(id="test"),
                artifact_id="c2",
                id="c2",
            ),
            source_paper="test",
        ),
    )

    return FamilyReferenceIndex.from_records(
        records,
        family="claim",
        artifact_id=lambda record: record.artifact_id,
        keys=(claim_reference_keys,),
    )


def _category_prior(category: str, value: float = 0.5) -> CategoryPrior:
    return CategoryPrior(
        category=category,
        value=value,
        source=CalibrationSource.MEASURED,
        provenance=Provenance(
            status=ProvenanceStatus.CALIBRATED,
            witnesses=(),
            operations=("test_category_prior",),
        ),
    )


def _category_prior_registry() -> CategoryPriorRegistry:
    return CategoryPriorRegistry(
        {
            "strong": _category_prior("strong", 0.7),
            "moderate": _category_prior("moderate", 0.5),
            "weak": _category_prior("weak", 0.3),
        }
    )


def _opinion_payload(
    *,
    b: float = 0.0,
    d: float = 0.0,
    u: float = 1.0,
    a: float = 0.5,
) -> dict:
    return {
        "b": b,
        "d": d,
        "u": u,
        "a": a,
        "provenance": _vacuous_provenance_payload(),
    }


# ---------------------------------------------------------------------------
# Helper: build bidirectional mock response
# ---------------------------------------------------------------------------

def _bidirectional_response(forward: dict, reverse: dict | None = None) -> MagicMock:
    """Build a mock response returning forward then reverse directional JSON."""
    if reverse is None:
        reverse = {"type": "none", "strength": "weak", "note": "reverse", "conditions_differ": None}
    resp = MagicMock()
    resp.choices = [MagicMock()]
    message = MagicMock()
    type(message).content = PropertyMock(
        side_effect=[json.dumps(forward), json.dumps(reverse)] * 100
    )
    resp.choices[0].message = message
    return resp


# ---------------------------------------------------------------------------
# Test 1: categorical_to_opinion without calibration returns vacuous
# ---------------------------------------------------------------------------

class TestCategoricalToOpinionNoCalibration:
    """Per Josang (2001, p.8): vacuous opinion is the correct representation
    of total ignorance.  Without calibration data, we have no empirical basis
    for confidence."""

    def test_strong_pass1_is_unresolved(self):
        result = categorical_to_opinion("strong", 1)
        assert isinstance(result, BaseRateUnresolved)
        assert result.reason == "missing_base_rate"

    def test_moderate_pass2_is_unresolved(self):
        result = categorical_to_opinion("moderate", 2)
        assert isinstance(result, BaseRateUnresolved)

    def test_weak_pass1_is_unresolved(self):
        result = categorical_to_opinion("weak", 1)
        assert isinstance(result, BaseRateUnresolved)

    def test_base_rate_does_not_exist_without_explicit_prior(self):
        """Without an explicit prior, every category is unresolved."""
        strong = categorical_to_opinion("strong", 1)
        weak = categorical_to_opinion("weak", 1)
        assert isinstance(strong, BaseRateUnresolved)
        assert isinstance(weak, BaseRateUnresolved)


# ---------------------------------------------------------------------------
# Test 2: categorical_to_opinion with calibration returns informative
# ---------------------------------------------------------------------------

class TestCategoricalToOpinionWithCalibration:
    """With calibration data, returns opinion with u < 1.0 and expectation
    near the empirical accuracy."""

    def test_informative_opinion(self):
        counts = {(1, "strong"): (90, 100)}  # 90% accuracy on 100 samples
        op = categorical_to_opinion(
            "strong",
            1,
            calibration_counts=counts,
            prior=_category_prior("strong", 0.7),
        )
        assert isinstance(op, Opinion)
        assert op.u < 1.0, "with evidence, uncertainty must decrease"
        assert op.expectation() == pytest.approx(90 / 102, abs=0.05)

    def test_high_evidence_low_uncertainty(self):
        counts = {(1, "strong"): (950, 1000)}
        op = categorical_to_opinion(
            "strong",
            1,
            calibration_counts=counts,
            prior=_category_prior("strong", 0.7),
        )
        assert isinstance(op, Opinion)
        assert op.u < 0.01, "1000 samples should yield very low uncertainty"


# ---------------------------------------------------------------------------
# Test 3: stance payload has top-level opinion
# ---------------------------------------------------------------------------

class TestResolutionDictHasOpinionFields:
    """classify_stance_async() returns scalar resolution metadata and a typed opinion."""

    @pytest.fixture
    def mock_litellm_response(self):
        return _bidirectional_response(
            {"type": "supports", "strength": "strong", "note": "test note", "conditions_differ": None},
        )

    def test_resolution_has_opinion_keys(self, mock_litellm_response):
        import asyncio
        from propstore.heuristic.classify import classify_stance_async

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.heuristic.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=mock_litellm_response)
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                    category_prior_registry=_category_prior_registry(),
                )

        results = asyncio.run(run())
        result = results[0]  # forward stance
        res = result["resolution"]
        assert "confidence" in res
        assert "opinion" not in res
        opinion = result["opinion"]
        assert isinstance(opinion, Opinion)
        assert opinion.provenance is not None
        assert opinion.provenance.status is ProvenanceStatus.CALIBRATED


# ---------------------------------------------------------------------------
# Test 4: confidence equals expectation
# ---------------------------------------------------------------------------

class TestConfidenceEqualsExpectation:
    """Per Josang (2001, p.5, Def 6): E(w) = b + a*u.
    The resolution confidence must equal the top-level opinion expectation."""

    def test_missing_prior_has_no_expectation(self):
        """Without a sourced prior, no numeric confidence is fabricated."""
        for cat in ("strong", "moderate", "weak"):
            result = categorical_to_opinion(cat, 1)
            assert isinstance(result, BaseRateUnresolved)

    def test_calibrated_opinion_expectation(self):
        counts = {(1, "strong"): (80, 100)}
        op = categorical_to_opinion(
            "strong",
            1,
            calibration_counts=counts,
            prior=_category_prior("strong", 0.7),
        )
        assert isinstance(op, Opinion)
        expected_e = op.b + op.a * op.u
        assert op.expectation() == pytest.approx(expected_e)

    def test_resolution_confidence_matches_expectation(self):
        """The confidence float in the resolution dict must equal Opinion.expectation()."""
        import asyncio
        from propstore.heuristic.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "rebuts", "strength": "moderate", "note": "test", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "A", "source_paper": "p"}
        claim_b = {"id": "b", "text": "B", "source_paper": "p"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.heuristic.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                    category_prior_registry=_category_prior_registry(),
                )

        results = asyncio.run(run())
        result = results[0]
        res = result["resolution"]
        opinion = result["opinion"]
        assert isinstance(opinion, Opinion)
        assert res["confidence"] == pytest.approx(opinion.expectation())


# ---------------------------------------------------------------------------
# Test 5: stance YAML round-trips opinion
# ---------------------------------------------------------------------------

class TestStanceYamlRoundTrip:
    def test_opinion_fields_survive_yaml(self):
        from quire.documents import encode_document
        from propstore.families.stances.lifecycle import (
            StanceProposalInput,
            build_stance_proposal_document,
        )

        stances = [{
            "target": "claim_b",
            "type": "supports",
            "strength": "strong",
            "note": "test",
            "conditions_differ": None,
            "resolution": {
                "method": "nli",
                "model": "test-model",
                "embedding_model": None,
                "embedding_distance": None,
                "confidence": 0.7,
            },
            "opinion": Opinion(
                0.0,
                0.0,
                1.0,
                0.7,
                provenance=Provenance(
                    status=ProvenanceStatus.VACUOUS,
                    witnesses=(),
                ),
            ),
        }]

        data = yaml.safe_load(
            encode_document(
                build_stance_proposal_document(
                    "claim_a",
                    StanceProposalInput(
                        target=str(stances[0]["target"]),
                        type=str(stances[0]["type"]),
                        strength=str(stances[0]["strength"]),
                        note=str(stances[0]["note"]),
                        conditions_differ=None,
                        opinion=stances[0]["opinion"],
                        resolution=stances[0]["resolution"],
                    ),
                    "test-model",
                )
            )
        )

        res = data["resolution"]
        opinion = data["opinion"]
        assert opinion["b"] == pytest.approx(0.0)
        assert opinion["d"] == pytest.approx(0.0)
        assert opinion["u"] == pytest.approx(1.0)
        assert opinion["a"] == pytest.approx(0.7)
        assert res["confidence"] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Test 6: sidecar populates relation opinion
# ---------------------------------------------------------------------------

class TestSidecarPopulatesOpinionColumns:
    def test_opinion_from_stance_yaml(self, tmp_path):
        from propstore.families.relations.declaration import (
            compile_authored_stance_models_with_diagnostics,
        )

        stances_dir = tmp_path / "stances"
        stances_dir.mkdir()
        stance_data = {
            "artifact_id": "ps:stance:opinion",
            "source_claim": "c1",
            "classification_model": "test",
            "classification_date": "2026-01-01",
            "target": "c2",
            "type": "supports",
            "strength": "strong",
            "note": "test",
            "artifact_code": "ps:stance:opinion",
            "opinion": _opinion_payload(a=0.7),
            "resolution": {
                "method": "nli",
                "model": "test",
                "confidence": 0.7,
            },
        }
        stance_path = stances_dir / "c1.yaml"
        stance_path.write_text(yaml.dump(stance_data))
        stance_document = decode_document_path(stance_path, StanceDocument)

        models, diagnostics = compile_authored_stance_models_with_diagnostics(
            [("c1", stance_document)],
            _claim_reference_index(),
        )

        assert diagnostics == ()
        assert len(models) == 1
        stance = models[0]
        assert stance.opinion == Opinion(
            0.0,
            0.0,
            1.0,
            0.7,
            provenance=Provenance(
                status=ProvenanceStatus.VACUOUS,
                witnesses=(),
            ),
        )
        assert stance.perspective_source_claim_id == "c1"


# ---------------------------------------------------------------------------
# Test 7: sidecar handles stance without opinion
# ---------------------------------------------------------------------------

class TestSidecarHandlesResolutionWithoutOpinion:
    def test_missing_opinion_becomes_null(self, tmp_path):
        from propstore.families.relations.declaration import (
            compile_authored_stance_models_with_diagnostics,
        )

        stances_dir = tmp_path / "stances"
        stances_dir.mkdir()
        stance_data = {
            "artifact_id": "ps:stance:no-opinion",
            "source_claim": "c1",
            "classification_model": "test",
            "classification_date": "2026-01-01",
            "target": "c2",
            "type": "supports",
            "strength": "strong",
            "note": "old format test",
            "artifact_code": "ps:stance:no-opinion",
            "resolution": {
                "method": "nli_first_pass",
                "model": "test",
                "confidence": 0.95,
            },
        }
        stance_path = stances_dir / "c1.yaml"
        stance_path.write_text(yaml.dump(stance_data))
        stance_document = decode_document_path(stance_path, StanceDocument)

        models, diagnostics = compile_authored_stance_models_with_diagnostics(
            [("c1", stance_document)],
            _claim_reference_index(),
        )

        assert diagnostics == ()
        assert len(models) == 1
        stance = models[0]
        assert stance.opinion is None
        assert stance.confidence == pytest.approx(0.95)


# ---------------------------------------------------------------------------
# Test 8: none stance gets null confidence
# ---------------------------------------------------------------------------

class TestNoneStanceGetsNullConfidence:
    """Stances with type='none' carry null confidence rather than a fabricated zero."""

    def test_none_type_null_confidence(self):
        import asyncio
        from propstore.heuristic.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "none", "strength": "strong", "note": "unrelated", "conditions_differ": None},
            {"type": "none", "strength": "weak", "note": "unrelated", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "A", "source_paper": "p"}
        claim_b = {"id": "b", "text": "B", "source_paper": "p"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.heuristic.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                )

        results = asyncio.run(run())
        assert results[0]["resolution"]["confidence"] is None
        assert results[0]["opinion"] is None


# ---------------------------------------------------------------------------
# Test 9: API failure returns error type, not none (F2.4)
# ---------------------------------------------------------------------------

class TestApiFailureReturnsErrorType:

    def test_api_exception_returns_error_not_none(self):
        import asyncio
        from propstore.heuristic.classify import classify_stance_async

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.heuristic.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(
                    side_effect=ConnectionError("API unreachable")
                )
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                )

        results = asyncio.run(run())
        for result in results:
            assert result["type"] != "none"
            assert result["type"] == "error"


# ---------------------------------------------------------------------------
# Test 10: JSON parse failure returns error type, not none (F2.5)
# ---------------------------------------------------------------------------

class TestJsonParseFailureReturnsErrorType:

    def test_json_parse_failure_returns_error_not_none(self):
        import asyncio
        from propstore.heuristic.classify import classify_stance_async

        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = "This is not valid JSON at all"

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.heuristic.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                )

        results = asyncio.run(run())
        for result in results:
            assert result["type"] != "none"
            assert result["type"] == "error"


# ---------------------------------------------------------------------------
# Test 11: Genuine "none" classification still works
# ---------------------------------------------------------------------------

class TestGenuineNoneStillWorks:

    def test_genuine_none_passes_through(self):
        import asyncio
        from propstore.heuristic.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "none", "strength": "weak", "note": "entirely different topics", "conditions_differ": None},
            {"type": "none", "strength": "weak", "note": "entirely different topics", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.heuristic.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                )

        results = asyncio.run(run())
        assert results[0]["type"] == "none"
        assert results[0]["resolution"]["confidence"] is None


# ---------------------------------------------------------------------------
# Test 12: stance proposals live on the proposal branch (F17)
# ---------------------------------------------------------------------------

class TestStanceProposalsUseBranchState:

    def test_stance_proposal_path_and_branch_are_git_native(self):
        from propstore.families.stances.lifecycle import (
            stance_proposal_branch,
            stance_proposal_relpath,
        )

        assert stance_proposal_branch() == "proposal/stances"
        assert stance_proposal_relpath("ps:stance:abc") == "stances/ps__stance__abc.yaml"


# ---------------------------------------------------------------------------
# Test 13: CorpusCalibrator reduces uncertainty in classify_stance_async
# ---------------------------------------------------------------------------

class TestCorpusCalibReducesUncertainty:

    def test_corpus_calibrator_reduces_uncertainty(self):
        import asyncio
        from propstore.heuristic.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "supports", "strength": "strong", "note": "test", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}
        reference_distances = [0.1, 0.2, 0.3, 0.4, 0.5]

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.heuristic.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                    category_prior_registry=_category_prior_registry(),
                    embedding_distance=0.3,
                    reference_distances=reference_distances,
                )

        results = asyncio.run(run())
        result = results[0]
        assert isinstance(result["opinion"], Opinion)
        assert result["opinion"].u < 1.0

    def test_no_reference_distances_and_no_prior_stays_unresolved(self):
        import asyncio
        from propstore.heuristic.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "supports", "strength": "strong", "note": "test", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.heuristic.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                    embedding_distance=0.3,
                    reference_distances=None,
                )

        results = asyncio.run(run())
        result = results[0]
        assert result["opinion"] is None
        assert result["resolution"]["confidence"] is None
        assert result["resolution"]["unresolved_calibration"]["reason"] == "missing_base_rate"

    def test_corpus_and_categorical_fused_via_wbf(self):
        import asyncio
        from propstore.heuristic.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "supports", "strength": "strong", "note": "test", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        reference_distances = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        calibration_counts = {(1, "strong"): (80, 100)}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.heuristic.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                    category_prior_registry=_category_prior_registry(),
                    embedding_distance=0.3,
                    reference_distances=reference_distances,
                    calibration_counts=calibration_counts,
                )

        results = asyncio.run(run())
        result = results[0]
        assert isinstance(result["opinion"], Opinion)
        u = result["opinion"].u

        from propstore.heuristic.calibrate import CorpusCalibrator, categorical_to_opinion
        corpus_op = CorpusCalibrator(reference_distances, corpus_base_rate=0.7).to_opinion(0.3)
        cat_op = categorical_to_opinion(
            "strong",
            1,
            calibration_counts=calibration_counts,
            prior=_category_prior("strong", 0.7),
        )
        assert isinstance(cat_op, Opinion)

        expected = Opinion.fuse(corpus_op, cat_op)
        assert u == pytest.approx(expected.u, abs=1e-12)
