"""Tests for the SQLite sidecar builder.

Verifies that the sidecar builder creates the correct tables,
populates them from concept YAML files, and builds the FTS5 index.
"""

import sqlite3

import pytest
import yaml
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from propstore.build_sidecar import _content_hash, build_sidecar
from propstore.validate import load_concepts
from propstore.validate_contexts import LoadedContext


_CLAIM_SELECT_SQL = """
    SELECT
        core.id,
        core.content_hash,
        core.seq,
        core.type,
        core.concept_id,
        num.value,
        num.lower_bound,
        num.upper_bound,
        num.uncertainty,
        num.uncertainty_type,
        num.sample_size,
        num.unit,
        txt.conditions_cel,
        txt.statement,
        txt.expression,
        txt.sympy_generated,
        txt.sympy_error,
        txt.name,
        core.target_concept,
        txt.measure,
        txt.listener_population,
        txt.methodology,
        txt.notes,
        txt.description,
        txt.auto_summary,
        alg.body,
        alg.canonical_ast,
        alg.variables_json,
        alg.stage,
        core.source_paper,
        core.provenance_page,
        core.provenance_json,
        num.value_si,
        num.lower_bound_si,
        num.upper_bound_si,
        core.context_id
    FROM claim_core AS core
    LEFT JOIN claim_numeric_payload AS num ON num.claim_id = core.id
    LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
    LEFT JOIN claim_algorithm_payload AS alg ON alg.claim_id = core.id
"""


def _fetch_claim(conn: sqlite3.Connection, claim_id: str) -> sqlite3.Row | None:
    conn.row_factory = sqlite3.Row
    return conn.execute(f"{_CLAIM_SELECT_SQL} WHERE core.id = ?", (claim_id,)).fetchone()


def _fetch_claim_rows(
    conn: sqlite3.Connection,
    where_sql: str = "",
    params: tuple[object, ...] = (),
) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(f"{_CLAIM_SELECT_SQL} {where_sql}", params).fetchall()


def _fetch_relation_edge_rows(
    conn: sqlite3.Connection,
    where_sql: str = "",
    params: tuple[object, ...] = (),
) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        """
        SELECT
            source_id AS claim_id,
            target_id AS target_claim_id,
            relation_type AS stance_type,
            target_justification_id,
            strength,
            conditions_differ,
            note,
            resolution_method,
            resolution_model,
            embedding_model,
            embedding_distance,
            pass_number,
            confidence,
            opinion_belief,
            opinion_disbelief,
            opinion_uncertainty,
            opinion_base_rate
        FROM relation_edge
        WHERE source_kind = 'claim' AND target_kind = 'claim'
        """ + (f" {where_sql}" if where_sql else ""),
        params,
    ).fetchall()


@pytest.fixture
def concept_dir(tmp_path):
    """Create a concepts directory with a few test concepts."""
    knowledge = tmp_path / "knowledge"
    concepts_path = knowledge / "concepts"
    concepts_path.mkdir(parents=True)
    counters = concepts_path / ".counters"
    counters.mkdir()
    (counters / "speech.next").write_text("5")
    (counters / "narr.next").write_text("2")

    # Create form definition files
    forms_dir = knowledge / "forms"
    forms_dir.mkdir()
    for form_name in ("frequency", "category", "structural", "duration_ratio", "pressure"):
        (forms_dir / f"{form_name}.yaml").write_text(
            yaml.dump({"name": form_name}, default_flow_style=False))

    def write(name, data):
        (concepts_path / f"{name}.yaml").write_text(yaml.dump(data, default_flow_style=False))

    write("fundamental_frequency", {
        "id": "concept1",
        "canonical_name": "fundamental_frequency",
        "status": "accepted",
        "definition": "The rate of vocal fold vibration during phonation.",
        "domain": "speech",
        "created_date": "2026-03-15",
        "form": "frequency",
        "range": [50, 1000],
        "aliases": [
            {"name": "F0", "source": "common"},
            {"name": "pitch", "source": "common", "note": "perceptual correlate"},
        ],
        "relationships": [
            {"type": "broader", "target": "concept4"},
        ],
    })

    write("subglottal_pressure", {
        "id": "concept2",
        "canonical_name": "subglottal_pressure",
        "status": "accepted",
        "definition": "Air pressure below the glottis during phonation.",
        "domain": "speech",
        "form": "pressure",
        "aliases": [
            {"name": "Ps", "source": "Sundberg_1993"},
        ],
    })

    write("task", {
        "id": "concept3",
        "canonical_name": "task",
        "status": "accepted",
        "definition": "The vocal activity type used in an experiment.",
        "domain": "speech",
        "form": "category",
        "form_parameters": {"values": ["speech", "singing", "whisper"], "extensible": True},
    })

    write("voice_source", {
        "id": "concept4",
        "canonical_name": "voice_source",
        "status": "accepted",
        "definition": "The acoustic signal generated by the vibrating vocal folds.",
        "domain": "speech",
        "form": "structural",
        "relationships": [
            {"type": "narrower", "target": "concept1"},
            {"type": "narrower", "target": "concept2"},
        ],
    })

    write("return_phase_ratio", {
        "id": "concept5",
        "canonical_name": "return_phase_ratio",
        "status": "proposed",
        "definition": "Ratio of return phase time to fundamental period.",
        "domain": "speech",
        "form": "duration_ratio",
        "aliases": [
            {"name": "ra", "source": "Gobl_1988"},
            {"name": "Ra", "source": "Fant_1985", "note": "unnormalized"},
        ],
        "parameterization_relationships": [{
            "formula": "ra = ta / T0",
            "sympy": "Eq(ra, ta / T0)",
            "inputs": ["concept5", "concept1"],
            "exactness": "exact",
            "source": "Fant_1985",
            "bidirectional": True,
            "conditions": ["task == 'speech'"],
        }],
    })

    return concepts_path


@pytest.fixture
def repo(concept_dir):
    """Create a Repository pointing at the knowledge/ directory."""
    from propstore.cli.repository import Repository
    return Repository(concept_dir.parent)


@pytest.fixture
def sidecar_path(tmp_path):
    return tmp_path / "sidecar" / "propstore.sqlite"


# ── Table existence ──────────────────────────────────────────────────

class TestTableCreation:
    def test_creates_sqlite_file(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        assert sidecar_path.exists()

    def test_concept_table_exists(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concept'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_alias_table_exists(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alias'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_relationship_table_exists(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relationship'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_parameterization_table_exists(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parameterization'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_fts_table_exists(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concept_fts'")
        assert cursor.fetchone() is not None
        conn.close()


# ── Concept table contents ───────────────────────────────────────────

class TestConceptTable:
    def test_concept_count(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        count = conn.execute("SELECT COUNT(*) FROM concept").fetchone()[0]
        assert count == 5
        conn.close()

    def test_concept_fields(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM concept WHERE id='concept1'").fetchone()
        assert row["canonical_name"] == "fundamental_frequency"
        assert row["status"] == "accepted"
        assert row["domain"] == "speech"
        assert row["kind_type"] == "quantity"
        assert "vocal fold" in row["definition"]
        conn.close()

    def test_proposed_concept_included(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute("SELECT status FROM concept WHERE id='concept5'").fetchone()
        assert row[0] == "proposed"
        conn.close()

    def test_concept_has_content_hash(self, concept_dir, sidecar_path):
        """Concepts have non-empty content_hash."""
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT content_hash FROM concept WHERE id='concept1'").fetchone()
        assert row["content_hash"] is not None
        assert len(row["content_hash"]) == 16
        conn.close()

    def test_concept_has_seq(self, concept_dir, sidecar_path):
        """Concepts have sequential numbering."""
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        seqs = [r[0] for r in conn.execute("SELECT seq FROM concept ORDER BY seq").fetchall()]
        assert seqs == list(range(1, len(seqs) + 1))
        conn.close()

    def test_content_hash_deterministic(self, concept_dir, sidecar_path):
        """Same content produces same hash across builds."""
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        hash1 = conn.execute("SELECT content_hash FROM concept WHERE id='concept1'").fetchone()[0]
        conn.close()

        build_sidecar(concepts, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        hash2 = conn.execute("SELECT content_hash FROM concept WHERE id='concept1'").fetchone()[0]
        conn.close()
        assert hash1 == hash2


# ── Alias table contents ─────────────────────────────────────────────

class TestAliasTable:
    def test_alias_count(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        count = conn.execute("SELECT COUNT(*) FROM alias").fetchone()[0]
        # F0, pitch, Ps, ra, Ra = 5
        assert count == 5
        conn.close()

    def test_alias_lookup(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT concept_id FROM alias WHERE alias_name='F0'"
        ).fetchone()
        assert row[0] == "concept1"
        conn.close()

    def test_alias_source(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute(
            "SELECT source FROM alias WHERE alias_name='Ps'"
        ).fetchone()
        assert row[0] == "Sundberg_1993"
        conn.close()


# ── Relationship table contents ──────────────────────────────────────

class TestRelationshipTable:
    def test_relationship_count(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        count = conn.execute("SELECT COUNT(*) FROM relationship").fetchone()[0]
        # broader(concept1→concept4), narrower(concept4→concept1),
        # narrower(concept4→concept2) = 3
        assert count == 3
        conn.close()

    def test_relationship_fields(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM relationship WHERE source_id='concept1'"
        ).fetchone()
        assert row["type"] == "broader"
        assert row["target_id"] == "concept4"
        conn.close()


# ── Parameterization table contents ──────────────────────────────────

class TestParameterizationTable:
    def test_parameterization_count(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        count = conn.execute("SELECT COUNT(*) FROM parameterization").fetchone()[0]
        assert count == 1
        conn.close()

    def test_parameterization_fields(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM parameterization").fetchone()
        assert "concept5" in row["concept_ids"]
        assert row["formula"] == "ra = ta / T0"
        assert row["exactness"] == "exact"
        conn.close()

    def test_parameterization_has_output_concept_id(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM parameterization").fetchone()
        assert row["output_concept_id"] == "concept5"
        conn.close()


# ── FTS5 index ───────────────────────────────────────────────────────

class TestFTS:
    def test_fts_search_by_name(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH 'frequency'"
        ).fetchall()
        ids = [r[0] for r in rows]
        assert "concept1" in ids
        conn.close()

    def test_fts_search_by_alias(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH 'pitch'"
        ).fetchall()
        ids = [r[0] for r in rows]
        assert "concept1" in ids
        conn.close()

    def test_fts_search_by_definition(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH 'glottis'"
        ).fetchall()
        ids = [r[0] for r in rows]
        assert "concept2" in ids
        conn.close()

    def test_fts_search_by_condition(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        rows = conn.execute(
            "SELECT concept_id FROM concept_fts WHERE concept_fts MATCH 'speech'"
        ).fetchall()
        ids = [r[0] for r in rows]
        # return_phase_ratio has condition "task == 'speech'"
        assert "concept5" in ids
        conn.close()


# ── Rebuild skipping ─────────────────────────────────────────────────

class TestRebuildSkipping:
    def test_skip_rebuild_when_unchanged(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)

        # Set mtime 2 seconds in the past so any rewrite would be detectable
        import os
        stat = sidecar_path.stat()
        os.utime(sidecar_path, (stat.st_atime, stat.st_mtime - 2))
        mtime1 = sidecar_path.stat().st_mtime

        # Build again — should skip
        build_sidecar(concepts, sidecar_path)
        mtime2 = sidecar_path.stat().st_mtime
        assert mtime1 == mtime2

    def test_rebuild_when_forced(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)

        # Set mtime 2 seconds in the past so forced rebuild produces a newer mtime
        import os
        stat = sidecar_path.stat()
        os.utime(sidecar_path, (stat.st_atime, stat.st_mtime - 2))
        mtime1 = sidecar_path.stat().st_mtime

        build_sidecar(concepts, sidecar_path, force=True)
        mtime2 = sidecar_path.stat().st_mtime
        assert mtime2 > mtime1

    def test_rebuild_when_contexts_change(self, concept_dir, sidecar_path):
        concepts = load_concepts(concept_dir)
        context_v1 = [
            LoadedContext(
                filename="ctx_root",
                filepath=None,
                data={"id": "ctx_root", "name": "Root", "assumptions": ["task == 'speech'"]},
            )
        ]
        context_v2 = [
            LoadedContext(
                filename="ctx_root",
                filepath=None,
                data={"id": "ctx_root", "name": "Root", "assumptions": ["task == 'singing'"]},
            )
        ]

        assert build_sidecar(concepts, sidecar_path, force=True, context_files=context_v1) is True
        assert build_sidecar(concepts, sidecar_path, context_files=context_v2) is True

    def test_rebuild_when_form_files_change(self, concept_dir, sidecar_path, repo):
        concepts = load_concepts(concept_dir)

        assert build_sidecar(concepts, sidecar_path, force=True, repo=repo) is True

        form_path = repo.forms_dir / "frequency.yaml"
        form_data = yaml.safe_load(form_path.read_text())
        form_data["note"] = "changed semantic form contract"
        form_path.write_text(yaml.dump(form_data, default_flow_style=False))

        assert build_sidecar(concepts, sidecar_path, repo=repo) is True

    def test_rebuild_when_stance_files_change(self, concept_dir, sidecar_path, claim_files, repo):
        concepts = load_concepts(concept_dir)
        concept_registry = {c.data["id"]: c.data for c in concepts if c.data.get("id")}

        assert build_sidecar(
            concepts,
            sidecar_path,
            force=True,
            claim_files=claim_files,
            concept_registry=concept_registry,
            repo=repo,
        ) is True

        stance_path = repo.stances_dir / "claim1.yaml"
        repo.stances_dir.mkdir(parents=True, exist_ok=True)
        stance_path.write_text(yaml.dump({
            "source_claim": "claim1",
            "stances": [{"type": "supports", "target": "claim5", "note": "new stance file"}],
        }, default_flow_style=False))

        assert build_sidecar(
            concepts,
            sidecar_path,
            claim_files=claim_files,
            concept_registry=concept_registry,
            repo=repo,
        ) is True

    def test_rebuild_when_semantic_version_changes(self, concept_dir, sidecar_path, monkeypatch):
        import propstore.build_sidecar as build_sidecar_module

        concepts = load_concepts(concept_dir)
        assert build_sidecar(concepts, sidecar_path, force=True) is True

        monkeypatch.setattr(
            build_sidecar_module,
            "_SEMANTIC_INPUT_VERSION",
            "test-version-bump",
            raising=False,
        )

        assert build_sidecar(concepts, sidecar_path) is True

    @given(
        assumption_a=st.sampled_from(["task == 'speech'", "task == 'singing'", "task == 'whisper'"]),
        assumption_b=st.sampled_from(["task == 'speech'", "task == 'singing'", "task == 'whisper'"]),
    )
    @settings(max_examples=12, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_content_hash_changes_when_context_semantics_change(
        self,
        concept_dir,
        assumption_a,
        assumption_b,
    ):
        assume(assumption_a != assumption_b)
        concepts = load_concepts(concept_dir)
        context_a = [
            LoadedContext(
                filename="ctx_root",
                filepath=None,
                data={"id": "ctx_root", "name": "Root", "assumptions": [assumption_a]},
            )
        ]
        context_b = [
            LoadedContext(
                filename="ctx_root",
                filepath=None,
                data={"id": "ctx_root", "name": "Root", "assumptions": [assumption_b]},
            )
        ]
        assert _content_hash(concepts, context_files=context_a) != _content_hash(
            concepts,
            context_files=context_b,
        )


# ── Claim fixtures ───────────────────────────────────────────────────

@pytest.fixture
def claim_files(concept_dir):
    """Create claim files in a claims subdirectory alongside concepts."""
    claims_dir = concept_dir / "claims_data"
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
                "provenance": {"paper": "test_paper_alpha", "page": 8, "table": "Table 2"},
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
                "provenance": {"paper": "test_paper_alpha", "page": 20, "section": "Discussion"},
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
                "provenance": {"paper": "test_paper_beta", "page": 19, "table": "Table 3"},
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

    (claims_dir / "test_paper_alpha.yaml").write_text(yaml.dump(alpha, default_flow_style=False))
    (claims_dir / "test_paper_beta.yaml").write_text(yaml.dump(beta, default_flow_style=False))

    from propstore.validate_claims import load_claim_files
    return load_claim_files(claims_dir)


@pytest.fixture
def sidecar_with_claims(concept_dir, sidecar_path, claim_files):
    """Build a sidecar that includes claim and conflict tables."""
    concepts = load_concepts(concept_dir)
    concept_registry = {c.data["id"]: c.data for c in concepts if c.data.get("id")}
    build_sidecar(concepts, sidecar_path, claim_files=claim_files, concept_registry=concept_registry)
    return sidecar_path


# ── Claim table ──────────────────────────────────────────────────────

class TestClaimTable:
    def test_claim_table_exists(self, sidecar_with_claims):
        """Normalized claim tables are created when claim_files are provided."""
        conn = sqlite3.connect(sidecar_with_claims)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='claim_core'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_claim_count(self, sidecar_with_claims):
        """Correct number of claims in normalized storage."""
        conn = sqlite3.connect(sidecar_with_claims)
        count = conn.execute("SELECT COUNT(*) FROM claim_core").fetchone()[0]
        # 5 from alpha + 4 from beta = 9
        assert count == 9
        conn.close()

    def test_claim_fields(self, sidecar_with_claims):
        """Claim fields populated correctly."""
        conn = sqlite3.connect(sidecar_with_claims)
        row = _fetch_claim(conn, "claim1")
        assert row["type"] == "parameter"
        assert row["concept_id"] == "concept1"
        assert row["unit"] == "Hz"
        assert row["source_paper"] == "test_paper_alpha"
        assert row["provenance_page"] == 5
        conn.close()

    def test_claim_has_content_hash(self, sidecar_with_claims):
        """Claims have non-empty content_hash."""
        conn = sqlite3.connect(sidecar_with_claims)
        row = _fetch_claim(conn, "claim1")
        assert row["content_hash"] is not None
        assert len(row["content_hash"]) == 16
        conn.close()

    def test_claim_has_seq(self, sidecar_with_claims):
        """Claims have sequential numbering."""
        conn = sqlite3.connect(sidecar_with_claims)
        seqs = [r["seq"] for r in _fetch_claim_rows(conn, "ORDER BY core.seq")]
        assert seqs == list(range(1, len(seqs) + 1))
        conn.close()

    def test_claim_has_auto_summary(self, sidecar_with_claims):
        """Parameter claims get auto_summary from description_generator."""
        conn = sqlite3.connect(sidecar_with_claims)
        row = _fetch_claim(conn, "claim1")
        assert row["auto_summary"] is not None
        assert "fundamental_frequency" in row["auto_summary"]
        conn.close()

    def test_claim_description_from_yaml(self, sidecar_with_claims):
        """description column is None when not in YAML (LLM-written field)."""
        conn = sqlite3.connect(sidecar_with_claims)
        row = _fetch_claim(conn, "claim1")
        assert row["description"] is None
        conn.close()

    def test_parameter_claim_has_concept(self, sidecar_with_claims):
        """Parameter claim has concept_id populated."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = _fetch_claim_rows(conn, "WHERE core.type='parameter'")
        for row in rows:
            assert row["concept_id"] is not None, f"claim {row['id']} missing concept_id"
        conn.close()

    def test_observation_claim_has_statement(self, sidecar_with_claims):
        """Observation claim has statement populated."""
        conn = sqlite3.connect(sidecar_with_claims)
        row = _fetch_claim(conn, "claim5")
        assert row["type"] == "observation"
        assert "logarithmic" in row["statement"]
        conn.close()

    def test_equation_claim_has_expression(self, sidecar_with_claims):
        """Equation claim has expression populated."""
        conn = sqlite3.connect(sidecar_with_claims)
        row = _fetch_claim(conn, "claim8")
        assert row["type"] == "equation"
        assert "log(Ps)" in row["expression"]
        conn.close()

    def test_equation_claim_preserves_sympy_error(self, concept_dir, sidecar_path, repo):
        """Equation claims preserve the auto-generation error when sympy cannot be derived."""
        claims_dir = concept_dir / "claims_equation_error"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "equation_error_paper"},
            "claims": [
                {
                    "id": "claim1",
                    "type": "equation",
                    "expression": "F0 is roughly proportional to Ps",
                    "variables": [
                        {"symbol": "F0", "concept": "concept1"},
                        {"symbol": "Ps", "concept": "concept2"},
                    ],
                    "provenance": {"paper": "equation_error_paper", "page": 1},
                },
            ],
        }
        (claims_dir / "equation_error_paper.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        from propstore.validate_claims import build_concept_registry, load_claim_files

        claim_files = load_claim_files(claims_dir)
        concepts = load_concepts(concept_dir)
        concept_registry = build_concept_registry(repo)
        build_sidecar(
            concepts,
            sidecar_path,
            force=True,
            claim_files=claim_files,
            concept_registry=concept_registry,
        )

        conn = sqlite3.connect(sidecar_path)
        row = _fetch_claim(conn, "claim1")
        assert row["sympy_generated"] is None
        assert row["sympy_error"] is not None
        conn.close()

    def test_legacy_list_value_raises(self, concept_dir, sidecar_path, repo):
        """Legacy list value format raises TypeError — no silent conversion."""
        claims_dir = concept_dir / "claims_range"
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
        (claims_dir / "range_paper.yaml").write_text(yaml.dump(claim_data, default_flow_style=False))

        from propstore.validate_claims import load_claim_files, build_concept_registry

        claim_files = load_claim_files(claims_dir)
        concepts = load_concepts(concept_dir)
        concept_registry = build_concept_registry(repo)
        with pytest.raises(TypeError):
            build_sidecar(concepts, sidecar_path, force=True,
                          claim_files=claim_files, concept_registry=concept_registry)

    def test_proper_bounds_without_value(self, concept_dir, sidecar_path, repo):
        """Proper bounds format (lower_bound + upper_bound, no value) stores correctly."""
        claims_dir = concept_dir / "claims_bounds"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "bounds_paper"},
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "lower_bound": 100.0,
                    "upper_bound": 300.0,
                    "unit": "Hz",
                    "provenance": {"paper": "bounds_paper", "page": 1},
                },
            ],
        }
        (claims_dir / "bounds_paper.yaml").write_text(yaml.dump(claim_data, default_flow_style=False))

        from propstore.validate_claims import load_claim_files, build_concept_registry

        claim_files = load_claim_files(claims_dir)
        concepts = load_concepts(concept_dir)
        concept_registry = build_concept_registry(repo)
        build_sidecar(concepts, sidecar_path, force=True,
                      claim_files=claim_files, concept_registry=concept_registry)

        conn = sqlite3.connect(sidecar_path)
        row = _fetch_claim(conn, "claim1")
        assert row["value"] is None
        assert row["lower_bound"] == 100.0
        assert row["upper_bound"] == 300.0
        conn.close()

    def test_no_claim_table_without_claims(self, concept_dir, sidecar_path):
        """Normalized claim tables are not created when claim_files is None."""
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='claim_core'")
        assert cursor.fetchone() is None
        conn.close()


# ── Conflicts table ──────────────────────────────────────────────────

class TestConflictsTable:
    def test_conflicts_table_exists(self, sidecar_with_claims):
        """conflict_witness table created when claim_files provided."""
        conn = sqlite3.connect(sidecar_with_claims)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conflict_witness'")
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
        row = _fetch_relation_edge_rows(conn, "AND source_id='claim2'")[0]
        assert row["claim_id"] == "claim2"
        assert row["target_claim_id"] == "claim1"
        assert row["stance_type"] == "rebuts"
        assert row["strength"] == "strong"
        assert "conflicting value" in row["note"]
        conn.close()

    def test_invalid_inline_stance_target_raises(self, concept_dir, sidecar_path, repo):
        claims_dir = concept_dir / "claims_invalid_stance_target"
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
        (claims_dir / "invalid_stance_target.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        from propstore.validate_claims import build_concept_registry, load_claim_files

        claim_files = load_claim_files(claims_dir)
        concepts = load_concepts(concept_dir)
        concept_registry = build_concept_registry(repo)
        with pytest.raises(sqlite3.IntegrityError):
            build_sidecar(
                concepts,
                sidecar_path,
                force=True,
                claim_files=claim_files,
                concept_registry=concept_registry,
            )

    def test_invalid_inline_stance_type_raises(self, concept_dir, sidecar_path, repo):
        claims_dir = concept_dir / "claims_invalid_stance_type"
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
        (claims_dir / "invalid_stance_type.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        from propstore.validate_claims import build_concept_registry, load_claim_files

        claim_files = load_claim_files(claims_dir)
        concepts = load_concepts(concept_dir)
        concept_registry = build_concept_registry(repo)
        with pytest.raises(ValueError, match="contradicts"):
            build_sidecar(
                concepts,
                sidecar_path,
                force=True,
                claim_files=claim_files,
                concept_registry=concept_registry,
            )

    def test_invalid_inline_stance_resolution_shape_raises_cleanly(
        self,
        concept_dir,
        sidecar_path,
        repo,
    ):
        claims_dir = concept_dir / "claims_invalid_stance_resolution"
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
                    "stances": [{
                        "type": "supports",
                        "target": "claim1",
                        "resolution": ["nli_first_pass"],
                    }],
                    "provenance": {"paper": "invalid_stance_resolution", "page": 2},
                },
            ],
        }
        (claims_dir / "invalid_stance_resolution.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        from propstore.validate_claims import build_concept_registry, load_claim_files

        claim_files = load_claim_files(claims_dir)
        concepts = load_concepts(concept_dir)
        concept_registry = build_concept_registry(repo)
        with pytest.raises(ValueError, match="resolution"):
            build_sidecar(
                concepts,
                sidecar_path,
                force=True,
                claim_files=claim_files,
                concept_registry=concept_registry,
            )

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
        max_examples=12,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_persisted_stance_edges_reference_extant_claim_ids(
        self,
        concept_dir,
        sidecar_path,
        repo,
        stance_pairs,
    ):
        claims_dir = concept_dir / "claims_property_stances"
        claims_dir.mkdir(exist_ok=True)
        claims = []
        for claim_id, value in (("claim1", 100.0), ("claim2", 120.0), ("claim3", 140.0)):
            claims.append({
                "id": claim_id,
                "type": "parameter",
                "concept": "concept1",
                "value": value,
                "unit": "Hz",
                "provenance": {"paper": "stance_property", "page": 1},
            })
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
        (claims_dir / "stance_property.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )

        from propstore.validate_claims import build_concept_registry, load_claim_files

        claim_files = load_claim_files(claims_dir)
        concepts = load_concepts(concept_dir)
        concept_registry = build_concept_registry(repo)
        build_sidecar(
            concepts,
            sidecar_path,
            force=True,
            claim_files=claim_files,
            concept_registry=concept_registry,
        )

        conn = sqlite3.connect(sidecar_path)
        try:
            claim_ids = {row[0] for row in conn.execute("SELECT id FROM claim_core").fetchall()}
            stance_rows = conn.execute(
                """
                SELECT source_id, target_id
                FROM relation_edge
                WHERE source_kind='claim' AND target_kind='claim'
                """
            ).fetchall()
            assert all(source in claim_ids and target in claim_ids for source, target in stance_rows)
        finally:
            conn.close()

    def test_conflict_query_by_class(self, sidecar_with_claims):
        """Can query normalized conflict witness rows by warning class."""
        conn = sqlite3.connect(sidecar_with_claims)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM conflict_witness WHERE warning_class = 'CONFLICT'"
        ).fetchall()
        for row in rows:
            assert row["warning_class"] == "CONFLICT"
        assert len(rows) >= 1
        conn.close()

    def test_conflict_query_by_concept(self, sidecar_with_claims):
        """Can query normalized conflict witness rows by concept."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            "SELECT * FROM conflict_witness WHERE concept_id = 'concept1'"
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
        assert "claim5" in ids
        conn.close()

    def test_claim_fts_search_expression(self, sidecar_with_claims):
        """Can search claim expressions via FTS."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            "SELECT claim_id FROM claim_fts WHERE claim_fts MATCH 'log'"
        ).fetchall()
        ids = [r[0] for r in rows]
        assert "claim8" in ids
        conn.close()

    def test_claim_fts_search_conditions(self, sidecar_with_claims):
        """Can search claim conditions via FTS."""
        conn = sqlite3.connect(sidecar_with_claims)
        rows = conn.execute(
            "SELECT claim_id FROM claim_fts WHERE claim_fts MATCH 'singing'"
        ).fetchall()
        ids = [r[0] for r in rows]
        assert "claim3" in ids
        conn.close()


# ── Parameterization group table ────────────────────────────────────

class TestParameterizationGroupTable:
    def test_parameterization_group_table_exists(self, concept_dir, sidecar_path):
        """parameterization_group table created during build."""
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='parameterization_group'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_parameterization_groups_reflect_components(self, concept_dir, sidecar_path):
        """Groups reflect connected components from parameterizations."""
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True)
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
            if "concept1" in members and "concept5" in members:
                found = True
                break
        assert found, f"concept1 and concept5 should be in the same parameterization group. Groups: {by_group}"

        conn.close()


# ── Concept form metadata ────────────────────────────────────────────

class TestConceptFormMetadata:
    def _setup_forms(self, concept_dir):
        """Write real form definitions for the test concepts."""
        forms_dir = concept_dir.parent / "forms"
        forms_dir.mkdir(exist_ok=True)
        yaml.dump({"name": "frequency", "unit_symbol": "Hz"},
                  (forms_dir / "frequency.yaml").open("w"))
        yaml.dump({"name": "pressure", "unit_symbol": "Pa",
                   "common_alternatives": [{"unit": "cmH2O", "type": "multiplicative", "multiplier": 98.0665}]},
                  (forms_dir / "pressure.yaml").open("w"))
        yaml.dump({"name": "category", "parameters": {"values": [], "extensible": False}},
                  (forms_dir / "category.yaml").open("w"))
        yaml.dump({"name": "structural", "note": "Non-measurable organizing concepts."},
                  (forms_dir / "structural.yaml").open("w"))
        yaml.dump({"name": "duration_ratio", "base": "ratio",
                   "parameters": {"numerator": "duration", "denominator": "duration"}},
                  (forms_dir / "duration_ratio.yaml").open("w"))

    def test_concept_has_is_dimensionless_column(self, concept_dir, sidecar_path):
        self._setup_forms(concept_dir)
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM concept WHERE id='concept1'").fetchone()
        assert "is_dimensionless" in row.keys()
        conn.close()

    def test_frequency_concept_not_dimensionless(self, concept_dir, sidecar_path):
        self._setup_forms(concept_dir)
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute("SELECT is_dimensionless FROM concept WHERE id='concept1'").fetchone()
        assert row[0] == 0
        conn.close()

    def test_ratio_concept_is_dimensionless(self, concept_dir, sidecar_path):
        self._setup_forms(concept_dir)
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute("SELECT is_dimensionless FROM concept WHERE id='concept5'").fetchone()
        assert row[0] == 1
        conn.close()

    def test_concept_has_unit_symbol_column(self, concept_dir, sidecar_path):
        self._setup_forms(concept_dir)
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM concept WHERE id='concept1'").fetchone()
        assert "unit_symbol" in row.keys()
        conn.close()

    def test_frequency_concept_unit_symbol(self, concept_dir, sidecar_path):
        self._setup_forms(concept_dir)
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute("SELECT unit_symbol FROM concept WHERE id='concept1'").fetchone()
        assert row[0] == "Hz"
        conn.close()

    def test_ratio_concept_unit_symbol_null(self, concept_dir, sidecar_path):
        self._setup_forms(concept_dir)
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True)
        conn = sqlite3.connect(sidecar_path)
        row = conn.execute("SELECT unit_symbol FROM concept WHERE id='concept5'").fetchone()
        assert row[0] is None
        conn.close()


# ── Algorithm claim tests ─────────────────────────────────────────────

@pytest.fixture
def algorithm_claim_files(concept_dir):
    """Create claim files containing an algorithm claim."""
    claims_dir = concept_dir / "claims_algo"
    claims_dir.mkdir(exist_ok=True)

    algo_paper = {
        "source": {"paper": "algo_test_paper"},
        "claims": [
            {
                "id": "algo_claim1",
                "type": "algorithm",
                "body": "def compute(x):\n    return x * 2\n",
                "stage": "excitation",
                "variables": {"x": "input_signal"},
                "provenance": {"paper": "algo_test_paper", "page": 3},
            },
        ],
    }
    (claims_dir / "algo_test_paper.yaml").write_text(
        yaml.dump(algo_paper, default_flow_style=False)
    )

    from propstore.validate_claims import load_claim_files
    return load_claim_files(claims_dir)


@pytest.fixture
def sidecar_with_algorithm(concept_dir, sidecar_path, algorithm_claim_files):
    """Build a sidecar that includes an algorithm claim."""
    concepts = load_concepts(concept_dir)
    concept_registry = {c.data["id"]: c.data for c in concepts if c.data.get("id")}
    build_sidecar(
        concepts, sidecar_path, force=True,
        claim_files=algorithm_claim_files,
        concept_registry=concept_registry,
    )
    return sidecar_path


class TestAlgorithmClaim:
    def test_algorithm_claim_stored(self, sidecar_with_algorithm):
        """Algorithm claim appears in sidecar with body, canonical_ast, stage."""
        conn = sqlite3.connect(sidecar_with_algorithm)
        row = _fetch_claim(conn, "algo_claim1")
        assert row is not None
        assert row["type"] == "algorithm"
        assert row["body"] is not None
        assert "return x * 2" in row["body"]
        assert row["canonical_ast"] is not None
        assert row["stage"] == "excitation"
        conn.close()

    def test_algorithm_canonical_ast_populated(self, sidecar_with_algorithm):
        """canonical_ast is non-empty for valid algorithm claims."""
        conn = sqlite3.connect(sidecar_with_algorithm)
        row = _fetch_claim(conn, "algo_claim1")
        assert row["canonical_ast"] is not None
        assert len(row["canonical_ast"]) > 0
        conn.close()

    def test_stage_index_exists(self, sidecar_with_algorithm):
        """The normalized algorithm stage index is created."""
        conn = sqlite3.connect(sidecar_with_algorithm)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_claim_algorithm_stage'"
        )
        assert cursor.fetchone() is not None
        conn.close()


class TestAlgorithmBindings:
    """Regression: algorithm claims with list-of-dict variables must produce
    canonical AST that includes the concept bindings (not empty bindings)."""

    def test_algorithm_canonical_ast_includes_bindings(
        self, concept_dir, sidecar_path,
    ):
        """When variables is a list of dicts (per schema), canonical_ast must
        contain the concept names from the bindings, not the raw variable names."""
        claims_dir = concept_dir / "claims_algo_bindings"
        claims_dir.mkdir(exist_ok=True)

        algo_paper = {
            "source": {"paper": "algo_bindings_paper"},
            "claims": [
                {
                    "id": "algo_bind_claim1",
                    "type": "algorithm",
                    "body": "def compute(x):\n    return x * 2\n",
                    "stage": "excitation",
                    "variables": [
                        {"name": "x", "concept": "concept1"},
                    ],
                    "provenance": {"paper": "algo_bindings_paper", "page": 1},
                },
            ],
        }
        (claims_dir / "algo_bindings_paper.yaml").write_text(
            yaml.dump(algo_paper, default_flow_style=False)
        )

        from propstore.validate_claims import load_claim_files
        claim_files = load_claim_files(claims_dir)

        concepts = load_concepts(concept_dir)
        concept_registry = {c.data["id"]: c.data for c in concepts if c.data.get("id")}
        build_sidecar(
            concepts, sidecar_path, force=True,
            claim_files=claim_files,
            concept_registry=concept_registry,
        )

        conn = sqlite3.connect(sidecar_path)
        row = _fetch_claim(conn, "algo_bind_claim1")
        conn.close()

        assert row is not None, "algorithm claim must be stored"
        ast_text = row["canonical_ast"]
        assert ast_text is not None, "canonical_ast must not be None"
        # With correct bindings, 'x' should be replaced by 'concept1'
        assert "concept1" in ast_text, (
            f"canonical_ast should contain concept binding 'concept1' "
            f"but got: {ast_text}"
        )


class TestClaimInsertRow:
    def test_prepare_claim_insert_row_returns_dict(self):
        """_prepare_claim_insert_row should return a dict with named columns."""
        from propstore.build_sidecar import _prepare_claim_insert_row

        claim = {
            "id": "test_claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": "42",
            "unit": "Hz",
            "provenance": {"paper": "test.yaml", "page": 1},
        }
        row = _prepare_claim_insert_row(
            claim, "test_paper.yaml", claim_seq=1, concept_registry={}
        )
        assert isinstance(row, dict), f"Expected dict, got {type(row).__name__}"

    def test_prepare_claim_insert_row_has_all_columns(self):
        """The returned dict should have entries for every claim table column."""
        from propstore.build_sidecar import _prepare_claim_insert_row

        claim = {
            "id": "test_claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": "42",
            "unit": "Hz",
            "provenance": {"paper": "test.yaml", "page": 1},
        }
        row = _prepare_claim_insert_row(
            claim, "test_paper.yaml", claim_seq=1, concept_registry={}
        )
        assert "id" in row
        assert "concept_id" in row
        assert "type" in row
        assert "source_paper" in row
        assert "context_id" in row


class TestNormalizedSidecarStorage:
    def test_normalized_tables_exist(self, sidecar_with_claims):
        conn = sqlite3.connect(sidecar_with_claims)
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()

        assert "claim_core" in names
        assert "claim_numeric_payload" in names
        assert "claim_text_payload" in names
        assert "claim_algorithm_payload" in names
        assert "relation_edge" in names
        assert "conflict_witness" in names
        assert "justification" in names

    def test_normalized_storage_is_deterministic_across_rebuilds(
        self,
        concept_dir,
        sidecar_path,
        claim_files,
    ):
        concepts = load_concepts(concept_dir)
        concept_registry = {c.data["id"]: c.data for c in concepts if c.data.get("id")}

        build_sidecar(
            concepts,
            sidecar_path,
            force=True,
            claim_files=claim_files,
            concept_registry=concept_registry,
        )

        def snapshot_tables() -> dict[str, list[tuple]]:
            conn = sqlite3.connect(sidecar_path)
            tables = {
                "claim_core": conn.execute(
                    "SELECT * FROM claim_core ORDER BY id"
                ).fetchall(),
                "claim_numeric_payload": conn.execute(
                    "SELECT * FROM claim_numeric_payload ORDER BY claim_id"
                ).fetchall(),
                "claim_text_payload": conn.execute(
                    "SELECT * FROM claim_text_payload ORDER BY claim_id"
                ).fetchall(),
                "claim_algorithm_payload": conn.execute(
                    "SELECT * FROM claim_algorithm_payload ORDER BY claim_id"
                ).fetchall(),
                "relation_edge": conn.execute(
                    "SELECT * FROM relation_edge ORDER BY source_kind, source_id, relation_type, target_kind, target_id"
                ).fetchall(),
                "conflict_witness": conn.execute(
                    "SELECT * FROM conflict_witness ORDER BY concept_id, claim_a_id, claim_b_id, warning_class"
                ).fetchall(),
                "justification": conn.execute(
                    "SELECT * FROM justification ORDER BY id"
                ).fetchall(),
            }
            conn.close()
            return tables

        first = snapshot_tables()
        build_sidecar(
            concepts,
            sidecar_path,
            force=True,
            claim_files=claim_files,
            concept_registry=concept_registry,
        )
        second = snapshot_tables()

        assert second == first


# ── Unsafe float() coercion (F12.1) ──────────────────────────────────

class TestExtractNumericClaimFieldsFloatSafety:
    """Verify _extract_numeric_claim_fields handles non-numeric values gracefully.

    Finding F12.1 (audit-error-handling.md): float(raw_value) on a non-numeric
    string like "N/A" raises ValueError, crashing the entire sidecar build.
    The function should handle this gracefully (return None for the value,
    or log a warning) instead of propagating the exception.
    """

    def test_non_numeric_value_does_not_crash(self):
        """A claim with value='N/A' must not raise ValueError.

        Current code: float('N/A') raises ValueError.
        Expected: graceful handling — return None for the value field.
        """
        from propstore.build_sidecar import _extract_numeric_claim_fields

        claim = {"value": "N/A", "unit": "Hz"}
        # This should NOT raise — non-numeric values should be handled gracefully
        result = _extract_numeric_claim_fields(claim)
        assert result["value"] is None, (
            "Non-numeric claim value 'N/A' should produce value=None, "
            "not crash with ValueError"
        )

    def test_non_numeric_value_in_prepare_row_does_not_crash(self):
        """End-to-end: _prepare_claim_insert_row with value='N/A' must not crash."""
        from propstore.build_sidecar import _prepare_claim_insert_row

        claim = {
            "id": "crash_claim",
            "type": "parameter",
            "concept": "concept1",
            "value": "N/A",
            "unit": "Hz",
            "provenance": {"paper": "test.yaml", "page": 1},
        }
        # This should NOT raise ValueError from float("N/A")
        row = _prepare_claim_insert_row(
            claim, "test_paper.yaml", claim_seq=1, concept_registry={}
        )
        assert isinstance(row, dict)
        assert row.get("value") is None, (
            "Non-numeric value 'N/A' should result in value=None in the row"
        )

    def test_empty_string_value_does_not_crash(self):
        """A claim with value='' (empty string) must not crash."""
        from propstore.build_sidecar import _extract_numeric_claim_fields

        claim = {"value": "", "unit": "Hz"}
        result = _extract_numeric_claim_fields(claim)
        assert result["value"] is None, (
            "Empty string claim value should produce value=None"
        )

    def test_numeric_string_still_works(self):
        """A claim with a valid numeric string must still convert correctly."""
        from propstore.build_sidecar import _extract_numeric_claim_fields

        claim = {"value": "42.5", "unit": "Hz"}
        result = _extract_numeric_claim_fields(claim)
        assert result["value"] == 42.5


# ── Form algebra: dim_verified flag ──────────────────────────────────

class TestFormAlgebraDimVerified:
    """Form algebra entries must never be dropped at build time.

    Forms without dimensions (or with failed dimensional verification)
    should be stored with dim_verified=0 instead of silently skipped.
    """

    def test_form_algebra_stores_entry_when_dimensions_missing(
        self, concept_dir, sidecar_path, repo
    ):
        """Forms without dimensions must still produce form_algebra rows."""
        # The fixture forms have no dimensions — the entry must still appear
        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True, repo=repo)
        conn = sqlite3.connect(sidecar_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM form_algebra").fetchall()
        conn.close()
        # concept5 has a parameterization_relationship → expect at least 1 row
        assert len(rows) >= 1, "form_algebra must not drop entries with missing dimensions"
        row = rows[0]
        assert row["dim_verified"] == 0, "entry without dimensions should have dim_verified=0"

    def test_form_algebra_dim_verified_true_when_dimensions_present(
        self, concept_dir, sidecar_path, repo
    ):
        """Forms WITH valid dimensions and no sympy to verify → dim_verified=1."""
        # Add dimensions to the form files
        forms_dir = concept_dir.parent / "forms"
        (forms_dir / "duration_ratio.yaml").write_text(yaml.dump({
            "name": "duration_ratio",
            "dimensions": {"T": 0},
            "dimensionless": True,
        }, default_flow_style=False))
        (forms_dir / "frequency.yaml").write_text(yaml.dump({
            "name": "frequency",
            "dimensions": {"T": -1},
        }, default_flow_style=False))

        # Add a concept with a parameterization that has NO sympy field,
        # so dimensional verification succeeds purely on dimension presence
        concepts_path = concept_dir
        (concepts_path / "period.yaml").write_text(yaml.dump({
            "id": "concept6",
            "canonical_name": "period",
            "status": "accepted",
            "definition": "Duration of one cycle.",
            "domain": "speech",
            "form": "duration_ratio",
            "parameterization_relationships": [{
                "formula": "T0 = 1/f0",
                "inputs": ["concept1"],
                "exactness": "exact",
                "source": "definition",
            }],
        }, default_flow_style=False))

        concepts = load_concepts(concept_dir)
        build_sidecar(concepts, sidecar_path, force=True, repo=repo)
        conn = sqlite3.connect(sidecar_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM form_algebra WHERE output_form='duration_ratio' "
            "AND source_concept_id='concept6'"
        ).fetchall()
        conn.close()
        assert len(rows) >= 1, "form_algebra must contain entries for dimensioned forms"
        row = rows[0]
        assert row["dim_verified"] == 1, "entry with valid dimensions should have dim_verified=1"


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
                "unit_symbol": "Hz",
                "dimensions": {"T": -1},
                "common_alternatives": [
                    {"unit": "kHz", "type": "multiplicative", "multiplier": 1000.0},
                ],
            },
            (forms_dir / "frequency.yaml").open("w"),
        )
        # Ensure other forms still exist (minimal stubs)
        for form_name in ("category", "structural", "duration_ratio", "pressure"):
            path = forms_dir / f"{form_name}.yaml"
            if not path.exists():
                yaml.dump({"name": form_name}, path.open("w"))
        # Clear form cache so new YAML is picked up
        from propstore.form_utils import _form_cache
        _form_cache.clear()

    def _build_with_claims(self, concept_dir, sidecar_path, claims_list):
        """Helper: write claim file, build sidecar, return db path."""
        self._setup_frequency_form_with_kHz(concept_dir)
        claims_dir = concept_dir / "claims_si_test"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "si_test_paper"},
            "claims": claims_list,
        }
        (claims_dir / "si_test_paper.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False)
        )
        from propstore.validate_claims import load_claim_files
        claim_files = load_claim_files(claims_dir)
        concepts = load_concepts(concept_dir)
        concept_registry = {c.data["id"]: c.data for c in concepts if c.data.get("id")}
        build_sidecar(
            concepts, sidecar_path, force=True,
            claim_files=claim_files,
            concept_registry=concept_registry,
        )
        return sidecar_path

    def test_claim_value_si_normalized(self, concept_dir, sidecar_path):
        """0.2 kHz -> value_si = 200.0 Hz."""
        db = self._build_with_claims(concept_dir, sidecar_path, [
            {
                "id": "si_claim1",
                "type": "parameter",
                "concept": "concept1",  # fundamental_frequency, form=frequency
                "value": 0.2,
                "unit": "kHz",
                "provenance": {"paper": "si_test_paper", "page": 1},
            },
        ])
        conn = sqlite3.connect(db)
        row = _fetch_claim(conn, "si_claim1")
        conn.close()
        assert row["value"] == 0.2, "raw value preserved"
        assert row["unit"] == "kHz", "raw unit preserved"
        assert row["value_si"] == pytest.approx(200.0), "value_si = 0.2 * 1000"

    def test_claim_value_si_canonical_unit(self, concept_dir, sidecar_path):
        """Claim with canonical unit Hz -> value_si = same as value."""
        db = self._build_with_claims(concept_dir, sidecar_path, [
            {
                "id": "si_claim2",
                "type": "parameter",
                "concept": "concept1",
                "value": 440.0,
                "unit": "Hz",
                "provenance": {"paper": "si_test_paper", "page": 2},
            },
        ])
        conn = sqlite3.connect(db)
        row = _fetch_claim(conn, "si_claim2")
        conn.close()
        assert row["value_si"] == pytest.approx(440.0), "canonical unit -> value_si == value"

    def test_claim_value_si_no_unit(self, concept_dir, sidecar_path):
        """Claim with no unit field -> value_si = same as value."""
        db = self._build_with_claims(concept_dir, sidecar_path, [
            {
                "id": "si_claim3",
                "type": "parameter",
                "concept": "concept1",
                "value": 100.0,
                "provenance": {"paper": "si_test_paper", "page": 3},
            },
        ])
        conn = sqlite3.connect(db)
        row = _fetch_claim(conn, "si_claim3")
        conn.close()
        assert row["value_si"] == pytest.approx(100.0), "no unit -> value_si == value"

    def test_claim_bounds_si_normalized(self, concept_dir, sidecar_path):
        """lower_bound=0.1, upper_bound=0.3, unit=kHz -> _si = 100.0, 300.0."""
        db = self._build_with_claims(concept_dir, sidecar_path, [
            {
                "id": "si_claim4",
                "type": "parameter",
                "concept": "concept1",
                "lower_bound": 0.1,
                "upper_bound": 0.3,
                "unit": "kHz",
                "provenance": {"paper": "si_test_paper", "page": 4},
            },
        ])
        conn = sqlite3.connect(db)
        row = _fetch_claim(conn, "si_claim4")
        conn.close()
        assert row["lower_bound"] == 0.1, "raw lower_bound preserved"
        assert row["upper_bound"] == 0.3, "raw upper_bound preserved"
        assert row["lower_bound_si"] == pytest.approx(100.0), "lower_bound_si = 0.1 * 1000"
        assert row["upper_bound_si"] == pytest.approx(300.0), "upper_bound_si = 0.3 * 1000"
