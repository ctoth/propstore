"""TDD tests for the notes field on claims.

Tests that claims can carry an optional free-text notes string, that
it roundtrips through validation, sidecar storage, and WorldQuery queries.
"""

import tempfile
from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import select
from quire.sqlalchemy_store import readonly_session

from tests.family_helpers import build_sidecar
from tests.family_helpers import load_claim_files
from tests.family_helpers import world_query_from_sqlite_path
from propstore.families.registry import world_schema
from propstore.families.claims.passes import validate_claims
from tests.conftest import (
    TEST_CONTEXT_ID,
    attach_claim_version_id,
    make_claim_identity,
    make_parameter_claim,
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
                f"claim{i + 1}",
                "concept1",
                200.0,
                "Hz",
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
            assert result.ok, (
                f"Validation failed for notes={notes_text!r}: {result.errors}"
            )
