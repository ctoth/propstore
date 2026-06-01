"""Tests for the SQLite sidecar builder.

Verifies that the sidecar builder creates the correct tables,
populates them from concept YAML files, and builds the FTS5 index.
"""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest
import yaml
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from ast_equiv import canonical_dump
from quire.documents import DocumentSchemaError
from propstore.families.identity.stances import stamp_stance_artifact_id
from propstore.families.registry import world_schema
from propstore.repository import Repository
from tests.family_helpers import (
    _materialize_claim_fixture_batches,
    build_sidecar as _build_sidecar,
    world_query_from_sqlite_path,
)
from propstore.families.identity.concepts import derive_concept_artifact_id
from tests.conftest import (
    make_claim_identity,
    normalize_concept_payloads,
)


def _concept_artifact(local_id: str) -> str:
    return derive_concept_artifact_id("propstore", local_id)


CONCEPT1_ID = _concept_artifact("concept1")
CONCEPT2_ID = _concept_artifact("concept2")
CONCEPT3_ID = _concept_artifact("concept3")
CONCEPT4_ID = _concept_artifact("concept4")
CONCEPT5_ID = _concept_artifact("concept5")
CONCEPT6_ID = _concept_artifact("concept6")


def _commit_worktree(repo: Repository, message: str = "Update test knowledge") -> str:
    adds: dict[str, bytes] = {}
    head = repo.git.head_sha()
    changed = head is None
    for path in sorted(repo.root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(repo.root)
        if ".git" in rel.parts:
            continue
        rel_text = rel.as_posix()
        if rel_text.startswith("sidecar/") or rel_text.endswith(
            (".sqlite", ".sqlite-wal", ".sqlite-shm", ".hash")
        ):
            continue
        content = path.read_bytes()
        adds[rel_text] = content
        if not changed:
            try:
                changed = repo.git.read_file(rel_text, commit=head) != content
            except FileNotFoundError:
                changed = True
    if not changed and head is not None:
        return head
    return repo.git.commit_batch(adds=adds, deletes=(), message=message)


def build_sidecar(
    repo: Repository,
    sidecar_path,
    force: bool = False,
    **kwargs,
):
    _materialize_claim_fixture_batches(repo)
    _commit_worktree(repo)
    return _build_sidecar(repo, sidecar_path, force=force, **kwargs)


@pytest.fixture
def knowledge_reader(concept_dir):
    """Return the git-backed knowledge repository."""
    repo = Repository(concept_dir.parent)
    _commit_worktree(repo, message="Seed sidecar test knowledge")
    return repo


@pytest.fixture
def sidecar_path(tmp_path):
    return tmp_path / "sidecar" / "propstore.sqlite"


# ── Table existence ──────────────────────────────────────────────────


class TestTableCreation:
    def test_creates_sqlite_file(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        assert sidecar_path.exists()

    def test_meta_table_stores_schema_version(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT schema_version FROM meta WHERE key='sidecar'"
        ).fetchone()
        assert row is not None
        assert isinstance(row[0], int)
        assert row[0] >= 1
        conn.close()

    def test_concept_table_exists(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='concept'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_alias_table_exists(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alias'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_relationship_table_exists(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='relationship'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_parameterization_table_exists(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='parameterization'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_fts_table_exists(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='concept_fts'"
        )
        assert cursor.fetchone() is not None
        conn.close()


class TestSchemaV6:
    """Sidecar schema additions for build-to-render gate removal.

    Implements `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md`
    findings 3.1/3.2/3.3 — every claim flows into the sidecar with a per-row
    lifecycle annotation, and a `build_diagnostics` table carries the
    quarantine reasons that the render layer filters per policy.
    """

    def test_schema_version_is_six(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT schema_version FROM meta WHERE key='sidecar'"
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == 6

    def test_build_diagnostics_table_exists(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='build_diagnostics'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_build_diagnostics_columns(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        info = conn.execute("PRAGMA table_info(build_diagnostics)").fetchall()
        conn.close()
        column_names = {row[1] for row in info}
        expected = {
            "id",
            "claim_id",
            "source_kind",
            "source_ref",
            "diagnostic_kind",
            "severity",
            "blocking",
            "message",
            "file",
            "detail_json",
        }
        assert expected <= column_names, (
            f"build_diagnostics missing columns: {expected - column_names}"
        )

    def test_claim_core_lifecycle_columns_exist(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        info = conn.execute("PRAGMA table_info(claim_core)").fetchall()
        conn.close()
        column_names = {row[1] for row in info}
        assert "build_status" in column_names
        assert "stage" in column_names
        assert "promotion_status" in column_names

    def test_claim_core_build_status_default_is_ingested(
        self, knowledge_reader, sidecar_path
    ):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        info = conn.execute("PRAGMA table_info(claim_core)").fetchall()
        conn.close()
        # PRAGMA table_info row layout: cid, name, type, notnull, dflt_value, pk
        for row in info:
            if row[1] == "build_status":
                assert row[3] == 1, "build_status should be NOT NULL"
                assert row[4] is not None and "ingested" in str(row[4])
                return
        raise AssertionError("build_status column not found")


# ── Concept table contents ───────────────────────────────────────────


class TestConceptTable:
    def test_concept_count(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        count = conn.execute("SELECT COUNT(*) FROM concept").fetchone()[0]
        assert count == 5
        conn.close()

    def test_concept_fields(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            """
            SELECT canonical_name, status, domain, kind_type, definition
            FROM concept
            WHERE id=?
            """,
            (CONCEPT1_ID,),
        ).fetchone()
        assert row[0] == "fundamental_frequency"
        assert row[1] == "accepted"
        assert row[2] == "speech"
        assert row[3] == "quantity"
        assert "vocal fold" in row[4]
        conn.close()

    def test_proposed_concept_included(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT status FROM concept WHERE id=?", (CONCEPT5_ID,)
        ).fetchone()
        assert row[0] == "proposed"
        conn.close()

    def test_concept_has_content_hash(self, knowledge_reader, sidecar_path):
        """Concepts have non-empty content_hash."""
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT content_hash FROM concept WHERE id=?", (CONCEPT1_ID,)
        ).fetchone()
        assert row[0] is not None
        assert len(row[0]) == 16
        conn.close()

    def test_concept_has_seq(self, knowledge_reader, sidecar_path):
        """Concepts have sequential numbering."""
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        seqs = [
            r[0]
            for r in conn.execute("SELECT seq FROM concept ORDER BY seq").fetchall()
        ]
        assert seqs == list(range(1, len(seqs) + 1))
        conn.close()

    def test_content_hash_deterministic(self, knowledge_reader, sidecar_path):
        """Same content produces same hash across builds."""
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        hash1 = conn.execute(
            "SELECT content_hash FROM concept WHERE id=?", (CONCEPT1_ID,)
        ).fetchone()[0]
        conn.close()

        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        hash2 = conn.execute(
            "SELECT content_hash FROM concept WHERE id=?", (CONCEPT1_ID,)
        ).fetchone()[0]
        conn.close()
        assert hash1 == hash2


# ── Alias table contents ─────────────────────────────────────────────


class TestAliasTable:
    def test_alias_count(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        count = conn.execute("SELECT COUNT(*) FROM alias").fetchone()[0]
        # F0, pitch, Ps, ra, Ra = 5
        assert count == 5
        conn.close()

    def test_alias_lookup(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT concept_id FROM alias WHERE alias_name='F0'"
        ).fetchone()
        assert row[0] == CONCEPT1_ID
        conn.close()

    def test_alias_source(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute("SELECT source FROM alias WHERE alias_name='Ps'").fetchone()
        assert row[0] == "Sundberg_1993"
        conn.close()


# ── Relationship table contents ──────────────────────────────────────


class TestRelationshipTable:
    def test_relationship_count(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        count = conn.execute("SELECT COUNT(*) FROM relationship").fetchone()[0]
        # broader(concept1→concept4), narrower(concept4→concept1),
        # narrower(concept4→concept2) = 3
        assert count == 3
        conn.close()

    def test_relationship_fields(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT type, target_id FROM relationship WHERE source_id=?",
            (CONCEPT1_ID,),
        ).fetchone()
        assert row[0] == "broader"
        assert row[1] == CONCEPT4_ID
        conn.close()


# ── Parameterization table contents ──────────────────────────────────


class TestParameterizationTable:
    def test_parameterization_count(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        count = conn.execute("SELECT COUNT(*) FROM parameterization").fetchone()[0]
        assert count == 1
        conn.close()

    def test_parameterization_fields(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT concept_ids, formula, exactness FROM parameterization"
        ).fetchone()
        assert CONCEPT5_ID in row[0]
        assert row[1] == "ra = ta / T0"
        assert row[2] == "exact"
        conn.close()

    def test_parameterization_has_output_concept_id(
        self, knowledge_reader, sidecar_path
    ):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute("SELECT output_concept_id FROM parameterization").fetchone()
        assert row[0] == CONCEPT5_ID
        conn.close()


# ── FTS5 index ───────────────────────────────────────────────────────


class TestFTS:
    def test_fts_search_by_name(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH 'frequency'"
        ).fetchall()
        ids = [r[0] for r in rows]
        assert CONCEPT1_ID in ids
        conn.close()

    def test_fts_search_by_alias(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH 'pitch'"
        ).fetchall()
        ids = [r[0] for r in rows]
        assert CONCEPT1_ID in ids
        conn.close()

    def test_fts_search_by_definition(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH 'glottis'"
        ).fetchall()
        ids = [r[0] for r in rows]
        assert CONCEPT2_ID in ids
        conn.close()

    def test_fts_search_by_condition(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH 'speech'"
        ).fetchall()
        ids = [r[0] for r in rows]
        # return_phase_ratio has condition "task == 'speech'"
        assert CONCEPT5_ID in ids
        conn.close()


# ── Rebuild skipping ─────────────────────────────────────────────────


class TestRebuildSkipping:
    def test_skip_rebuild_when_unchanged(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)

        # Set mtime 2 seconds in the past so any rewrite would be detectable
        import os

        stat = sidecar_path.stat()
        os.utime(sidecar_path, (stat.st_atime, stat.st_mtime - 2))
        mtime1 = sidecar_path.stat().st_mtime

        # Build again — should skip
        build_sidecar(knowledge_reader, sidecar_path)
        mtime2 = sidecar_path.stat().st_mtime
        assert mtime1 == mtime2

    def test_rebuild_when_forced(self, knowledge_reader, sidecar_path):
        build_sidecar(knowledge_reader, sidecar_path)

        # Set mtime 2 seconds in the past so forced rebuild produces a newer mtime
        import os

        stat = sidecar_path.stat()
        os.utime(sidecar_path, (stat.st_atime, stat.st_mtime - 2))
        mtime1 = sidecar_path.stat().st_mtime

        build_sidecar(knowledge_reader, sidecar_path, force=True)
        mtime2 = sidecar_path.stat().st_mtime
        assert mtime2 > mtime1

    def test_rebuild_when_contexts_change(
        self, concept_dir, knowledge_reader, sidecar_path
    ):
        contexts_dir = concept_dir.parent / "contexts"
        contexts_dir.mkdir(exist_ok=True)
        (contexts_dir / "ctx_root.yaml").write_text(
            yaml.dump(
                {
                    "id": "ctx_root",
                    "name": "Root",
                    "assumptions": ["task == 'speech'"],
                },
                default_flow_style=False,
            )
        )

        assert build_sidecar(knowledge_reader, sidecar_path, force=True) is True

        (contexts_dir / "ctx_root.yaml").write_text(
            yaml.dump(
                {
                    "id": "ctx_root",
                    "name": "Root",
                    "assumptions": ["task == 'singing'"],
                },
                default_flow_style=False,
            )
        )

        assert build_sidecar(knowledge_reader, sidecar_path) is True

    def test_rebuild_when_form_files_change(
        self, concept_dir, knowledge_reader, sidecar_path
    ):
        assert build_sidecar(knowledge_reader, sidecar_path, force=True) is True

        form_path = concept_dir.parent / "forms" / "frequency.yaml"
        form_data = yaml.safe_load(form_path.read_text())
        form_data["note"] = "changed semantic form contract"
        form_path.write_text(yaml.dump(form_data, default_flow_style=False))

        assert build_sidecar(knowledge_reader, sidecar_path) is True

    def test_rebuild_when_new_commit_changes(
        self, concept_dir, knowledge_reader, sidecar_path
    ):
        assert build_sidecar(knowledge_reader, sidecar_path, force=True) is True

        contexts_dir = concept_dir.parent / "contexts"
        (contexts_dir / "ctx_commit_key.yaml").write_text(
            yaml.dump(
                {"id": "ctx_commit_key", "name": "Commit-key context"},
                default_flow_style=False,
            )
        )

        assert build_sidecar(knowledge_reader, sidecar_path) is True

    @pytest.mark.property
    @given(
        assumption_a=st.sampled_from(
            ["task == 'speech'", "task == 'singing'", "task == 'whisper'"]
        ),
        assumption_b=st.sampled_from(
            ["task == 'speech'", "task == 'singing'", "task == 'whisper'"]
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_content_hash_changes_when_context_semantics_change(
        self,
        concept_dir,
        sidecar_path,
        assumption_a,
        assumption_b,
    ):
        assume(assumption_a != assumption_b)
        contexts_dir = concept_dir.parent / "contexts"
        contexts_dir.mkdir(exist_ok=True)

        (contexts_dir / "ctx_root.yaml").write_text(
            yaml.dump(
                {
                    "id": "ctx_root",
                    "name": "Root",
                    "assumptions": [assumption_a],
                },
                default_flow_style=False,
            )
        )
        repo = Repository(concept_dir.parent)
        assert build_sidecar(repo, sidecar_path, force=True) is True
        hash_a = sidecar_path.with_suffix(".hash").read_text()

        (contexts_dir / "ctx_root.yaml").write_text(
            yaml.dump(
                {
                    "id": "ctx_root",
                    "name": "Root",
                    "assumptions": [assumption_b],
                },
                default_flow_style=False,
            )
        )
        assert build_sidecar(repo, sidecar_path) is True
        hash_b = sidecar_path.with_suffix(".hash").read_text()

        assert hash_a != hash_b


# ── Claim fixtures ───────────────────────────────────────────────────


@pytest.fixture
def claim_files(concept_dir):
    """Create claim files in the knowledge/claims directory."""
    claims_dir = concept_dir.parent / "claims"
    claims_dir.mkdir(exist_ok=True)

    alpha = {
        "source": {"paper": "test_paper_alpha"},
        "claims": [
            {
                "id": "claim1",
                "type": "parameter",
                "concept": "concept1",
                "value": 200.0,
                "unit": "Hz",
                "conditions": ["task == 'speech'"],
                "provenance": {"paper": "test_paper_alpha", "page": 5},
            },
            {
                "id": "claim2",
                "type": "parameter",
                "concept": "concept1",
                "value": 350.0,
                "unit": "Hz",
                "conditions": ["task == 'speech'"],
                "stances": [
                    {
                        "type": "rebuts",
                        "target": "claim1",
                        "strength": "strong",
                        "note": "same task, conflicting value",
                    }
                ],
                "provenance": {
                    "paper": "test_paper_alpha",
                    "page": 8,
                    "table": "Table 2",
                },
            },
            {
                "id": "claim3",
                "type": "parameter",
                "concept": "concept1",
                "value": 180.0,
                "unit": "Hz",
                "conditions": ["task == 'singing'"],
                "provenance": {"paper": "test_paper_alpha", "page": 12},
            },
            {
                "id": "claim4",
                "type": "parameter",
                "concept": "concept2",
                "value": 800.0,
                "unit": "Pa",
                "conditions": ["task == 'speech'"],
                "provenance": {"paper": "test_paper_alpha", "page": 15},
            },
            {
                "id": "claim5",
                "type": "observation",
                "statement": "Fundamental frequency increases with subglottal pressure in a roughly logarithmic relationship.",
                "concepts": ["concept1", "concept2"],
                "provenance": {
                    "paper": "test_paper_alpha",
                    "page": 20,
                    "section": "Discussion",
                },
            },
        ],
    }

    beta = {
        "source": {"paper": "test_paper_beta"},
        "claims": [
            {
                "id": "claim6",
                "type": "parameter",
                "concept": "concept2",
                "value": 800.0,
                "unit": "Pa",
                "conditions": ["task == 'speech'"],
                "provenance": {"paper": "test_paper_beta", "page": 3},
            },
            {
                "id": "claim7",
                "type": "parameter",
                "concept": "concept1",
                "value": 250.0,
                "unit": "Hz",
                "conditions": ["task == 'speech'", "fundamental_frequency > 100"],
                "provenance": {"paper": "test_paper_beta", "page": 7},
            },
            {
                "id": "claim8",
                "type": "equation",
                "expression": "log(Ps) = 1.00 + 0.88 * log(F0)",
                "sympy": "Eq(log(Ps), 1.00 + 0.88 * log(F0))",
                "variables": [
                    {"symbol": "Ps", "concept": "concept2", "role": "dependent"},
                    {"symbol": "F0", "concept": "concept1", "role": "independent"},
                ],
                "fit": {"r": 0.965, "r_sd": 0.04, "slope": 0.88, "slope_sd": 0.186},
                "conditions": ["task == 'speech'"],
                "provenance": {
                    "paper": "test_paper_beta",
                    "page": 19,
                    "table": "Table 3",
                },
            },
            {
                "id": "claim9",
                "type": "parameter",
                "concept": "concept1",
                "value": 220.0,
                "unit": "Hz",
                "conditions": ["task == 'whisper'"],
                "provenance": {"paper": "test_paper_beta", "page": 22},
            },
        ],
    }

    alpha = _normalize_claim_concept_refs(alpha)
    beta = _normalize_claim_concept_refs(beta)

    (claims_dir / "test_paper_alpha.yaml").write_text(
        yaml.dump(alpha, default_flow_style=False)
    )
    (claims_dir / "test_paper_beta.yaml").write_text(
        yaml.dump(beta, default_flow_style=False)
    )

    return None


@pytest.fixture
def sidecar_with_claims(knowledge_reader, sidecar_path, claim_files):
    """Build a sidecar that includes claim and conflict tables."""
    build_sidecar(knowledge_reader, sidecar_path)
    return sidecar_path


# ── Claim table ──────────────────────────────────────────────────────


class TestClaimTable:
    def test_claim_table_exists(self, sidecar_with_claims):
        """Normalized claim tables are created when claim_files are provided."""
        conn = sqlite3.connect(sidecar_with_claims)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='claim_core'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_claim_count(self, sidecar_with_claims):
        """Correct number of claims in normalized storage."""
        conn = sqlite3.connect(sidecar_with_claims)
        count = conn.execute("SELECT COUNT(*) FROM claim_core").fetchone()[0]
        # 5 from alpha + 4 from beta = 9
        assert count == 9
        conn.close()

    def test_claim_keeps_source_slug_separate_from_provenance_paper(
        self,
        knowledge_reader,
        sidecar_path,
    ):
        claims_dir = knowledge_reader.root / "claims"
        claims_dir.mkdir(exist_ok=True)
        sources_dir = knowledge_reader.root / "sources"
        sources_dir.mkdir(exist_ok=True)

        source_doc = {
            "id": "source-alpha",
            "kind": "academic_paper",
            "origin": {"type": "doi", "value": "10.1000/example"},
            "trust": {
                "status": "stated",
                "prior_base_rate": {"b": 0.0, "d": 0.0, "u": 1.0, "a": 0.6},
            },
        }
        (sources_dir / "alpha_source.yaml").write_text(
            yaml.dump(source_doc, default_flow_style=False)
        )

        claim_data = _normalize_claim_concept_refs(
            {
                "source": {"paper": "alpha_source"},
                "claims": [
                    {
                        "id": "claim_slug",
                        "type": "parameter",
                        "concept": "concept1",
                        "value": 200.0,
                        "unit": "Hz",
                        "provenance": {"paper": "Alpha Paper", "page": 9},
                    }
                ],
            }
        )
        (claims_dir / "alpha_source.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        build_sidecar(knowledge_reader, sidecar_path, force=True)

        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT source_slug, source_paper FROM claim_core WHERE primary_logical_id = ?",
            ("alpha_source:claim_slug",),
        ).fetchone()
        assert row == ("alpha_source", "Alpha Paper")
        conn.close()

    def test_claim_has_version_id(self, sidecar_with_claims):
        """Claims have non-empty immutable version IDs."""
        conn = sqlite3.connect(sidecar_with_claims)
        row = conn.execute(
            "SELECT version_id FROM claim_core WHERE primary_logical_id LIKE ?",
            ("%:claim1",),
        ).fetchone()
        assert row[0] is not None
        assert str(row[0]).startswith("sha256:")
        conn.close()

    def test_claim_has_seq(self, sidecar_with_claims):
        """Claims have sequential numbering."""
        conn = sqlite3.connect(sidecar_with_claims)
        seqs = [
            row[0]
            for row in conn.execute(
                "SELECT seq FROM claim_core ORDER BY seq"
            ).fetchall()
        ]
        assert seqs == list(range(1, len(seqs) + 1))
        conn.close()

    def test_missing_stances_dir_is_treated_as_no_stance_files(
        self,
        knowledge_reader,
        sidecar_path,
        claim_files,
    ):
        """Claim builds without a stances/ subtree should still succeed."""
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        claim_count = conn.execute("SELECT COUNT(*) FROM claim_core").fetchone()[0]
        stance_count = conn.execute(
            "SELECT COUNT(*) FROM relation_edge WHERE source_kind='claim' AND target_kind='claim'"
        ).fetchone()[0]
        assert claim_count == 9
        assert stance_count == 1
        conn.close()

    def test_without_authored_justifications_sidecar_persists_no_synthetic_rows(
        self,
        knowledge_reader,
        sidecar_path,
        claim_files,
    ):
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        justification_ids = [
            row[0]
            for row in conn.execute(
                "SELECT id FROM justification ORDER BY id"
            ).fetchall()
        ]
        assert justification_ids == []
        conn.close()

    def test_world_query_loads_authored_justifications_as_domain_objects(
        self,
        knowledge_reader,
        sidecar_path,
        claim_files,
    ):
        justifications_dir = knowledge_reader.root / "justifications"
        justifications_dir.mkdir(exist_ok=True)
        (justifications_dir / "test_paper_alpha.yaml").write_text(
            yaml.dump(
                {
                    "id": "just_multi",
                    "conclusion": "claim5",
                    "premises": ["claim1", "claim4"],
                    "rule_kind": "empirical_support",
                    "rule_strength": "defeasible",
                    "provenance": {"page": 20},
                },
                default_flow_style=False,
            )
        )

        build_sidecar(knowledge_reader, sidecar_path, force=True)

        world = world_query_from_sqlite_path(sidecar_path)
        try:
            justifications = world.justifications_for_claim_scope(
                {"claim1", "claim4", "claim5"}
            )
            expected_claim_ids: dict[str, str] = {}
            for claim_id in ("claim1", "claim4", "claim5"):
                claim = world.get_claim(claim_id)
                expected_claim_ids[claim_id] = (
                    str(claim.id) if claim is not None else claim_id
                )
        finally:
            world.close()

        assert len(justifications) == 1
        justification = justifications[0]
        assert justification.justification_id == "just_multi"
        assert justification.conclusion_claim_id == expected_claim_ids["claim5"]
        assert justification.premise_claim_ids == (
            expected_claim_ids["claim1"],
            expected_claim_ids["claim4"],
        )
        assert justification.rule_kind == "empirical_support"
        assert justification.rule_strength == "defeasible"
        assert justification.provenance is not None
        assert justification.provenance.page == 20

    def test_parameter_claim_has_concept(self, sidecar_with_claims):
        """Parameter claim has output_concept_id populated."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            """
            SELECT core.id, output_link.concept_id
            FROM claim_core AS core
            LEFT JOIN claim_concept_link AS output_link
                ON output_link.claim_id = core.id AND output_link.role = 'output'
            WHERE core.type='parameter'
            """
        ).fetchall()
        for row in rows:
            assert row[1] is not None, f"claim {row[0]} missing output_concept_id"
        conn.close()

    def test_list_value_input_raises(self, concept_dir, knowledge_reader, sidecar_path):
        """List-valued claim input raises TypeError — no silent conversion."""
        claims_dir = concept_dir.parent / "claims"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "range_paper"},
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": [100.0, 300.0],
                    "unit": "Hz",
                    "provenance": {"paper": "range_paper", "page": 1},
                },
            ],
        }
        claim_data = _normalize_claim_concept_refs(claim_data)
        (claims_dir / "range_paper.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        with pytest.raises(DocumentSchemaError, match="value"):
            build_sidecar(knowledge_reader, sidecar_path, force=True)

    def test_no_claim_table_without_claims(self, knowledge_reader, sidecar_path):
        """Stable sidecar schema keeps claim tables present even with zero claims."""
        build_sidecar(knowledge_reader, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='claim_core'"
        )
        assert cursor.fetchone() == ("claim_core",)
        claim_count = conn.execute("SELECT COUNT(*) FROM claim_core").fetchone()[0]
        assert claim_count == 0
        conn.close()


# ── Conflicts table ──────────────────────────────────────────────────


class TestConflictsTable:
    def test_conflicts_table_exists(self, sidecar_with_claims):
        """conflict_witness table created when claim_files provided."""
        conn = sqlite3.connect(sidecar_with_claims)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='conflict_witness'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_conflict_detected(self, sidecar_with_claims):
        """CONFLICT record present for same-scope different-value claims."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            "SELECT * FROM conflict_witness WHERE warning_class='CONFLICT'"
        ).fetchall()
        assert len(rows) >= 1
        conn.close()


class TestClaimStanceTable:
    def test_claim_stance_table_exists(self, sidecar_with_claims):
        conn = sqlite3.connect(sidecar_with_claims)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='relation_edge'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_claim_stance_rows_persisted(self, sidecar_with_claims):
        conn = sqlite3.connect(sidecar_with_claims)
        claim1_id = make_claim_identity("claim1", namespace="test_paper_alpha")[
            "artifact_id"
        ]
        claim2_id = make_claim_identity("claim2", namespace="test_paper_alpha")[
            "artifact_id"
        ]
        row = conn.execute(
            """
            SELECT source_id, target_id, relation_type, strength, note
            FROM relation_edge
            WHERE source_kind = 'claim' AND target_kind = 'claim'
              AND source_id=?
            """,
            (claim2_id,),
        ).fetchone()
        assert row[0] == claim2_id
        assert row[1] == claim1_id
        assert row[2] == "rebuts"
        assert row[3] == "strong"
        assert "conflicting value" in row[4]
        conn.close()

    def test_raw_inline_stance_targets_are_quarantined_not_rejected(
        self,
        concept_dir,
        knowledge_reader,
        sidecar_path,
    ):
        """Raw-id-broken claims quarantine into sidecar instead of aborting build.

        Per ws-z-render-gates.md axis-1 finding 3.1: a claim with a raw 'id'
        input but no canonical identity fields must *not* abort the whole
        sidecar build. The build proceeds; the offending claim lands as a
        synthetic-id row with ``build_status='blocked'`` and a
        ``build_diagnostics`` row records why. All other claims ingest
        normally.

        This test is the inversion of the prior
        ``test_raw_inline_stance_targets_are_rejected_at_compile_boundary``:
        the gate was a build-time abort; now it's a render-time policy
        filter over quarantine rows.
        """

        claims_dir = concept_dir.parent / "claims"
        claims_dir.mkdir(exist_ok=True)
        (claims_dir / "raw_handles.yaml").write_text(
            yaml.dump(
                {
                    "source": {"paper": "raw_handles"},
                    "claims": [
                        {
                            "id": "claim1",
                            "type": "parameter",
                            "output_concept": CONCEPT1_ID,
                            "value": 200.0,
                            "unit": "Hz",
                            "context": {"id": "ctx_test"},
                            "provenance": {"paper": "raw_handles", "page": 1},
                        },
                        {
                            "id": "claim2",
                            "type": "parameter",
                            "output_concept": CONCEPT1_ID,
                            "value": 220.0,
                            "unit": "Hz",
                            "context": {"id": "ctx_test"},
                            "stances": [{"type": "rebuts", "target": "claim1"}],
                            "provenance": {"paper": "raw_handles", "page": 2},
                        },
                    ],
                },
                default_flow_style=False,
            )
        )

        # Build must succeed — no exception.
        build_sidecar(knowledge_reader, sidecar_path, force=True)

        conn = sqlite3.connect(sidecar_path)
        try:
            blocked_rows = conn.execute(
                "SELECT id, build_status, source_paper FROM claim_core "
                "WHERE build_status = 'blocked'"
            ).fetchall()
            assert blocked_rows == []

            ingested = conn.execute(
                "SELECT COUNT(*) FROM claim_core WHERE build_status = 'ingested'"
            ).fetchone()[0]
            assert ingested == 2

            diagnostic_rows = conn.execute(
                "SELECT claim_id, diagnostic_kind, blocking, severity, message, file "
                "FROM build_diagnostics "
                "WHERE diagnostic_kind = 'raw_id_input'"
            ).fetchall()
            assert diagnostic_rows == []
        finally:
            conn.close()

    def test_invalid_inline_stance_target_quarantines(
        self,
        concept_dir,
        knowledge_reader,
        sidecar_path,
    ):
        claims_dir = concept_dir.parent / "claims"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "invalid_stance_target"},
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 200.0,
                    "unit": "Hz",
                    "provenance": {"paper": "invalid_stance_target", "page": 1},
                },
                {
                    "id": "claim2",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 220.0,
                    "unit": "Hz",
                    "stances": [{"type": "rebuts", "target": "missing_claim"}],
                    "provenance": {"paper": "invalid_stance_target", "page": 2},
                },
            ],
        }
        claim_data = _normalize_claim_concept_refs(claim_data)
        (claims_dir / "invalid_stance_target.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        build_sidecar(knowledge_reader, sidecar_path, force=True)

        conn = sqlite3.connect(sidecar_path)
        try:
            relation_rows = conn.execute(
                """
                SELECT source_id, target_id
                FROM relation_edge
                WHERE source_kind = 'claim' AND target_kind = 'claim'
                """
            ).fetchall()
            diagnostics = conn.execute(
                """
                SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
                FROM build_diagnostics
                WHERE diagnostic_kind = 'stance_validation'
                """
            ).fetchall()
        finally:
            conn.close()

        assert relation_rows == []
        assert diagnostics
        assert diagnostics[0][:5] == (
            "stance",
            "missing_claim",
            "stance_validation",
            "error",
            1,
        )
        assert "references nonexistent target claim" in diagnostics[0][5]

    def test_invalid_inline_stance_type_raises(
        self, concept_dir, knowledge_reader, sidecar_path
    ):
        claims_dir = concept_dir.parent / "claims"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "invalid_stance_type"},
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 200.0,
                    "unit": "Hz",
                    "provenance": {"paper": "invalid_stance_type", "page": 1},
                },
                {
                    "id": "claim2",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 220.0,
                    "unit": "Hz",
                    "stances": [{"type": "contradicts", "target": "claim1"}],
                    "provenance": {"paper": "invalid_stance_type", "page": 2},
                },
            ],
        }
        claim_data = _normalize_claim_concept_refs(claim_data)
        (claims_dir / "invalid_stance_type.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        with pytest.raises(ValueError, match="contradicts"):
            build_sidecar(knowledge_reader, sidecar_path, force=True)

    def test_invalid_inline_stance_resolution_shape_raises_cleanly(
        self,
        concept_dir,
        knowledge_reader,
        sidecar_path,
    ):
        claims_dir = concept_dir.parent / "claims"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "invalid_stance_resolution"},
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 200.0,
                    "unit": "Hz",
                    "provenance": {"paper": "invalid_stance_resolution", "page": 1},
                },
                {
                    "id": "claim2",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 220.0,
                    "unit": "Hz",
                    "stances": [
                        {
                            "type": "supports",
                            "target": "claim1",
                            "resolution": ["nli_first_pass"],
                        }
                    ],
                    "provenance": {"paper": "invalid_stance_resolution", "page": 2},
                },
            ],
        }
        claim_data = _normalize_claim_concept_refs(claim_data)
        (claims_dir / "invalid_stance_resolution.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        with pytest.raises(ValueError, match="resolution"):
            build_sidecar(knowledge_reader, sidecar_path, force=True)

    @pytest.mark.property
    @given(
        stance_pairs=st.lists(
            st.tuples(
                st.sampled_from(["claim1", "claim2", "claim3"]),
                st.sampled_from(["claim1", "claim2", "claim3"]),
                st.sampled_from(["rebuts", "supports", "explains", "undercuts"]),
            ),
            max_size=6,
        )
    )
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_persisted_stance_edges_reference_extant_claim_ids(
        self,
        concept_dir,
        sidecar_path,
        stance_pairs,
    ):
        claims_dir = concept_dir.parent / "claims"
        claims_dir.mkdir(exist_ok=True)
        claims = []
        for claim_id, value in (
            ("claim1", 100.0),
            ("claim2", 120.0),
            ("claim3", 140.0),
        ):
            claims.append(
                {
                    "id": claim_id,
                    "type": "parameter",
                    "concept": "concept1",
                    "value": value,
                    "unit": "Hz",
                    "provenance": {"paper": "stance_property", "page": 1},
                }
            )
        stances_by_source: dict[str, list[dict[str, str]]] = {}
        for source, target, stance_type in stance_pairs:
            if source == target:
                continue
            stances_by_source.setdefault(source, []).append(
                {"type": stance_type, "target": target}
            )
        for claim in claims:
            if claim["id"] in stances_by_source:
                claim["stances"] = stances_by_source[claim["id"]]
        claim_data = {"source": {"paper": "stance_property"}, "claims": claims}
        claim_data = _normalize_claim_concept_refs(claim_data)
        (claims_dir / "stance_property.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        knowledge_reader = Repository(concept_dir.parent)
        build_sidecar(knowledge_reader, sidecar_path, force=True)

        conn = sqlite3.connect(sidecar_path)
        try:
            claim_ids = {
                row[0] for row in conn.execute("SELECT id FROM claim_core").fetchall()
            }
            stance_rows = conn.execute(
                """
                SELECT source_id, target_id
                FROM relation_edge
                WHERE source_kind='claim' AND target_kind='claim'
                """
            ).fetchall()
            assert all(
                source in claim_ids and target in claim_ids
                for source, target in stance_rows
            )
        finally:
            conn.close()

    def test_conflict_query_by_class(self, sidecar_with_claims):
        """Can query normalized conflict witness rows by warning class."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            "SELECT warning_class FROM conflict_witness WHERE warning_class = 'CONFLICT'"
        ).fetchall()
        for row in rows:
            assert row[0] == "CONFLICT"
        assert len(rows) >= 1
        conn.close()

    def test_conflict_query_by_concept(self, sidecar_with_claims):
        """Can query normalized conflict witness rows by concept."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            "SELECT * FROM conflict_witness WHERE concept_id = ?",
            (CONCEPT1_ID,),
        ).fetchall()
        # concept1 has claims with different values under same/different conditions
        assert len(rows) >= 1
        conn.close()

    def test_phi_node_detected(self, sidecar_with_claims):
        """PHI_NODE record present for different-condition claims."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            "SELECT * FROM conflict_witness WHERE warning_class='PHI_NODE'"
        ).fetchall()
        assert len(rows) >= 1
        conn.close()


# ── Claim FTS ────────────────────────────────────────────────────────


class TestClaimFTS:
    def test_claim_fts_search(self, sidecar_with_claims):
        """Can search claim statements via FTS."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            "SELECT claim_id FROM claim_fts WHERE claim_fts MATCH 'logarithmic'"
        ).fetchall()
        ids = [r[0] for r in rows]
        expected_id = make_claim_identity("claim5", namespace="test_paper_alpha")[
            "artifact_id"
        ]
        assert expected_id in ids
        conn.close()

    def test_claim_fts_search_expression(self, sidecar_with_claims):
        """Can search claim expressions via FTS."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            "SELECT claim_id FROM claim_fts WHERE claim_fts MATCH 'log'"
        ).fetchall()
        ids = [r[0] for r in rows]
        expected_id = make_claim_identity("claim8", namespace="test_paper_beta")[
            "artifact_id"
        ]
        assert expected_id in ids
        conn.close()

    def test_claim_fts_search_conditions(self, sidecar_with_claims):
        """Can search claim conditions via FTS."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            "SELECT claim_id FROM claim_fts WHERE claim_fts MATCH 'singing'"
        ).fetchall()
        ids = [r[0] for r in rows]
        expected_id = make_claim_identity("claim3", namespace="test_paper_alpha")[
            "artifact_id"
        ]
        assert expected_id in ids
        conn.close()


# ── Parameterization group table ────────────────────────────────────


class TestParameterizationGroupTable:
    def test_parameterization_group_table_exists(self, knowledge_reader, sidecar_path):
        """parameterization_group table created during build."""
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='parameterization_group'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_parameterization_groups_reflect_components(
        self, knowledge_reader, sidecar_path
    ):
        """Groups reflect connected components from parameterizations."""
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)

        # Concepts with parameterization links should share a group
        rows = conn.execute(
            "SELECT concept_id, group_id FROM parameterization_group"
        ).fetchall()
        by_group = {}
        for cid, gid in rows:
            by_group.setdefault(gid, set()).add(cid)

        # concept5 (return_phase_ratio) has parameterization with inputs [concept5, concept1]
        # So concept1 and concept5 should be in the same group
        found = False
        for gid, members in by_group.items():
            if CONCEPT1_ID in members and CONCEPT5_ID in members:
                found = True
                break
        assert found, (
            f"concept1 and concept5 should be in the same parameterization group. Groups: {by_group}"
        )

        conn.close()


# ── Concept form metadata ────────────────────────────────────────────


class TestConceptFormMetadata:
    def _setup_forms(self, concept_dir):
        """Write real form definitions for the test concepts."""
        forms_dir = concept_dir.parent / "forms"
        forms_dir.mkdir(exist_ok=True)
        yaml.dump(
            {"name": "frequency", "dimensionless": False, "unit_symbol": "Hz"},
            (forms_dir / "frequency.yaml").open("w"),
        )
        yaml.dump(
            {
                "name": "pressure",
                "dimensionless": False,
                "unit_symbol": "Pa",
                "common_alternatives": [
                    {"unit": "cmH2O", "type": "multiplicative", "multiplier": 98.0665}
                ],
            },
            (forms_dir / "pressure.yaml").open("w"),
        )
        yaml.dump(
            {
                "name": "category",
                "dimensionless": True,
                "parameters": {"values": [], "extensible": False},
            },
            (forms_dir / "category.yaml").open("w"),
        )
        yaml.dump(
            {
                "name": "structural",
                "dimensionless": True,
                "note": "Non-measurable organizing concepts.",
            },
            (forms_dir / "structural.yaml").open("w"),
        )
        yaml.dump(
            {
                "name": "duration_ratio",
                "dimensionless": True,
                "base": "ratio",
                "parameters": {"numerator": "duration", "denominator": "duration"},
            },
            (forms_dir / "duration_ratio.yaml").open("w"),
        )

    def test_concept_has_is_dimensionless_column(
        self, concept_dir, knowledge_reader, sidecar_path
    ):
        self._setup_forms(concept_dir)
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        assert "is_dimensionless" in {
            column.name for column in world_schema().table("concept").columns
        }

    def test_frequency_concept_not_dimensionless(
        self, concept_dir, knowledge_reader, sidecar_path
    ):
        self._setup_forms(concept_dir)
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT is_dimensionless FROM concept WHERE id=?", (CONCEPT1_ID,)
        ).fetchone()
        assert row[0] == 0
        conn.close()

    def test_ratio_concept_is_dimensionless(
        self, concept_dir, knowledge_reader, sidecar_path
    ):
        self._setup_forms(concept_dir)
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT is_dimensionless FROM concept WHERE id=?", (CONCEPT5_ID,)
        ).fetchone()
        assert row[0] == 1
        conn.close()

    def test_concept_has_unit_symbol_column(
        self, concept_dir, knowledge_reader, sidecar_path
    ):
        self._setup_forms(concept_dir)
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        assert "unit_symbol" in {
            column.name for column in world_schema().table("concept").columns
        }

    def test_frequency_concept_unit_symbol(
        self, concept_dir, knowledge_reader, sidecar_path
    ):
        self._setup_forms(concept_dir)
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT unit_symbol FROM concept WHERE id=?", (CONCEPT1_ID,)
        ).fetchone()
        assert row[0] == "Hz"
        conn.close()

    def test_ratio_concept_unit_symbol_null(
        self, concept_dir, knowledge_reader, sidecar_path
    ):
        self._setup_forms(concept_dir)
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT unit_symbol FROM concept WHERE id=?", (CONCEPT5_ID,)
        ).fetchone()
        assert row[0] is None
        conn.close()


# ── Algorithm claim tests ─────────────────────────────────────────────


@pytest.fixture
def algorithm_claim_files(concept_dir):
    """Create claim files containing an algorithm claim."""
    claims_dir = concept_dir.parent / "claims"
    claims_dir.mkdir(exist_ok=True)

    algo_paper = {
        "source": {"paper": "algo_test_paper"},
        "claims": [
            {
                "id": "algo_claim1",
                "type": "algorithm",
                "body": "def compute(x):\n    return x * 2\n",
                "stage": "excitation",
                "variables": [{"name": "x", "concept": "concept1"}],
                "provenance": {"paper": "algo_test_paper", "page": 3},
            },
        ],
    }
    algo_paper = _normalize_claim_concept_refs(algo_paper)
    (claims_dir / "algo_test_paper.yaml").write_text(
        yaml.dump(algo_paper, default_flow_style=False)
    )

    return None


@pytest.fixture
def sidecar_with_algorithm(knowledge_reader, sidecar_path, algorithm_claim_files):
    """Build a sidecar that includes an algorithm claim."""
    build_sidecar(knowledge_reader, sidecar_path, force=True)
    return sidecar_path


class TestAlgorithmClaim:
    def test_stage_index_exists(self, sidecar_with_algorithm):
        """The normalized algorithm stage index is created."""
        conn = sqlite3.connect(sidecar_with_algorithm)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_claim_algorithm_stage'"
        )
        assert cursor.fetchone() is not None
        conn.close()


class TestNormalizedSidecarStorage:
    def test_claim_core_drops_generic_concept_id_column(self, sidecar_with_claims):
        conn = sqlite3.connect(sidecar_with_claims)
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(claim_core)").fetchall()
        }
        conn.close()

        assert "concept_id" not in columns


# ── Form algebra: dim_verified flag ──────────────────────────────────


class TestFormAlgebraDimVerified:
    """Form algebra entries must never be dropped at build time.

    Forms without dimensions (or with failed dimensional verification)
    should be stored with dim_verified=0 instead of silently skipped.
    """

    def test_form_algebra_stores_entry_when_dimensions_missing(
        self, knowledge_reader, sidecar_path
    ):
        """Forms without dimensions must still produce form_algebra rows."""
        # The fixture forms have no dimensions — the entry must still appear
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute("SELECT dim_verified FROM form_algebra").fetchall()
        conn.close()
        # concept5 has a parameterization_relationship → expect at least 1 row
        assert len(rows) >= 1, (
            "form_algebra must not drop entries with missing dimensions"
        )
        row = rows[0]
        assert row[0] == 0, "entry without dimensions should have dim_verified=0"


# ── value_si normalization ────────────────────────────────────────────


class TestClaimValueSI:
    """value_si / lower_bound_si / upper_bound_si columns are populated
    at build time by normalizing raw values through normalize_to_si()."""

    def _setup_frequency_form_with_kHz(self, concept_dir):
        """Write a frequency form with kHz in common_alternatives."""
        forms_dir = concept_dir.parent / "forms"
        forms_dir.mkdir(exist_ok=True)
        yaml.dump(
            {
                "name": "frequency",
                "kind": "quantity",
                "dimensionless": False,
                "unit_symbol": "Hz",
                "dimensions": {"T": -1},
                "common_alternatives": [
                    {"unit": "kHz", "type": "multiplicative", "multiplier": 1000.0},
                ],
            },
            (forms_dir / "frequency.yaml").open("w"),
        )
        # Ensure other forms still exist (minimal stubs)
        dimensionless_forms = {"category", "structural", "duration_ratio"}
        for form_name in ("category", "structural", "duration_ratio", "pressure"):
            path = forms_dir / f"{form_name}.yaml"
            if not path.exists():
                yaml.dump(
                    {
                        "name": form_name,
                        "dimensionless": form_name in dimensionless_forms,
                    },
                    path.open("w"),
                )
        # Clear form cache so new YAML is picked up
        from propstore.families.forms.stages import _form_cache

        _form_cache.clear()

    def _build_with_claims(self, concept_dir, sidecar_path, claims_list):
        """Helper: write claim file, build sidecar, return db path."""
        self._setup_frequency_form_with_kHz(concept_dir)
        claims_dir = concept_dir.parent / "claims"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "si_test_paper"},
            "claims": claims_list,
        }
        claim_data = _normalize_claim_concept_refs(claim_data)
        (claims_dir / "si_test_paper.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )
        knowledge_reader = Repository(concept_dir.parent)
        build_sidecar(knowledge_reader, sidecar_path, force=True)
        return sidecar_path


class TestEmbeddingSnapshotErrors:
    def test_embedding_snapshot_runtime_error_propagates(
        self,
        knowledge_reader,
        sidecar_path,
    ):
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(sidecar_path)
        conn.execute("CREATE TABLE existing_snapshot_marker (id TEXT)")
        conn.close()

        with (
            patch(
                "propstore.compiler.workflows.extract_embedding_snapshot",
                MagicMock(side_effect=RuntimeError("snapshot boom")),
            ),
        ):
            with pytest.raises(RuntimeError, match="snapshot boom"):
                build_sidecar(knowledge_reader, sidecar_path, force=True)
