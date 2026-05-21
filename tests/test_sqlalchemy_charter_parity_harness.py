from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.compare_sqlalchemy_charter_parity import main


def test_parity_harness_passes_matching_sqlite_fixtures(tmp_path: Path) -> None:
    before = tmp_path / "before.sqlite"
    after = tmp_path / "after.sqlite"
    out = tmp_path / "report.json"
    _fixture_db(before)
    _fixture_db(after)
    _baseline(before)

    code = main(_args(tmp_path, before, after, out))

    report = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0
    assert report["failures"] == []
    assert report["row_counts"]["entity"]["status"] == "pass"


def test_parity_harness_records_schema_catalog_without_row_comparing_it(tmp_path: Path) -> None:
    before = tmp_path / "before.sqlite"
    after = tmp_path / "after.sqlite"
    out = tmp_path / "report.json"
    _fixture_db(before)
    _fixture_db(after, schema_hash="schema-1")
    _baseline(before)

    code = main(_args(tmp_path, before, after, out))

    report = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0
    assert "quire_schema_catalog" not in report["tables"]
    assert report["after"]["schema_hash"] == "schema-1"


def test_parity_harness_fails_missing_key(tmp_path: Path) -> None:
    before = tmp_path / "before.sqlite"
    after = tmp_path / "after.sqlite"
    out = tmp_path / "report.json"
    _fixture_db(before)
    _fixture_db(after, include_second=False)
    _baseline(before)

    code = main(_args(tmp_path, before, after, out))

    report = json.loads(out.read_text(encoding="utf-8"))
    assert code == 1
    assert report["key_sets"]["entity"]["missing_keys"] == ['["b"]']
    assert report["failures"]


def test_parity_harness_allows_extra_empty_table(tmp_path: Path) -> None:
    before = tmp_path / "before.sqlite"
    after = tmp_path / "after.sqlite"
    out = tmp_path / "report.json"
    _fixture_db(before)
    _fixture_db(after, extra_table=True)
    _baseline(before)

    code = main(_args(tmp_path, before, after, out))

    report = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0
    assert report["tables"]["extra_empty"]["status"] == "pass"
    assert report["tables"]["extra_empty"]["columns"] == ["id"]


def test_parity_harness_rejects_extra_populated_table(tmp_path: Path) -> None:
    before = tmp_path / "before.sqlite"
    after = tmp_path / "after.sqlite"
    out = tmp_path / "report.json"
    _fixture_db(before)
    _fixture_db(after, extra_table=True, populate_extra=True)
    _baseline(before)

    code = main(_args(tmp_path, before, after, out))

    report = json.loads(out.read_text(encoding="utf-8"))
    assert code == 1
    assert "extra table extra_empty" in report["failures"]


def test_parity_harness_requires_vector_blocks(tmp_path: Path) -> None:
    before = tmp_path / "before.sqlite"
    after = tmp_path / "after.sqlite"
    out = tmp_path / "report.json"
    _fixture_db(before)
    _fixture_db(after)
    _baseline(before)

    passing = main(
        _args(tmp_path, before, after, out)
        + ["--require-vector", "entity_vec"]
    )
    failing = main(
        _args(tmp_path, before, after, out)
        + ["--require-vector", "missing_vec"]
    )

    report = json.loads(out.read_text(encoding="utf-8"))
    assert passing == 0
    assert failing == 1
    assert "missing passing vector comparison block" in report["failures"][0]


def test_parity_harness_emits_required_semantic_vector_blocks(tmp_path: Path) -> None:
    before = tmp_path / "before.sqlite"
    after = tmp_path / "after.sqlite"
    out = tmp_path / "report.json"
    _fixture_db(before)
    _fixture_db(after)
    _vector_tables(before)
    _vector_tables(after)
    _baseline(before)

    code = main(
        _args(tmp_path, before, after, out)
        + [
            "--require-vector",
            "claim-similarity",
            "--require-vector",
            "concept-similarity",
            "--require-vector",
            "claim-agree-disagree",
            "--require-vector",
            "concept-agree-disagree",
            "--require-vector",
            "embedding-snapshot-restore",
        ]
    )

    report = json.loads(out.read_text(encoding="utf-8"))
    vector_names = {block["name"] for block in report["vectors"]}
    assert code == 0
    assert report["failures"] == []
    assert vector_names >= {
        "claim-similarity",
        "concept-similarity",
        "claim-agree-disagree",
        "concept-agree-disagree",
        "embedding-snapshot-restore",
    }


def test_parity_harness_requires_behavior_blocks(tmp_path: Path) -> None:
    before = tmp_path / "before.sqlite"
    after = tmp_path / "after.sqlite"
    out = tmp_path / "report.json"
    _fixture_db(before)
    _fixture_db(after)
    _baseline(before)

    passing = main(
        _args(tmp_path, before, after, out)
        + ["--require-behavior", "behavior_claim_lookup"]
    )
    failing = main(
        _args(tmp_path, before, after, out)
        + ["--require-behavior", "missing_behavior"]
    )

    report = json.loads(out.read_text(encoding="utf-8"))
    assert passing == 0
    assert failing == 1
    assert "missing passing behavior comparison block" in report["failures"][0]


def test_parity_harness_rejects_missing_baseline(tmp_path: Path) -> None:
    before = tmp_path / "before.sqlite"
    after = tmp_path / "after.sqlite"
    out = tmp_path / "report.json"
    _fixture_db(before)
    _fixture_db(after)

    code = main(_args(tmp_path, before, after, out))

    report = json.loads(out.read_text(encoding="utf-8"))
    assert code == 1
    assert "missing baseline report" in report["failures"][0]


def test_parity_harness_rejects_semantic_input_hash_mismatch(tmp_path: Path) -> None:
    before = tmp_path / "before.sqlite"
    after = tmp_path / "after.sqlite"
    out = tmp_path / "report.json"
    _fixture_db(before)
    _fixture_db(after)
    _baseline(before, semantic_input_hash="other")

    code = main(_args(tmp_path, before, after, out))

    report = json.loads(out.read_text(encoding="utf-8"))
    assert code == 1
    assert "semantic_input_hash mismatch" in report["failures"][0]


def _args(tmp_path: Path, before: Path, after: Path, out: Path) -> list[str]:
    workstream = tmp_path / "04-propstore-build-orchestration.md"
    workstream.write_text(
        """
# Propstore Build Orchestration Cutover Workstream

owner build-orchestration

## Data-Parity Gate

Accepted parity difference allowlist:

- deleted test-only item
""",
        encoding="utf-8",
    )
    return [
        "--knowledge-dir",
        str(tmp_path),
        "--before",
        str(before),
        "--after",
        str(after),
        "--owner",
        "build-orchestration",
        "--workstream",
        str(workstream),
        "--out",
        str(out),
    ]


def _fixture_db(
    path: Path,
    *,
    include_second: bool = True,
    schema_hash: str | None = None,
    extra_table: bool = False,
    populate_extra: bool = False,
) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE entity (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("CREATE TABLE entity_vec (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute(
            "CREATE TABLE behavior_claim_lookup (id TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        conn.execute("INSERT INTO entity VALUES ('a', 'alpha')")
        conn.execute("INSERT INTO entity_vec VALUES ('a', 'alpha')")
        conn.execute("INSERT INTO behavior_claim_lookup VALUES ('a', 'alpha')")
        if include_second:
            conn.execute("INSERT INTO entity VALUES ('b', 'beta')")
        if extra_table:
            conn.execute("CREATE TABLE extra_empty (id TEXT PRIMARY KEY)")
            if populate_extra:
                conn.execute("INSERT INTO extra_empty VALUES ('extra')")
        if schema_hash is not None:
            conn.execute(
                """
                CREATE TABLE quire_schema_catalog (
                    key TEXT PRIMARY KEY,
                    schema_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "INSERT INTO quire_schema_catalog VALUES ('default', ?, '{}')",
                (schema_hash,),
            )
        conn.commit()
    finally:
        conn.close()


def _baseline(before: Path, *, semantic_input_hash: str = "") -> None:
    (before.parent / "baseline.json").write_text(
        json.dumps(
            {
                "baseline_head_sha": "baseline",
                "semantic_input_hash": semantic_input_hash,
            }
        ),
        encoding="utf-8",
    )


def _vector_tables(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE embedding_model (
                model_identity_hash TEXT PRIMARY KEY,
                provider TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE embedding_status (
                model_identity_hash TEXT NOT NULL,
                claim_id TEXT NOT NULL,
                PRIMARY KEY (model_identity_hash, claim_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE concept_embedding_status (
                model_identity_hash TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                PRIMARY KEY (model_identity_hash, concept_id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
