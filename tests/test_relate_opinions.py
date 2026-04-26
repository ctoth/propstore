"""Tests for opinion algebra wiring in classify.py.

Verifies that the fabricated _CONFIDENCE_MAP lookup table has been replaced
by categorical_to_opinion() from calibrate.py, and that opinion fields
flow through resolution dicts, stance YAML, and sidecar correctly.

Literature grounding:
- Josang 2001 (p.8, Def 9): vacuous opinion (0,0,1,a) = total ignorance
- Josang 2001 (p.5, Def 6): E(w) = b + a*u
- Guo et al. 2017 (p.0): raw neural scores are miscalibrated
"""

from __future__ import annotations

import sqlite3
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import yaml

from quire.documents import decode_document_path

from propstore.calibrate import (
    CalibrationSource,
    CategoryPrior,
    CategoryPriorRegistry,
    categorical_to_opinion,
)
from propstore.core.base_rates import BaseRateUnresolved
from propstore.families.documents.stances import StanceFileDocument
from propstore.opinion import Opinion
from propstore.provenance import Provenance, ProvenanceStatus


def _vacuous_provenance_payload() -> dict:
    return {"status": "vacuous", "witnesses": []}


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
    """Build a mock litellm response with bidirectional JSON."""
    if reverse is None:
        reverse = {"type": "none", "strength": "weak", "note": "reverse", "conditions_differ": None}
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = json.dumps({"forward": forward, "reverse": reverse})
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
# Test 3: resolution dict has opinion fields
# ---------------------------------------------------------------------------

class TestResolutionDictHasOpinionFields:
    """The resolution dict produced by classify_stance_async() must contain
    both confidence (float) and a provenance-bearing opinion document."""

    @pytest.fixture
    def mock_litellm_response(self):
        return _bidirectional_response(
            {"type": "supports", "strength": "strong", "note": "test note", "conditions_differ": None},
        )

    def test_resolution_has_opinion_keys(self, mock_litellm_response):
        import asyncio
        from propstore.classify import classify_stance_async

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.classify._require_litellm") as mock_req:
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
        assert set(res["opinion"]) == {"b", "d", "u", "a", "provenance"}
        for key in ("b", "d", "u", "a"):
            assert isinstance(res["opinion"][key], float), f"opinion.{key} must be float"
        assert res["opinion"]["provenance"]["status"] == "calibrated"


# ---------------------------------------------------------------------------
# Test 4: confidence equals expectation
# ---------------------------------------------------------------------------

class TestConfidenceEqualsExpectation:
    """Per Josang (2001, p.5, Def 6): E(w) = b + a*u.
    The resolution confidence must equal the opinion expectation."""

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
        from propstore.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "rebuts", "strength": "moderate", "note": "test", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "A", "source_paper": "p"}
        claim_b = {"id": "b", "text": "B", "source_paper": "p"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.classify._require_litellm") as mock_req:
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
        opinion = res["opinion"]
        op = Opinion(
            opinion["b"], opinion["d"], opinion["u"], opinion["a"],
        )
        assert res["confidence"] == pytest.approx(op.expectation())


# ---------------------------------------------------------------------------
# Test 5: stance YAML round-trips opinion
# ---------------------------------------------------------------------------

class TestStanceYamlRoundTrip:
    def test_opinion_fields_survive_yaml(self):
        from propstore.proposals import build_stance_document, dump_yaml_bytes

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
                "opinion": _opinion_payload(a=0.7),
            },
        }]

        data = yaml.safe_load(dump_yaml_bytes(build_stance_document("claim_a", stances, "test-model")))

        res = data["stances"][0]["resolution"]
        assert res["opinion"]["b"] == pytest.approx(0.0)
        assert res["opinion"]["d"] == pytest.approx(0.0)
        assert res["opinion"]["u"] == pytest.approx(1.0)
        assert res["opinion"]["a"] == pytest.approx(0.7)
        assert res["opinion"]["provenance"]["status"] == "vacuous"
        assert res["confidence"] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Test 6: sidecar populates opinion columns
# ---------------------------------------------------------------------------

class TestSidecarPopulatesOpinionColumns:
    def test_opinion_columns_from_stance_yaml(self, tmp_path):
        from propstore.sidecar.claims import populate_stances
        from propstore.sidecar.passes import compile_authored_stance_sidecar_rows

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE claim_core (
                id TEXT PRIMARY KEY,
                primary_logical_id TEXT,
                logical_ids_json TEXT,
                version_id TEXT,
                content_hash TEXT,
                seq INTEGER,
                type TEXT,
                concept_id TEXT,
                target_concept TEXT,
                source_paper TEXT NOT NULL DEFAULT 'test',
                provenance_page INTEGER NOT NULL DEFAULT 1,
                provenance_json TEXT,
                context_id TEXT,
                branch TEXT
            );
            CREATE TABLE relation_edge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_kind TEXT NOT NULL,
                source_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                target_kind TEXT NOT NULL,
                target_id TEXT NOT NULL,
                target_justification_id TEXT,
                strength TEXT,
                conditions_differ TEXT,
                note TEXT,
                resolution_method TEXT,
                resolution_model TEXT,
                embedding_model TEXT,
                embedding_distance REAL,
                pass_number INTEGER,
                confidence REAL,
                opinion_belief REAL,
                opinion_disbelief REAL,
                opinion_uncertainty REAL,
                opinion_base_rate REAL DEFAULT 0.5
            );
        """)
        conn.execute(
            """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id,
                content_hash, seq, type, concept_id, target_concept,
                source_paper, provenance_page, provenance_json, context_id
            ) VALUES ('c1', 'test:c1', '[{"namespace": "test", "value": "c1"}]',
                'sha256:c1', NULL, NULL, NULL, NULL, NULL, 'test', 1, NULL, NULL)
            """
        )
        conn.execute(
            """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id,
                content_hash, seq, type, concept_id, target_concept,
                source_paper, provenance_page, provenance_json, context_id
            ) VALUES ('c2', 'test:c2', '[{"namespace": "test", "value": "c2"}]',
                'sha256:c2', NULL, NULL, NULL, NULL, NULL, 'test', 1, NULL, NULL)
            """
        )

        stances_dir = tmp_path / "stances"
        stances_dir.mkdir()
        stance_data = {
            "source_claim": "c1",
            "classification_model": "test",
            "classification_date": "2026-01-01",
            "stances": [{
                "target": "c2",
                "type": "supports",
                "strength": "strong",
                "note": "test",
                "resolution": {
                    "method": "nli",
                    "model": "test",
                    "confidence": 0.7,
                    "opinion": _opinion_payload(a=0.7),
                },
            }],
        }
        stance_path = stances_dir / "c1.yaml"
        stance_path.write_text(yaml.dump(stance_data))
        stance_document = decode_document_path(stance_path, StanceFileDocument)

        populate_stances(
            conn,
            compile_authored_stance_sidecar_rows(
                [("c1", stance_document)],
                {"c1": "c1", "c2": "c2", "test:c1": "c1", "test:c2": "c2"},
            ),
        )

        row = conn.execute(
            "SELECT * FROM relation_edge WHERE source_kind='claim' AND target_kind='claim' AND source_id='c1'"
        ).fetchone()
        assert row["opinion_belief"] == pytest.approx(0.0)
        assert row["opinion_disbelief"] == pytest.approx(0.0)
        assert row["opinion_uncertainty"] == pytest.approx(1.0)
        assert row["opinion_base_rate"] == pytest.approx(0.7)
        conn.close()


# ---------------------------------------------------------------------------
# Test 7: sidecar handles old format YAML (no opinion fields)
# ---------------------------------------------------------------------------

class TestSidecarHandlesOldFormatYaml:
    def test_missing_opinion_fields_become_null(self, tmp_path):
        from propstore.sidecar.claims import populate_stances
        from propstore.sidecar.passes import compile_authored_stance_sidecar_rows

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE claim_core (
                id TEXT PRIMARY KEY,
                primary_logical_id TEXT,
                logical_ids_json TEXT,
                version_id TEXT,
                content_hash TEXT,
                seq INTEGER,
                type TEXT,
                concept_id TEXT,
                target_concept TEXT,
                source_paper TEXT NOT NULL DEFAULT 'test',
                provenance_page INTEGER NOT NULL DEFAULT 1,
                provenance_json TEXT,
                context_id TEXT,
                branch TEXT
            );
            CREATE TABLE relation_edge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_kind TEXT NOT NULL,
                source_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                target_kind TEXT NOT NULL,
                target_id TEXT NOT NULL,
                target_justification_id TEXT,
                strength TEXT,
                conditions_differ TEXT,
                note TEXT,
                resolution_method TEXT,
                resolution_model TEXT,
                embedding_model TEXT,
                embedding_distance REAL,
                pass_number INTEGER,
                confidence REAL,
                opinion_belief REAL,
                opinion_disbelief REAL,
                opinion_uncertainty REAL,
                opinion_base_rate REAL DEFAULT 0.5
            );
        """)
        conn.execute(
            """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id,
                content_hash, seq, type, concept_id, target_concept,
                source_paper, provenance_page, provenance_json, context_id
            ) VALUES ('c1', 'test:c1', '[{"namespace": "test", "value": "c1"}]',
                'sha256:c1', NULL, NULL, NULL, NULL, NULL, 'test', 1, NULL, NULL)
            """
        )
        conn.execute(
            """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id,
                content_hash, seq, type, concept_id, target_concept,
                source_paper, provenance_page, provenance_json, context_id
            ) VALUES ('c2', 'test:c2', '[{"namespace": "test", "value": "c2"}]',
                'sha256:c2', NULL, NULL, NULL, NULL, NULL, 'test', 1, NULL, NULL)
            """
        )

        stances_dir = tmp_path / "stances"
        stances_dir.mkdir()
        # Old format: no opinion fields in resolution
        stance_data = {
            "source_claim": "c1",
            "classification_model": "test",
            "classification_date": "2026-01-01",
            "stances": [{
                "target": "c2",
                "type": "supports",
                "strength": "strong",
                "note": "old format test",
                "resolution": {
                    "method": "nli_first_pass",
                    "model": "test",
                    "confidence": 0.95,
                },
            }],
        }
        stance_path = stances_dir / "c1.yaml"
        stance_path.write_text(yaml.dump(stance_data))
        stance_document = decode_document_path(stance_path, StanceFileDocument)

        populate_stances(
            conn,
            compile_authored_stance_sidecar_rows(
                [("c1", stance_document)],
                {"c1": "c1", "c2": "c2", "test:c1": "c1", "test:c2": "c2"},
            ),
        )

        row = conn.execute(
            "SELECT * FROM relation_edge WHERE source_kind='claim' AND target_kind='claim' AND source_id='c1'"
        ).fetchone()
        assert row["opinion_belief"] is None
        assert row["opinion_disbelief"] is None
        assert row["opinion_uncertainty"] is None
        # confidence still preserved from old format
        assert row["confidence"] == pytest.approx(0.95)
        conn.close()


# ---------------------------------------------------------------------------
# Test 8: none stance gets zero confidence
# ---------------------------------------------------------------------------

class TestNoneStanceGetsZeroConfidence:
    """Stances with type='none' must still get confidence 0.0."""

    def test_none_type_zero_confidence(self):
        import asyncio
        from propstore.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "none", "strength": "strong", "note": "unrelated", "conditions_differ": None},
            {"type": "none", "strength": "weak", "note": "unrelated", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "A", "source_paper": "p"}
        claim_b = {"id": "b", "text": "B", "source_paper": "p"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                )

        results = asyncio.run(run())
        assert results[0]["resolution"]["confidence"] == 0.0
        assert results[0]["resolution"]["opinion"] is None


# ---------------------------------------------------------------------------
# Test 9: API failure returns error type, not none (F2.4)
# ---------------------------------------------------------------------------

class TestApiFailureReturnsErrorType:

    def test_api_exception_returns_error_not_none(self):
        import asyncio
        from propstore.classify import classify_stance_async

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.classify._require_litellm") as mock_req:
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
        from propstore.classify import classify_stance_async

        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = "This is not valid JSON at all"

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.classify._require_litellm") as mock_req:
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
        from propstore.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "none", "strength": "weak", "note": "entirely different topics", "conditions_differ": None},
            {"type": "none", "strength": "weak", "note": "entirely different topics", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.classify._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                )

        results = asyncio.run(run())
        assert results[0]["type"] == "none"
        assert results[0]["resolution"]["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Test 12: stance proposals live on the proposal branch (F17)
# ---------------------------------------------------------------------------

class TestStanceProposalsUseBranchState:

    def test_stance_proposal_path_and_branch_are_git_native(self):
        from propstore.proposals import stance_proposal_branch, stance_proposal_relpath

        assert stance_proposal_branch() == "proposal/stances"
        assert stance_proposal_relpath("paper:claim_a") == "stances/paper__claim_a.yaml"


# ---------------------------------------------------------------------------
# Test 13: CorpusCalibrator reduces uncertainty in classify_stance_async
# ---------------------------------------------------------------------------

class TestCorpusCalibReducesUncertainty:

    def test_corpus_calibrator_reduces_uncertainty(self):
        import asyncio
        from propstore.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "supports", "strength": "strong", "note": "test", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}
        reference_distances = [0.1, 0.2, 0.3, 0.4, 0.5]

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.classify._require_litellm") as mock_req:
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
        assert result["resolution"]["opinion"]["u"] < 1.0

    def test_no_reference_distances_and_no_prior_stays_unresolved(self):
        import asyncio
        from propstore.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "supports", "strength": "strong", "note": "test", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.classify._require_litellm") as mock_req:
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
        assert result["resolution"]["opinion"] is None
        assert result["resolution"]["confidence"] == pytest.approx(0.0)
        assert result["resolution"]["unresolved_calibration"]["reason"] == "missing_base_rate"

    def test_corpus_and_categorical_fused_via_consensus(self):
        import asyncio
        from propstore.classify import classify_stance_async

        resp = _bidirectional_response(
            {"type": "supports", "strength": "strong", "note": "test", "conditions_differ": None},
        )

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        reference_distances = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        calibration_counts = {(1, "strong"): (80, 100)}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.classify._require_litellm") as mock_req:
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
        u = result["resolution"]["opinion"]["u"]

        from propstore.calibrate import CorpusCalibrator, categorical_to_opinion
        corpus_op = CorpusCalibrator(reference_distances).to_opinion(0.3)
        cat_op = categorical_to_opinion(
            "strong",
            1,
            calibration_counts=calibration_counts,
            prior=_category_prior("strong", 0.7),
        )
        assert isinstance(cat_op, Opinion)

        assert u <= min(corpus_op.u, cat_op.u) + 1e-9
