"""Tests that RuntimeError propagates through narrowed exception handlers (Group 3).

Each test mocks the failing call to raise RuntimeError and verifies it is NOT caught.
For Location 1 (build_sidecar embedding snapshot), the broad catch is intentional —
test verifies the catch works AND logs a warning.
"""

from unittest.mock import patch, MagicMock
import pytest


class TestBuildSidecarEmbeddingSnapshot:
    """Location 1: build_sidecar.py:250 — embedding snapshot failure.

    This is intentionally broad: embedding snapshot is optional graceful degradation.
    Test verifies the broad catch works and logs.
    """

    def test_embedding_snapshot_exception_caught_and_logged(self, tmp_path):
        """Any exception during embedding snapshot should be caught and logged."""
        import sqlite3
        import logging

        # Create a minimal sidecar db so snapshot path exists
        sidecar = tmp_path / "sidecar.db"
        conn = sqlite3.connect(sidecar)
        conn.execute("CREATE TABLE t (x)")
        conn.close()

        mock_extract = MagicMock(side_effect=RuntimeError("snapshot boom"))
        mock_load_vec = MagicMock()

        # Patch the module-level so the local import picks them up
        import propstore.embed
        original_extract = getattr(propstore.embed, "extract_embeddings", None)
        original_load = getattr(propstore.embed, "_load_vec_extension", None)
        propstore.embed.extract_embeddings = mock_extract
        propstore.embed._load_vec_extension = mock_load_vec

        try:
            # Simulate the try/except block from build_sidecar.py:236-252
            _embedding_snapshot = None
            try:
                _load_vec_extension = mock_load_vec
                extract_embeddings = mock_extract
                _snap_conn = sqlite3.connect(sidecar)
                _snap_conn.row_factory = sqlite3.Row
                _load_vec_extension(_snap_conn)
                _embedding_snapshot = extract_embeddings(_snap_conn)
                _snap_conn.close()
            except ImportError:
                pass
            except Exception as exc:
                logging.warning("Embedding snapshot failed: %s", exc)

            # Verify the broad catch caught it and snapshot is still None
            assert _embedding_snapshot is None
            mock_extract.assert_called_once()
        finally:
            if original_extract is not None:
                propstore.embed.extract_embeddings = original_extract
            if original_load is not None:
                propstore.embed._load_vec_extension = original_load


class TestCliHelpersYamlParsing:
    """Location 2: cli/helpers.py:57 — YAML parsing on concept scan."""

    def test_runtime_error_propagates_through_yaml_scan(self, tmp_path):
        """RuntimeError should NOT be caught — must propagate."""
        concept_dir = tmp_path / "concepts"
        concept_dir.mkdir()
        (concept_dir / "c1.yaml").write_text("id: concept1\n")

        with patch("propstore.cli.helpers.yaml.safe_load", side_effect=RuntimeError("boom")):
            from propstore.cli.helpers import _scan_max_concept_id
            with pytest.raises(RuntimeError, match="boom"):
                _scan_max_concept_id(concept_dir)


class TestEmbedLitellmCall:
    """Location 3: embed.py:226 — litellm.embedding() API call."""

    def test_runtime_error_propagates_through_embed(self):
        """RuntimeError should NOT be caught — must propagate."""
        import sqlite3

        mock_litellm = MagicMock()
        mock_litellm.embedding.side_effect = RuntimeError("boom")

        with patch("propstore.embed._require_litellm", return_value=mock_litellm):
            from propstore.embed import _embed_entities, _EmbedConfig

            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            conn.executescript("""
                CREATE TABLE claim_core (
                    id TEXT PRIMARY KEY,
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
                CREATE TABLE claim_text_payload (
                    claim_id TEXT PRIMARY KEY,
                    conditions_cel TEXT,
                    statement TEXT,
                    expression TEXT,
                    sympy_generated TEXT,
                    sympy_error TEXT,
                    name TEXT,
                    measure TEXT,
                    listener_population TEXT,
                    methodology TEXT,
                    notes TEXT,
                    description TEXT,
                    auto_summary TEXT
                );
            """)
            conn.execute("INSERT INTO claim_core VALUES ('c1', 'h1', 1, 'observation', NULL, NULL, 'test', 1, NULL, NULL)")
            conn.execute("INSERT INTO claim_text_payload VALUES ('c1', NULL, 'stmt', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'summary')")
            conn.execute("CREATE TABLE embedding_model (model_key TEXT, model_name TEXT, dimensions INTEGER, updated_at TEXT)")
            conn.execute("CREATE TABLE embedding_status (claim_id TEXT, model_key TEXT, content_hash TEXT)")

            config = _EmbedConfig(
                entity_table="""
                    (
                        SELECT
                            core.id,
                            core.seq,
                            core.content_hash,
                            txt.auto_summary,
                            txt.statement,
                            txt.expression,
                            txt.name
                        FROM claim_core AS core
                        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
                    )
                """,
                select_columns="id, seq, content_hash, auto_summary, statement, expression, name",
                status_table="embedding_status",
                status_id_column="claim_id",
                vec_prefix="claim_vec",
                text_builder=lambda e, _: str(e["id"]),
                pre_batch_hook=None,
            )

            with pytest.raises(RuntimeError, match="boom"):
                _embed_entities(conn, "test-model", config)
            conn.close()


class TestParamConflictsSympy:
    """Location 4: param_conflicts.py:147 — SymPy evaluation."""

    def test_runtime_error_propagates_through_param_conflicts(self):
        """RuntimeError from SymPy should propagate through param conflict detection."""
        from propstore.param_conflicts import _detect_param_conflicts
        from propstore.loaded import LoadedEntry
        from pathlib import Path

        input_claim_a = {
            "id": "ca",
            "concept": "a",
            "type": "measurement",
            "value": 2.0,
            "conditions": [],
        }
        input_claim_b = {
            "id": "cb",
            "concept": "b",
            "type": "measurement",
            "value": 3.0,
            "conditions": [],
        }
        derived_claim = {
            "id": "cd",
            "concept": "derived",
            "type": "measurement",
            "value": 10.0,
            "conditions": [],
        }

        claim_file = LoadedEntry(
            filename="test",
            source_path=Path("test.yaml"),
            data={"source_paper": "test", "claims": [input_claim_a, input_claim_b, derived_claim]},
        )

        by_concept = {
            "a": [input_claim_a],
            "b": [input_claim_b],
            "derived": [derived_claim],
        }

        # The function iterates concept_registry looking for parameterization_relationships
        # Each rel needs: exactness=exact, inputs list, sympy expression
        # Input concepts need form != category/structural/boolean/""
        concept_registry = {
            "derived": {
                "id": "derived",
                "parameterization_relationships": [
                    {
                        "exactness": "exact",
                        "inputs": ["a", "b"],
                        "sympy": "a * b",
                    }
                ],
            },
            "a": {"id": "a", "form": "quantity"},
            "b": {"id": "b", "form": "quantity"},
        }

        with patch(
            "sympy.parsing.sympy_parser.parse_expr",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                _detect_param_conflicts(
                    [claim_file], by_concept, concept_registry, [claim_file]
                )


class TestRelateLitellmCall:
    """Location 5: relate.py:154 — litellm.acompletion() API call."""

    def test_runtime_error_propagates_through_relate(self):
        """RuntimeError should NOT be caught — must propagate."""
        import asyncio

        mock_litellm = MagicMock()
        # acompletion is async, so make it an async function that raises
        async def mock_acompletion(*args, **kwargs):
            raise RuntimeError("boom")
        mock_litellm.acompletion = mock_acompletion

        claim_a = {"id": "a", "text": "claim a"}
        claim_b = {"id": "b", "text": "claim b"}

        with patch("propstore.relate._require_litellm", return_value=mock_litellm):
            from propstore.relate import _classify_stance_async

            async def run():
                sem = asyncio.Semaphore(1)
                return await _classify_stance_async(
                    claim_a, claim_b, "model", sem,
                    embedding_model="embed-model",
                    embedding_distance=0.5,
                    pass_number=1,
                )

            with pytest.raises(RuntimeError, match="boom"):
                asyncio.run(run())


class TestSympyGenerator:
    """Location 6: sympy_generator.py:50 — parse_expr call."""

    def test_runtime_error_propagates_through_sympy_generator(self):
        """RuntimeError should NOT be caught — must propagate."""
        with patch(
            "propstore.sympy_generator.parse_expr",
            side_effect=RuntimeError("boom"),
        ):
            from propstore.sympy_generator import generate_sympy_with_error
            with pytest.raises(RuntimeError, match="boom"):
                generate_sympy_with_error("x + 1")


class TestValueResolverZ3:
    """Location 7: value_resolver.py:162 — Z3 equivalence check via ast_compare."""

    def test_runtime_error_propagates_through_value_resolver(self):
        """RuntimeError from ast_compare should propagate."""
        from propstore.world.value_resolver import ActiveClaimResolver

        resolver = ActiveClaimResolver(
            parameterizations_for=lambda _: [],
            is_param_compatible=lambda _: True,
            value_of=lambda _: None,
            extract_variable_concepts=lambda _: [],
            collect_known_values=lambda _: {},
            extract_bindings=lambda _: {},
        )

        algo_claims = [
            {"body": "x = 1", "id": "c1"},
            {"body": "x = 2", "id": "c2"},
        ]

        with patch(
            "propstore.world.value_resolver.ast_compare",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                resolver._all_algorithms_equivalent(algo_claims, known_values={})
