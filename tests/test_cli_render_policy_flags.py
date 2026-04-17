"""CLI-level tests for Phase 4 lifecycle-visibility flags on `pks world`.

Exercises the contract described in
``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``:

- ``pks world status``, ``pks world query``, ``pks world chain``,
  ``pks world derive``, and ``pks world resolve`` each accept
  ``--include-drafts/--no-include-drafts``,
  ``--include-blocked/--no-include-blocked``, and
  ``--show-quarantined/--no-show-quarantined`` flags (default False).
- Flags plumb through to the ``RenderPolicy`` constructor used to bind
  the world, so ``claim_core`` rows carrying ``stage='draft'``,
  ``build_status='blocked'``, or ``promotion_status='blocked'`` surface
  only under the matching opt-in.

The fixture builds a minimal knowledge tree via ``pks build``, then
seeds the compiled sidecar with one claim_core row per lifecycle state
so the CLI tests have something to filter. Seeding after the build is
acceptable here because these tests probe the render layer's
policy-filtering behaviour, not the build pipeline; the Phase 3 tests
already cover the build-time population paths.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from propstore.world import RenderPolicy, WorldModel
from propstore.world.queries import (
    WorldConceptQueryRequest,
    WorldStatusRequest,
    get_world_status,
    query_world_concept,
)
from tests.conftest import normalize_concept_payloads


# ── Fixtures ────────────────────────────────────────────────────────


def _make_concept_doc(name: str, cid: str, domain: str, form: str) -> dict:
    return normalize_concept_payloads(
        [
            {
                "id": cid,
                "canonical_name": name,
                "status": "accepted",
                "definition": f"Test definition for {name}.",
                "domain": domain,
                "created_date": "2026-04-16",
                "form": form,
            }
        ],
        default_domain=domain,
    )[0]


@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Seed a minimal repo with a single concept and a single valid claim,
    then run ``pks build`` so the sidecar is fully populated."""
    monkeypatch.chdir(tmp_path)
    knowledge = tmp_path / "knowledge"
    repo = Repository.init(knowledge)

    adds: dict[str, bytes] = {}
    adds["forms/frequency.yaml"] = yaml.dump(
        {"name": "frequency", "dimensionless": False, "unit_symbol": "Hz"},
        default_flow_style=False,
    ).encode("utf-8")
    adds["concepts/pitch.yaml"] = yaml.dump(
        _make_concept_doc("pitch", "concept1", "speech", "frequency"),
        default_flow_style=False,
        sort_keys=False,
    ).encode("utf-8")
    adds["concepts/.counters/global.next"] = b"2\n"
    repo.git.commit_files(adds, "Seed cli-render-policy workspace")
    repo.git.sync_worktree()

    # Run pks build so the sidecar exists (with schema v3 + lifecycle cols).
    runner = CliRunner()
    sidecar = knowledge / "sidecar" / "propstore.sqlite"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(cli, ["build", "-o", str(sidecar)])
    assert result.exit_code == 0, f"Build failed: {result.output}"
    return tmp_path


def _concept_id(workspace: Path) -> str:
    """The canonical artifact id for the 'pitch' concept committed above."""
    concept_file = workspace / "knowledge" / "concepts" / "pitch.yaml"
    data = yaml.safe_load(concept_file.read_text())
    aid = data.get("artifact_id")
    assert isinstance(aid, str) and aid
    return aid


def _seed_lifecycle_rows(workspace: Path, concept_aid: str) -> None:
    """Insert four claim_core rows (one per lifecycle state) + two
    build_diagnostics rows into the compiled sidecar.

    Rows:
      - ``claim_fixture_draft``   — stage='draft'.
      - ``claim_fixture_blocked`` — build_status='blocked'.
      - ``claim_fixture_promote_blocked`` — promotion_status='blocked',
        branch='source/fixture'.

    The clean final claim for this concept is created by the build path
    via ``freq_paper.yaml``? No — workspace fixture only adds the
    concept. To give the tests a reliably-visible "clean" baseline I
    also insert ``claim_fixture_final`` with default lifecycle values.
    """
    sidecar = workspace / "knowledge" / "sidecar" / "propstore.sqlite"
    conn = sqlite3.connect(sidecar)
    try:
        # Ensure a source row the claim can FK against.
        conn.execute(
            """
            INSERT OR IGNORE INTO source (slug, source_id, kind, origin_type, origin_value)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("fixture_paper", "fixture_paper", "academic_paper", "manual", "fixture"),
        )
        base_cols = (
            "id, primary_logical_id, logical_ids_json, version_id, "
            "content_hash, seq, type, concept_id, source_slug, source_paper, "
            "provenance_page, premise_kind, branch, build_status, stage, "
            "promotion_status"
        )

        def _insert(claim_id, *, build_status="ingested", stage=None,
                    promotion_status=None, branch="master") -> None:
            conn.execute(
                f"""
                INSERT INTO claim_core ({base_cols}) VALUES (
                    ?, ?, '[]', '', '', 0, 'parameter', ?, 'fixture_paper',
                    'fixture_paper', 1, 'ordinary', ?, ?, ?, ?
                )
                """,
                (
                    claim_id,
                    claim_id,
                    concept_aid,
                    branch,
                    build_status,
                    stage,
                    promotion_status,
                ),
            )

        _insert("claim_fixture_final")
        _insert("claim_fixture_draft", stage="draft")
        _insert("claim_fixture_blocked", build_status="blocked")
        _insert(
            "claim_fixture_promote_blocked",
            promotion_status="blocked",
            branch="source/fixture",
        )

        conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref,
                diagnostic_kind, severity, blocking, message
            ) VALUES (?, 'claim', NULL, 'raw_id_input', 'error', 1, ?)
            """,
            (
                "claim_fixture_blocked",
                "claim uses raw 'id' input without canonical identity fields",
            ),
        )
        conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref,
                diagnostic_kind, severity, blocking, message
            ) VALUES (?, 'claim', ?, 'promotion_blocked', 'error', 1, ?)
            """,
            (
                "claim_fixture_promote_blocked",
                "source/fixture:claim_fixture_promote_blocked",
                "finalize error: unresolved stance target",
            ),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture()
def seeded_workspace(workspace: Path) -> Path:
    """Workspace + seeded lifecycle rows in the sidecar."""
    _seed_lifecycle_rows(workspace, _concept_id(workspace))
    return workspace


# ── `pks world status` ──────────────────────────────────────────────


class TestWorldStatusFlags:
    """`pks world status` reports claim counts under the policy."""

    def test_owner_report_default_hides_draft_blocked_promotion(
        self,
        seeded_workspace: Path,
    ) -> None:
        repo = Repository.find(seeded_workspace / "knowledge")
        wm = WorldModel(repo)
        try:
            report = get_world_status(
                wm,
                WorldStatusRequest(policy=RenderPolicy()),
            )
        finally:
            wm.close()

        assert report.visible_claim_count == 1
        assert report.diagnostic_count == 0

    def test_owner_report_all_flags_surface_everything(
        self,
        seeded_workspace: Path,
    ) -> None:
        repo = Repository.find(seeded_workspace / "knowledge")
        wm = WorldModel(repo)
        try:
            report = get_world_status(
                wm,
                WorldStatusRequest(
                    policy=RenderPolicy(
                        include_drafts=True,
                        include_blocked=True,
                        show_quarantined=True,
                    )
                ),
            )
        finally:
            wm.close()

        assert report.visible_claim_count == 4
        assert report.diagnostic_count == 2

    def test_default_hides_draft_blocked_promotion(self, seeded_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli, ["-C", str(seeded_workspace / "knowledge"), "world", "status"]
        )
        assert result.exit_code == 0, result.output
        # Only the 'clean' claim should count under the default policy.
        assert "Claims:   1" in result.output

    def test_include_drafts_increments_count(self, seeded_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-C",
                str(seeded_workspace / "knowledge"),
                "world",
                "status",
                "--include-drafts",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Claims:   2" in result.output

    def test_include_blocked_surfaces_both_blocked_variants(
        self, seeded_workspace: Path
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-C",
                str(seeded_workspace / "knowledge"),
                "world",
                "status",
                "--include-blocked",
            ],
        )
        assert result.exit_code == 0, result.output
        # final + build_status=blocked + promotion_status=blocked = 3.
        assert "Claims:   3" in result.output

    def test_all_flags_surface_everything(self, seeded_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-C",
                str(seeded_workspace / "knowledge"),
                "world",
                "status",
                "--include-drafts",
                "--include-blocked",
                "--show-quarantined",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Claims:   4" in result.output
        # --show-quarantined should also add a Diagnostics line.
        assert "Diagnostics:" in result.output


# ── `pks world query` ───────────────────────────────────────────────


class TestWorldQueryFlags:
    """`pks world query <concept>` lists claims under policy."""

    def test_owner_report_default_hides_draft(self, seeded_workspace: Path) -> None:
        aid = _concept_id(seeded_workspace)
        repo = Repository.find(seeded_workspace / "knowledge")
        wm = WorldModel(repo)
        try:
            report = query_world_concept(
                wm,
                WorldConceptQueryRequest(target=aid, policy=RenderPolicy()),
            )
        finally:
            wm.close()

        assert [claim.display_id for claim in report.claims] == ["claim_fixture_final"]
        assert report.diagnostics == ()

    def test_owner_report_all_flags_surfaces_diagnostics(
        self,
        seeded_workspace: Path,
    ) -> None:
        aid = _concept_id(seeded_workspace)
        repo = Repository.find(seeded_workspace / "knowledge")
        wm = WorldModel(repo)
        try:
            report = query_world_concept(
                wm,
                WorldConceptQueryRequest(
                    target=aid,
                    policy=RenderPolicy(
                        include_drafts=True,
                        include_blocked=True,
                        show_quarantined=True,
                    ),
                ),
            )
        finally:
            wm.close()

        assert {claim.display_id for claim in report.claims} == {
            "claim_fixture_final",
            "claim_fixture_draft",
            "claim_fixture_blocked",
            "claim_fixture_promote_blocked",
        }
        assert [diagnostic.diagnostic_kind for diagnostic in report.diagnostics] == [
            "raw_id_input",
            "promotion_blocked",
        ]

    def test_default_hides_draft(self, seeded_workspace: Path) -> None:
        runner = CliRunner()
        aid = _concept_id(seeded_workspace)
        result = runner.invoke(
            cli,
            ["-C", str(seeded_workspace / "knowledge"), "world", "query", aid],
        )
        assert result.exit_code == 0, result.output
        assert "claim_fixture_final" in result.output
        assert "claim_fixture_draft" not in result.output

    def test_include_drafts_surfaces_draft(self, seeded_workspace: Path) -> None:
        runner = CliRunner()
        aid = _concept_id(seeded_workspace)
        result = runner.invoke(
            cli,
            [
                "-C",
                str(seeded_workspace / "knowledge"),
                "world",
                "query",
                aid,
                "--include-drafts",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "claim_fixture_draft" in result.output

    def test_include_blocked_surfaces_blocked(self, seeded_workspace: Path) -> None:
        runner = CliRunner()
        aid = _concept_id(seeded_workspace)
        result = runner.invoke(
            cli,
            [
                "-C",
                str(seeded_workspace / "knowledge"),
                "world",
                "query",
                aid,
                "--include-blocked",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "claim_fixture_blocked" in result.output
        assert "claim_fixture_promote_blocked" in result.output


# ── `pks world resolve/chain/derive` accept the flags ──────────────


class TestWorldCommandFlagsAccepted:
    """The three flags are registered on the remaining world subcommands
    named by scout D (resolve, chain, derive). The behavioral contract is
    exercised above for status + query; here we only verify the flags
    parse without error on the other subcommands."""

    @pytest.mark.parametrize(
        "subcommand_args",
        [
            ("resolve",),
            ("chain",),
            ("derive",),
        ],
    )
    def test_flags_accepted_on_subcommand(
        self, seeded_workspace: Path, subcommand_args: tuple[str, ...]
    ) -> None:
        runner = CliRunner()
        aid = _concept_id(seeded_workspace)
        args = [
            "-C",
            str(seeded_workspace / "knowledge"),
            "world",
            *subcommand_args,
            aid,
            "--include-drafts",
            "--include-blocked",
            "--show-quarantined",
        ]
        if subcommand_args == ("resolve",):
            args.extend(["--strategy", "recency"])
        result = runner.invoke(cli, args)
        # Subcommand may exit non-zero for orthogonal reasons (e.g. no
        # parameterization for `derive`); the relevant contract here is
        # that the flag parsing did NOT fail with "no such option".
        assert "no such option" not in result.output.lower()
        assert "error: got unexpected" not in result.output.lower()
