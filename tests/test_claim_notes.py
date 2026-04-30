"""TDD tests for the notes field on claims.

Tests that claims can carry an optional free-text notes string, that
it roundtrips through validation, sidecar storage, and WorldQuery queries.
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.core.row_types import coerce_claim_row
from tests.family_helpers import build_sidecar
from tests.family_helpers import load_claim_files
from propstore.families.claims.passes import validate_claims
from propstore.world import WorldQuery
from tests.conftest import (
    TEST_CONTEXT_ID,
    attach_claim_version_id,
    make_claim_identity,
    make_parameter_claim,
    make_concept_registry,
    make_compilation_context,
    normalize_claims_payload,
    normalize_concept_payloads,
    write_test_context,
)


def make_claim_file_data(claims, paper="test_paper"):
    """Wrap claims in a ClaimFile structure."""
    normalized_claims = []
    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            normalized_claims.append(claim)
            continue
        normalized = dict(claim)
        if "artifact_id" not in normalized:
            raw_id = normalized.pop("id", f"claim{index}")
            normalized.update(make_claim_identity(str(raw_id), namespace=paper))
        normalized.setdefault("context", {"id": TEST_CONTEXT_ID})
        normalized["version_id"] = attach_claim_version_id(normalized)["version_id"]
        normalized_claims.append(normalized)
    return {
        "source": {"paper": paper},
        "claims": normalized_claims,
    }


def write_claim_file(claims_dir, filename, data):
    """Helper: write a claim YAML file."""
    path = claims_dir / filename
    path.write_text(yaml.dump(data, default_flow_style=False))
    return path


# ── Fixtures (reused patterns from test_build_sidecar) ──────────────


@pytest.fixture
def claims_dir(tmp_path):
    return tmp_path / "claims"


@pytest.fixture
def concept_dir(tmp_path):
    """Create a concepts directory with test concepts."""
    knowledge = tmp_path / "knowledge"
    concepts_path = knowledge / "concepts"
    concepts_path.mkdir(parents=True)
    write_test_context(knowledge)
    counters = concepts_path / ".counters"
    counters.mkdir()
    (counters / "speech.next").write_text("3")

    forms_dir = knowledge / "forms"
    forms_dir.mkdir()
    for form_name in ("frequency", "pressure"):
        (forms_dir / f"{form_name}.yaml").write_text(
            yaml.dump({"name": form_name, "dimensionless": False}, default_flow_style=False))

    def write(name, data):
        normalized = normalize_concept_payloads([data], default_domain="speech")[0]
        (concepts_path / f"{name}.yaml").write_text(
            yaml.dump(normalized, default_flow_style=False))

    write("fundamental_frequency", {
        "id": "concept1",
        "canonical_name": "fundamental_frequency",
        "status": "accepted",
        "definition": "The rate of vocal fold vibration during phonation.",
        "domain": "speech",
        "created_date": "2026-03-15",
        "form": "frequency",
    })

    write("subglottal_pressure", {
        "id": "concept2",
        "canonical_name": "subglottal_pressure",
        "status": "accepted",
        "definition": "Air pressure below the glottis during phonation.",
        "domain": "speech",
        "form": "pressure",
    })

    return concepts_path


@pytest.fixture
def sidecar_path(tmp_path):
    return tmp_path / "sidecar" / "propstore.sqlite"


# ── Unit Tests ───────────────────────────────────────────────────────


class TestClaimNotesValidation:
    """Validation tests for the notes field on claims."""

    def test_claim_with_notes_validates(self, claims_dir):
        """A parameter claim with notes: 'some note' validates against JSON schema."""
        claims_dir.mkdir(parents=True, exist_ok=True)
        claim = make_parameter_claim(
            "claim1", "concept1", 200.0, "Hz", notes="some note"
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        claim_files = load_claim_files(claims_dir)
        context = make_compilation_context()
        result = validate_claims(claim_files, context)
        assert result.ok, f"Validation errors: {result.errors}"

    def test_claim_without_notes_validates(self, claims_dir):
        """Existing claims without notes still validate (backward compat)."""
        claims_dir.mkdir(parents=True, exist_ok=True)
        claim = make_parameter_claim("claim1", "concept1", 200.0, "Hz")
        # Explicitly verify no notes key
        assert "notes" not in claim
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        claim_files = load_claim_files(claims_dir)
        context = make_compilation_context()
        result = validate_claims(claim_files, context)
        assert result.ok, f"Validation errors: {result.errors}"

    def test_notes_any_nonempty_string_valid(self, claims_dir):
        """Notes field accepts any non-empty string, no constraints."""
        claims_dir.mkdir(parents=True, exist_ok=True)
        notes_values = [
            "short",
            "A much longer note with special characters: !@#$%^&*()",
            "Multi\nline\nnotes",
            "Unicode: \u00e9\u00e0\u00fc\u00f1 \u4e16\u754c",
        ]
        claims = [
            make_parameter_claim(
                f"claim{i+1}", "concept1", 200.0, "Hz",
                notes=note,
            )
            for i, note in enumerate(notes_values)
        ]
        data = make_claim_file_data(claims)
        write_claim_file(claims_dir, "test_paper.yaml", data)

        claim_files = load_claim_files(claims_dir)
        context = make_compilation_context()
        result = validate_claims(claim_files, context)
        assert result.ok, f"Validation errors: {result.errors}"


class TestClaimNotesSidecar:
    """Sidecar storage tests for the notes field."""

    def test_sidecar_stores_notes_in_claim_table(
        self, concept_dir, sidecar_path
    ):
        """Build sidecar with a claim that has notes, verify notes column exists."""
        knowledge = concept_dir.parent
        claims_dir = knowledge / "claims"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "notes_paper"},
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 200.0,
                    "unit": "Hz",
                    "notes": "This is a test note",
                    "provenance": {"paper": "notes_paper", "page": 1},
                },
            ],
        }
        claim_data = normalize_claims_payload(claim_data)
        (claims_dir / "notes_paper.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )
        claim1_id = make_claim_identity("claim1", namespace="notes_paper")["artifact_id"]

        build_sidecar(knowledge, sidecar_path, force=True)

        conn = sqlite3.connect(sidecar_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT core.*, num.*, txt.*, alg.*
            FROM claim_core AS core
            LEFT JOIN claim_numeric_payload AS num ON num.claim_id = core.id
            LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
            LEFT JOIN claim_algorithm_payload AS alg ON alg.claim_id = core.id
            WHERE core.id=?
            """
        , (claim1_id,)).fetchone()
        assert "notes" in row.keys(), "notes column missing from normalized claim storage"
        assert row["notes"] == "This is a test note"
        conn.close()

    def test_world_query_get_claim_returns_notes(
        self, concept_dir, sidecar_path
    ):
        """After building sidecar, WorldQuery.get_claim returns notes field."""
        knowledge = concept_dir.parent
        claims_dir = knowledge / "claims"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "wm_notes_paper"},
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 200.0,
                    "unit": "Hz",
                    "notes": "WorldQuery test note",
                    "provenance": {"paper": "wm_notes_paper", "page": 1},
                },
            ],
        }
        claim_data = normalize_claims_payload(claim_data)
        (claims_dir / "wm_notes_paper.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        build_sidecar(knowledge, sidecar_path, force=True)

        # WorldQuery expects a repo-like object with .sidecar_path
        class _FakeRepo:
            def __init__(self, path):
                self.sidecar_path = path

        wm = WorldQuery(_FakeRepo(sidecar_path))
        claim = wm.get_claim(make_claim_identity("claim1", namespace="wm_notes_paper")["artifact_id"])
        assert claim is not None
        claim_data = coerce_claim_row(claim).to_dict()
        assert "notes" in claim_data, f"notes not in claim dict, keys: {list(claim_data.keys())}"
        assert claim_data["notes"] == "WorldQuery test note"
        wm.close()


# ── Hypothesis Property Tests ────────────────────────────────────────


class TestClaimNotesProperties:
    """Property-based tests for the notes field."""

    @settings(deadline=None)
    @pytest.mark.property
    @given(notes_text=st.text(min_size=1))
    def test_any_nonempty_string_produces_valid_claim(self, notes_text):
        """For any valid claim, adding a non-empty notes string produces a valid claim."""
        with tempfile.TemporaryDirectory() as td:
            claims_dir = Path(td) / "claims_hyp"
            claims_dir.mkdir(exist_ok=True)
            claim = make_parameter_claim(
                "claim1", "concept1", 200.0, "Hz", notes=notes_text
            )
            data = make_claim_file_data([claim])
            write_claim_file(claims_dir, "test_paper.yaml", data)

            claim_files = load_claim_files(claims_dir)
            context = make_compilation_context()
            result = validate_claims(claim_files, context)
            assert result.ok, f"Validation failed for notes={notes_text!r}: {result.errors}"

    @settings(deadline=None)
    @pytest.mark.property
    @given(notes_text=st.text(min_size=1, max_size=500))
    def test_notes_roundtrips_through_sidecar(self, notes_text):
        """Notes field roundtrips: write claim with notes -> build sidecar -> query -> same string."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            tmp_path = Path(td)
            # Set up minimal concept dir
            knowledge = tmp_path / "knowledge"
            concepts_path = knowledge / "concepts"
            concepts_path.mkdir(parents=True, exist_ok=True)
            write_test_context(knowledge)
            counters = concepts_path / ".counters"
            counters.mkdir(exist_ok=True)
            (counters / "speech.next").write_text("2")

            forms_dir = knowledge / "forms"
            forms_dir.mkdir(exist_ok=True)
            (forms_dir / "frequency.yaml").write_text(
                yaml.dump({"name": "frequency", "dimensionless": False}, default_flow_style=False))

            concept_payload = normalize_concept_payloads([{
                    "id": "concept1",
                    "canonical_name": "fundamental_frequency",
                    "status": "accepted",
                    "definition": "F0",
                    "domain": "speech",
                    "form": "frequency",
                }], default_domain="speech")[0]
            (concepts_path / "fundamental_frequency.yaml").write_text(
                yaml.dump(concept_payload, default_flow_style=False))

            claims_dir = knowledge / "claims"
            claims_dir.mkdir(exist_ok=True)
            claim_data = {
                "source": {"paper": "rt_paper"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "parameter",
                        "concept": "concept1",
                        "value": 200.0,
                        "unit": "Hz",
                        "notes": notes_text,
                        "provenance": {"paper": "rt_paper", "page": 1},
                    },
                ],
            }
            claim_data = normalize_claims_payload(claim_data)
            (claims_dir / "rt_paper.yaml").write_text(
                yaml.dump(claim_data, default_flow_style=False)
            )
            claim1_id = make_claim_identity("claim1", namespace="rt_paper")["artifact_id"]

            sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"
            build_sidecar(knowledge, sidecar_path, force=True)

            conn = sqlite3.connect(sidecar_path)
            try:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT notes FROM claim_text_payload WHERE claim_id=?",
                    (claim1_id,),
                ).fetchone()
                assert row is not None, "claim artifact not found in sidecar"
                assert row["notes"] == notes_text, (
                    f"Notes roundtrip failed: wrote {notes_text!r}, got {row['notes']!r}"
                )
            finally:
                conn.close()
