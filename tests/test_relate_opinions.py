"""Tests for opinion algebra wiring in relate.py.

Verifies that the fabricated _CONFIDENCE_MAP lookup table has been replaced
by categorical_to_opinion() from calibrate.py, and that opinion fields
flow through resolution dicts, stance YAML, and sidecar correctly.

Literature grounding:
- Jøsang 2001 (p.8, Def 9): vacuous opinion (0,0,1,a) = total ignorance
- Jøsang 2001 (p.5, Def 6): E(ω) = b + a·u
- Guo et al. 2017 (p.0): raw neural scores are miscalibrated
"""

from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import yaml

from propstore.calibrate import categorical_to_opinion
from propstore.opinion import Opinion


# ---------------------------------------------------------------------------
# Test 1: categorical_to_opinion without calibration returns vacuous
# ---------------------------------------------------------------------------

class TestCategoricalToOpinionNoCalibration:
    """Per Jøsang (2001, p.8): vacuous opinion is the correct representation
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
    """The resolution dict produced by _classify_stance_async() must contain
    both confidence (float) and the four opinion components."""

    @pytest.fixture
    def mock_litellm_response(self):
        """Fake a successful LLM classification."""
        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = json.dumps({
            "type": "supports",
            "strength": "strong",
            "note": "test note",
            "conditions_differ": None,
        })
        return resp

    def test_resolution_has_opinion_keys(self, mock_litellm_response):
        import asyncio
        from propstore.relate import _classify_stance_async

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.relate._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=mock_litellm_response)
                mock_req.return_value = mock_litellm
                return await _classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                    pass_number=1,
                )

        result = asyncio.run(run())
        res = result["resolution"]
        assert "confidence" in res
        assert "opinion_belief" in res
        assert "opinion_disbelief" in res
        assert "opinion_uncertainty" in res
        assert "opinion_base_rate" in res
        # All opinion fields must be floats
        for key in ("opinion_belief", "opinion_disbelief", "opinion_uncertainty", "opinion_base_rate"):
            assert isinstance(res[key], float), f"{key} must be float"


# ---------------------------------------------------------------------------
# Test 4: confidence equals expectation
# ---------------------------------------------------------------------------

class TestConfidenceEqualsExpectation:
    """Per Jøsang (2001, p.5, Def 6): E(ω) = b + a·u.
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
        from propstore.relate import _classify_stance_async

        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = json.dumps({
            "type": "rebuts",
            "strength": "moderate",
            "note": "test",
            "conditions_differ": None,
        })

        claim_a = {"id": "a", "text": "A", "source_paper": "p"}
        claim_b = {"id": "b", "text": "B", "source_paper": "p"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.relate._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await _classify_stance_async(
                    claim_a, claim_b, "test-model", sem, pass_number=1,
                )

        result = asyncio.run(run())
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
    def test_opinion_fields_survive_yaml(self, tmp_path):
        from propstore.relate import write_stance_file

        stances = [{
            "target": "claim_b",
            "type": "supports",
            "strength": "strong",
            "note": "test",
            "conditions_differ": None,
            "resolution": {
                "method": "nli_first_pass",
                "model": "test-model",
                "embedding_model": None,
                "embedding_distance": None,
                "pass_number": 1,
                "confidence": 0.7,
                "opinion_belief": 0.0,
                "opinion_disbelief": 0.0,
                "opinion_uncertainty": 1.0,
                "opinion_base_rate": 0.7,
            },
        }]

        path = write_stance_file(tmp_path, "claim_a", stances, "test-model")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

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
        from propstore.build_sidecar import _populate_stances_from_files

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE claim (id TEXT PRIMARY KEY, source_paper TEXT NOT NULL DEFAULT 'test',
                                provenance_page INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE claim_stance (
                claim_id TEXT NOT NULL, target_claim_id TEXT NOT NULL,
                stance_type TEXT NOT NULL, strength TEXT,
                conditions_differ TEXT, note TEXT,
                resolution_method TEXT, resolution_model TEXT,
                embedding_model TEXT, embedding_distance REAL,
                pass_number INTEGER, confidence REAL,
                opinion_belief REAL, opinion_disbelief REAL,
                opinion_uncertainty REAL, opinion_base_rate REAL DEFAULT 0.5,
                FOREIGN KEY (claim_id) REFERENCES claim(id),
                FOREIGN KEY (target_claim_id) REFERENCES claim(id)
            );
        """)
        conn.execute("INSERT INTO claim (id) VALUES ('c1')")
        conn.execute("INSERT INTO claim (id) VALUES ('c2')")

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
                    "method": "nli_first_pass",
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

        _populate_stances_from_files(conn, stances_dir)

        row = conn.execute("SELECT * FROM claim_stance WHERE claim_id='c1'").fetchone()
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
        from propstore.build_sidecar import _populate_stances_from_files

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE claim (id TEXT PRIMARY KEY, source_paper TEXT NOT NULL DEFAULT 'test',
                                provenance_page INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE claim_stance (
                claim_id TEXT NOT NULL, target_claim_id TEXT NOT NULL,
                stance_type TEXT NOT NULL, strength TEXT,
                conditions_differ TEXT, note TEXT,
                resolution_method TEXT, resolution_model TEXT,
                embedding_model TEXT, embedding_distance REAL,
                pass_number INTEGER, confidence REAL,
                opinion_belief REAL, opinion_disbelief REAL,
                opinion_uncertainty REAL, opinion_base_rate REAL DEFAULT 0.5,
                FOREIGN KEY (claim_id) REFERENCES claim(id),
                FOREIGN KEY (target_claim_id) REFERENCES claim(id)
            );
        """)
        conn.execute("INSERT INTO claim (id) VALUES ('c1')")
        conn.execute("INSERT INTO claim (id) VALUES ('c2')")

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

        _populate_stances_from_files(conn, stances_dir)

        row = conn.execute("SELECT * FROM claim_stance WHERE claim_id='c1'").fetchone()
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
        from propstore.relate import _classify_stance_async

        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = json.dumps({
            "type": "none",
            "strength": "strong",
            "note": "unrelated",
            "conditions_differ": None,
        })

        claim_a = {"id": "a", "text": "A", "source_paper": "p"}
        claim_b = {"id": "b", "text": "B", "source_paper": "p"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.relate._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await _classify_stance_async(
                    claim_a, claim_b, "test-model", sem, pass_number=1,
                )

        result = asyncio.run(run())
        assert result["resolution"]["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Test 9: API failure returns error type, not none (F2.4)
# ---------------------------------------------------------------------------

class TestApiFailureReturnsErrorType:
    """Bug F2.4: When the LLM API call raises an exception, relate.py returns
    type="none" with confidence=0.0. This is indistinguishable from a genuine
    "no relationship" classification. The type should be "error" (or some
    distinct indicator) so downstream consumers can tell the difference."""

    def test_api_exception_returns_error_not_none(self):
        import asyncio
        from propstore.relate import _classify_stance_async

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.relate._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(
                    side_effect=ConnectionError("API unreachable")
                )
                mock_req.return_value = mock_litellm
                return await _classify_stance_async(
                    claim_a, claim_b, "test-model", sem, pass_number=1,
                )

        result = asyncio.run(run())
        # Must NOT be "none" — errors are not negatives
        assert result["type"] != "none", (
            "API failure must not return type='none'; "
            "errors must be distinguishable from genuine no-relationship"
        )
        assert result["type"] == "error", (
            "API failure should return type='error'"
        )


# ---------------------------------------------------------------------------
# Test 10: JSON parse failure returns error type, not none (F2.5)
# ---------------------------------------------------------------------------

class TestJsonParseFailureReturnsErrorType:
    """Bug F2.5: When the LLM returns invalid JSON, relate.py returns
    type="none" with confidence=0.0. This silently drops the error and
    makes it look like there's genuinely no relationship."""

    def test_json_parse_failure_returns_error_not_none(self):
        import asyncio
        from propstore.relate import _classify_stance_async

        # LLM returns non-JSON text
        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = "This is not valid JSON at all"

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.relate._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await _classify_stance_async(
                    claim_a, claim_b, "test-model", sem, pass_number=1,
                )

        result = asyncio.run(run())
        # Must NOT be "none" — parse failures are not negatives
        assert result["type"] != "none", (
            "JSON parse failure must not return type='none'; "
            "errors must be distinguishable from genuine no-relationship"
        )
        assert result["type"] == "error", (
            "JSON parse failure should return type='error'"
        )


# ---------------------------------------------------------------------------
# Test 11: Genuine "none" classification still works
# ---------------------------------------------------------------------------

class TestGenuineNoneStillWorks:
    """A real LLM classification of type="none" (no relationship) must
    pass through unchanged. This test ensures the fix for F2.4/F2.5
    doesn't break genuine negatives."""

    def test_genuine_none_passes_through(self):
        import asyncio
        from propstore.relate import _classify_stance_async

        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = json.dumps({
            "type": "none",
            "strength": "weak",
            "note": "These claims are about entirely different topics",
            "conditions_differ": None,
        })

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.relate._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await _classify_stance_async(
                    claim_a, claim_b, "test-model", sem, pass_number=1,
                )

        result = asyncio.run(run())
        assert result["type"] == "none", "Genuine none must remain type='none'"
        assert result["resolution"]["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Test 12: write_stance_file writes to proposals/, not knowledge/ (F17)
# ---------------------------------------------------------------------------

class TestWriteStanceFileWritesToProposals:
    """Bug F17: write_stance_file() writes LLM stance output directly to
    knowledge/stances/ (source-of-truth storage).  Per the core design
    principle, heuristic output must be proposal artifacts, never source
    mutations.  The output path must contain 'proposals/stances/'."""

    def test_output_path_is_under_proposals(self, tmp_path):
        """write_stance_file must write to proposals/stances/, not knowledge/stances/."""
        from propstore.relate import write_stance_file

        # Simulate a knowledge root with a proposals subdirectory
        knowledge_root = tmp_path / "knowledge"
        knowledge_root.mkdir()
        proposals_stances = tmp_path / "proposals" / "stances"
        # Do NOT pre-create — write_stance_file should target proposals/ internally

        stances = [{
            "target": "claim_b",
            "type": "supports",
            "strength": "strong",
            "note": "test",
            "conditions_differ": None,
            "resolution": {
                "method": "nli_first_pass",
                "model": "test-model",
                "confidence": 0.7,
                "opinion_belief": 0.0,
                "opinion_disbelief": 0.0,
                "opinion_uncertainty": 1.0,
                "opinion_base_rate": 0.7,
            },
        }]

        # Currently write_stance_file accepts stances_dir and writes there.
        # The caller passes knowledge/stances/.  After the fix, the output
        # path must route through proposals/stances/ instead.
        path = write_stance_file(
            knowledge_root / "stances", "claim_a", stances, "test-model"
        )

        # The returned path must be under proposals/, not knowledge/
        path_str = str(path).replace("\\", "/")
        assert "proposals/stances/" in path_str, (
            f"write_stance_file wrote to {path_str} — expected proposals/stances/. "
            "Heuristic output must be proposal artifacts, not source mutations."
        )


# ---------------------------------------------------------------------------
# Test 13: CorpusCalibrator reduces uncertainty in _classify_stance_async
# ---------------------------------------------------------------------------

class TestCorpusCalibReducesUncertainty:
    """Sub-task 1a: CorpusCalibrator should be used in _classify_stance_async
    to produce a non-vacuous opinion when reference_distances are available.

    Currently fails because CorpusCalibrator is never imported or used in
    relate.py — the embedding_distance is available but not converted to
    an opinion via corpus calibration.
    """

    def test_corpus_calibrator_reduces_uncertainty(self):
        """When _classify_stance_async is called with reference_distances,
        the resulting opinion should have uncertainty < 1.0 (non-vacuous).

        Per Josang 2001 (p.8): vacuous = total ignorance. With corpus
        calibration data, we have *some* evidence, so u must decrease.

        EXPECTED TO FAIL: _classify_stance_async does not accept
        reference_distances and never uses CorpusCalibrator.
        """
        import asyncio
        from propstore.relate import _classify_stance_async

        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = json.dumps({
            "type": "supports",
            "strength": "strong",
            "note": "test",
            "conditions_differ": None,
        })

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}
        reference_distances = [0.1, 0.2, 0.3, 0.4, 0.5]

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.relate._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await _classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                    embedding_distance=0.3,
                    reference_distances=reference_distances,
                    pass_number=1,
                )

        result = asyncio.run(run())
        assert result["resolution"]["opinion_uncertainty"] < 1.0, (
            "With reference_distances, opinion should be non-vacuous (u < 1.0). "
            "CorpusCalibrator must be used to convert embedding distance to opinion."
        )

    def test_no_reference_distances_stays_vacuous(self):
        """When reference_distances is None, behavior is unchanged — opinion
        is vacuous. Backward compatibility test.

        EXPECTED TO FAIL: _classify_stance_async does not accept
        reference_distances parameter (TypeError).
        """
        import asyncio
        from propstore.relate import _classify_stance_async

        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = json.dumps({
            "type": "supports",
            "strength": "strong",
            "note": "test",
            "conditions_differ": None,
        })

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.relate._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await _classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                    embedding_distance=0.3,
                    reference_distances=None,
                    pass_number=1,
                )

        result = asyncio.run(run())
        assert result["resolution"]["opinion_uncertainty"] == pytest.approx(1.0), (
            "Without reference_distances, opinion must remain vacuous (u = 1.0)"
        )

    def test_corpus_and_categorical_fused_via_consensus(self):
        """When both corpus opinion and categorical opinion are available,
        the result should have lower uncertainty than either alone.

        Per Josang 2001 (p.25, Theorem 7): consensus reduces uncertainty.
        Assert fused.u <= min(corpus.u, categorical.u).

        EXPECTED TO FAIL: no consensus fusion happens in _classify_stance_async.
        """
        import asyncio
        from propstore.relate import _classify_stance_async

        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = json.dumps({
            "type": "supports",
            "strength": "strong",
            "note": "test",
            "conditions_differ": None,
        })

        claim_a = {"id": "a", "text": "claim a", "source_paper": "paper_a"}
        claim_b = {"id": "b", "text": "claim b", "source_paper": "paper_b"}

        # Provide both reference_distances (for corpus opinion) and
        # calibration_counts (for categorical opinion)
        reference_distances = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        calibration_counts = {(1, "strong"): (80, 100)}

        async def run():
            sem = asyncio.Semaphore(1)
            with patch("propstore.relate._require_litellm") as mock_req:
                mock_litellm = MagicMock()
                mock_litellm.acompletion = AsyncMock(return_value=resp)
                mock_req.return_value = mock_litellm
                return await _classify_stance_async(
                    claim_a, claim_b, "test-model", sem,
                    embedding_distance=0.3,
                    reference_distances=reference_distances,
                    calibration_counts=calibration_counts,
                    pass_number=1,
                )

        result = asyncio.run(run())
        u = result["resolution"]["opinion_uncertainty"]

        # Compute what the individual opinions would give
        from propstore.calibrate import CorpusCalibrator, categorical_to_opinion
        corpus_op = CorpusCalibrator(reference_distances).to_opinion(0.3)
        cat_op = categorical_to_opinion("strong", 1, calibration_counts=calibration_counts)

        assert u <= min(corpus_op.u, cat_op.u) + 1e-9, (
            f"Fused uncertainty u={u} should be <= min(corpus.u={corpus_op.u}, "
            f"categorical.u={cat_op.u}). Consensus must reduce uncertainty "
            "(Josang 2001, Theorem 7, p.25)."
        )
