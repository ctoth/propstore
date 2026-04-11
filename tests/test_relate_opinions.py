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

from propstore.calibrate import categorical_to_opinion
from propstore.opinion import Opinion


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

    def test_strong_pass1_is_vacuous(self):
        op = categorical_to_opinion("strong", 1)
        assert op.u == pytest.approx(1.0), "uncertainty must be 1.0 (vacuous)"
        assert op.b == pytest.approx(0.0)
        assert op.d == pytest.approx(0.0)

    def test_moderate_pass2_is_vacuous(self):
        op = categorical_to_opinion("moderate", 2)
        assert op.u == pytest.approx(1.0)

    def test_weak_pass1_is_vacuous(self):
        op = categorical_to_opinion("weak", 1)
        assert op.u == pytest.approx(1.0)

    def test_base_rate_varies_by_category(self):
        """Base rate reflects corpus frequency prior, not fabricated confidence."""
        strong = categorical_to_opinion("strong", 1)
        weak = categorical_to_opinion("weak", 1)
        assert strong.a > weak.a, "strong should have higher base rate than weak"


# ---------------------------------------------------------------------------
# Test 2: categorical_to_opinion with calibration returns informative
# ---------------------------------------------------------------------------

class TestCategoricalToOpinionWithCalibration:
    """With calibration data, returns opinion with u < 1.0 and expectation
    near the empirical accuracy."""

    def test_informative_opinion(self):
        counts = {(1, "strong"): (90, 100)}  # 90% accuracy on 100 samples
        op = categorical_to_opinion("strong", 1, calibration_counts=counts)
        assert op.u < 1.0, "with evidence, uncertainty must decrease"
        assert op.expectation() == pytest.approx(90 / 102, abs=0.05)

    def test_high_evidence_low_uncertainty(self):
        counts = {(1, "strong"): (950, 1000)}
        op = categorical_to_opinion("strong", 1, calibration_counts=counts)
        assert op.u < 0.01, "1000 samples should yield very low uncertainty"


# ---------------------------------------------------------------------------
# Test 3: resolution dict has opinion fields
# ---------------------------------------------------------------------------

class TestResolutionDictHasOpinionFields:
    """The resolution dict produced by classify_stance_async() must contain
    both confidence (float) and the four opinion components."""

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
                )

        results = asyncio.run(run())
        result = results[0]  # forward stance
        res = result["resolution"]
        assert "confidence" in res
        assert "opinion_belief" in res
        assert "opinion_disbelief" in res
        assert "opinion_uncertainty" in res
        assert "opinion_base_rate" in res
        for key in ("opinion_belief", "opinion_disbelief", "opinion_uncertainty", "opinion_base_rate"):
            assert isinstance(res[key], float), f"{key} must be float"


# ---------------------------------------------------------------------------
# Test 4: confidence equals expectation
# ---------------------------------------------------------------------------

class TestConfidenceEqualsExpectation:
    """Per Josang (2001, p.5, Def 6): E(w) = b + a*u.
    The resolution confidence must equal the opinion expectation."""

    def test_vacuous_opinion_expectation(self):
        """Without calibration, confidence = base_rate (since E(vacuous) = a)."""
        for cat in ("strong", "moderate", "weak"):
            op = categorical_to_opinion(cat, 1)
            assert op.expectation() == pytest.approx(op.a)

    def test_calibrated_opinion_expectation(self):
        counts = {(1, "strong"): (80, 100)}
        op = categorical_to_opinion("strong", 1, calibration_counts=counts)
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
                )

        results = asyncio.run(run())
        result = results[0]
        res = result["resolution"]
        op = Opinion(
            res["opinion_belief"], res["opinion_disbelief"],
            res["opinion_uncertainty"], res["opinion_base_rate"],
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
                "opinion_belief": 0.0,
                "opinion_disbelief": 0.0,
                "opinion_uncertainty": 1.0,
                "opinion_base_rate": 0.7,
            },
        }]

        data = yaml.safe_load(dump_yaml_bytes(build_stance_document("claim_a", stances, "test-model")))

        res = data["stances"][0]["resolution"]
        assert res["opinion_belief"] == pytest.approx(0.0)
        assert res["opinion_disbelief"] == pytest.approx(0.0)
        assert res["opinion_uncertainty"] == pytest.approx(1.0)
        assert res["opinion_base_rate"] == pytest.approx(0.7)
        assert res["confidence"] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Test 6: sidecar populates opinion columns
# ---------------------------------------------------------------------------

class TestSidecarPopulatesOpinionColumns:
    def test_opinion_columns_from_stance_yaml(self, tmp_path):
        from propstore.sidecar.claims import populate_stances_from_files

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
                context_id TEXT
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
            "INSERT INTO claim_core VALUES ('c1', 'test:c1', '[{\"namespace\": \"test\", \"value\": \"c1\"}]', "
            "'sha256:c1', NULL, NULL, NULL, NULL, NULL, 'test', 1, NULL, NULL)"
        )
        conn.execute(
            "INSERT INTO claim_core VALUES ('c2', 'test:c2', '[{\"namespace\": \"test\", \"value\": \"c2\"}]', "
            "'sha256:c2', NULL, NULL, NULL, NULL, NULL, 'test', 1, NULL, NULL)"
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
                    "opinion_belief": 0.0,
                    "opinion_disbelief": 0.0,
                    "opinion_uncertainty": 1.0,
                    "opinion_base_rate": 0.7,
                },
            }],
        }
        (stances_dir / "c1.yaml").write_text(yaml.dump(stance_data))

        populate_stances_from_files(conn, stances_dir)

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
        from propstore.sidecar.claims import populate_stances_from_files

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
                context_id TEXT
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
            "INSERT INTO claim_core VALUES ('c1', 'test:c1', '[{\"namespace\": \"test\", \"value\": \"c1\"}]', "
            "'sha256:c1', NULL, NULL, NULL, NULL, NULL, 'test', 1, NULL, NULL)"
        )
        conn.execute(
            "INSERT INTO claim_core VALUES ('c2', 'test:c2', '[{\"namespace\": \"test\", \"value\": \"c2\"}]', "
            "'sha256:c2', NULL, NULL, NULL, NULL, NULL, 'test', 1, NULL, NULL)"
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
        (stances_dir / "c1.yaml").write_text(yaml.dump(stance_data))

        populate_stances_from_files(conn, stances_dir)

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
        from propstore.proposals import STANCE_PROPOSAL_BRANCH, stance_proposal_relpath

        assert STANCE_PROPOSAL_BRANCH == "proposal/stances"
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
                    embedding_distance=0.3,
                    reference_distances=reference_distances,
                )

        results = asyncio.run(run())
        result = results[0]
        assert result["resolution"]["opinion_uncertainty"] < 1.0

    def test_no_reference_distances_stays_vacuous(self):
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
        assert result["resolution"]["opinion_uncertainty"] == pytest.approx(1.0)

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
                    embedding_distance=0.3,
                    reference_distances=reference_distances,
                    calibration_counts=calibration_counts,
                )

        results = asyncio.run(run())
        result = results[0]
        u = result["resolution"]["opinion_uncertainty"]

        from propstore.calibrate import CorpusCalibrator, categorical_to_opinion
        corpus_op = CorpusCalibrator(reference_distances).to_opinion(0.3)
        cat_op = categorical_to_opinion("strong", 1, calibration_counts=calibration_counts)

        assert u <= min(corpus_op.u, cat_op.u) + 1e-9
