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

import json
import sqlite3
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.app.predicates import PredicateAddRequest, add_predicate
from propstore.app.rules import RuleAddRequest, add_rule
from propstore.core.claim_types import ClaimType
from propstore.families.claims.documents import (
    ClaimDocument,
    ClaimLogicalIdDocument,
    ClaimSourceDocument,
    ProvenanceDocument,
)
from propstore.families.contexts.documents import ContextDocument, ContextReferenceDocument
from propstore.families.documents.sources import (
    SourceJustificationDocument,
)
from propstore.families.identity.justifications import stamp_justification_artifact_id
from propstore.families.identity.stances import stamp_stance_artifact_id
from propstore.families.registry import ClaimRef, ContextRef, JustificationRef, StanceRef
from propstore.repository import Repository
from propstore.sidecar.build import materialize_world_sidecar
from propstore.stances import StanceType
from propstore.world import RenderPolicy, WorldQuery
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

    handle, _ = materialize_world_sidecar(repo)
    assert handle.path.exists()
    return tmp_path


def _concept_id(workspace: Path) -> str:
    """The canonical artifact id for the 'pitch' concept committed above."""
    concept_file = workspace / "knowledge" / "concepts" / "pitch.yaml"
    data = yaml.safe_load(concept_file.read_text())
    aid = data.get("artifact_id")
    assert isinstance(aid, str) and aid
    return aid


def _world_store_path(workspace: Path) -> Path:
    handle, _ = materialize_world_sidecar(Repository.find(workspace / "knowledge"))
    return handle.path


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
    sidecar = _world_store_path(workspace)
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
            "content_hash, seq, type, source_slug, source_paper, "
            "provenance_page, premise_kind, branch, build_status, stage, "
            "promotion_status"
        )

        def _insert(claim_id, *, build_status="ingested", stage=None,
                    promotion_status=None, branch="master") -> None:
            conn.execute("DELETE FROM claim_concept_link WHERE claim_id = ?", (claim_id,))
            conn.execute("DELETE FROM claim_core WHERE id = ?", (claim_id,))
            conn.execute(
                f"""
                INSERT INTO claim_core ({base_cols}) VALUES (
                    ?, ?, '[]', '', '', 0, 'parameter', 'fixture_paper',
                    'fixture_paper', 1, 'ordinary', ?, ?, ?, ?
                )
                """,
                (
                    claim_id,
                    claim_id,
                    branch,
                    build_status,
                    stage,
                    promotion_status,
                ),
            )
            conn.execute(
                """
                INSERT INTO claim_concept_link (
                    claim_id, concept_id, role, ordinal, binding_name
                ) VALUES (?, ?, 'output', 0, NULL)
                """,
                (claim_id, concept_aid),
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


def _seed_authored_reasoning(repo: Repository, concept_aid: str) -> None:
    context_ref = ContextRef("ctx_fixture")
    repo.families.contexts.save(
        context_ref,
        ContextDocument(id=str(context_ref), name="Fixture context"),
        message="Seed world status context",
    )
    for claim_id in ("claim_fixture_final", "claim_fixture_draft"):
        repo.families.claims.save(
            ClaimRef(claim_id),
            ClaimDocument(
                artifact_id=claim_id,
                logical_ids=(
                    ClaimLogicalIdDocument(namespace="fixture", value=claim_id),
                ),
                version_id=f"sha256:{claim_id.encode('utf-8').hex():0<64}"[:71],
                type=ClaimType.PARAMETER,
                output_concept=concept_aid,
                value=1.0,
                unit="Hz",
                provenance=ProvenanceDocument(paper="fixture_paper", page=1),
                source=ClaimSourceDocument(paper="fixture_paper"),
                context=ContextReferenceDocument(id=str(context_ref)),
                statement=claim_id,
            ),
            message="Seed world status claims",
        )
    add_predicate(
        repo,
        PredicateAddRequest(
            file="fixture",
            predicate_id="fixture_visible_claim",
            arity=1,
            arg_types=("str",),
        ),
    )
    add_predicate(
        repo,
        PredicateAddRequest(
            file="fixture",
            predicate_id="fixture_hidden_claim",
            arity=1,
            arg_types=("str",),
        ),
    )
    add_rule(
        repo,
        RuleAddRequest(
            file="fixture",
            paper="fixture_paper",
            rule_id="r_visible",
            kind="strict",
            head="fixture_visible_claim(clean)",
        ),
    )
    add_rule(
        repo,
        RuleAddRequest(
            file="fixture",
            paper="fixture_paper",
            rule_id="r_hidden",
            kind="defeasible",
            head="fixture_hidden_claim(draft)",
        ),
    )
    justification_payload = stamp_justification_artifact_id(
        SourceJustificationDocument(
            id="j_fixture",
            conclusion="claim_fixture_final",
            premises=("claim_fixture_draft",),
            rule_kind="reported_claim",
            rule_strength="defeasible",
        ).to_payload()
    )
    justification_ref = JustificationRef(str(justification_payload["artifact_code"]))
    repo.families.justifications.save(
        justification_ref,
        repo.families.justifications.coerce(
            justification_payload,
            source=repo.families.justifications.address(justification_ref).require_path(),
        ),
        message="Seed world status justifications",
    )
    stance_payload = stamp_stance_artifact_id(
        {
            "source_claim": "claim_fixture_final",
            "target": "claim_fixture_draft",
            "type": StanceType.SUPPORTS.value,
            "strength": "low",
        }
    )
    stance_ref = StanceRef(str(stance_payload["artifact_code"]))
    repo.families.stances.save(
        stance_ref,
        repo.families.stances.coerce(
            stance_payload,
            source=repo.families.stances.address(stance_ref).require_path(),
        ),
        message="Seed world status stances",
    )


@pytest.fixture()
def seeded_workspace(workspace: Path) -> Path:
    """Workspace + seeded lifecycle rows in the sidecar."""
    concept_aid = _concept_id(workspace)
    _seed_authored_reasoning(Repository.find(workspace / "knowledge"), concept_aid)
    _seed_lifecycle_rows(workspace, concept_aid)
    return workspace


# ── `pks world status` ──────────────────────────────────────────────


class TestWorldStatusFlags:
    """`pks world status` reports claim counts under the policy."""

    def test_owner_report_default_hides_draft_blocked_promotion(
        self,
        seeded_workspace: Path,
    ) -> None:
        repo = Repository.find(seeded_workspace / "knowledge")
        wm = WorldQuery(repo)
        try:
            report = get_world_status(
                wm,
                WorldStatusRequest(policy=RenderPolicy()),
            )
        finally:
            wm.close()

        assert report.visible_claim_count == 1
        assert report.diagnostic_count == 0
        assert report.predicate_count == 0
        assert report.rule_count == 0

    def test_owner_report_all_flags_surface_everything(
        self,
        seeded_workspace: Path,
    ) -> None:
        repo = Repository.find(seeded_workspace / "knowledge")
        wm = WorldQuery(repo)
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

    def test_app_report_counts_authored_reasoning_artifacts(
        self,
        seeded_workspace: Path,
    ) -> None:
        from propstore.app.world import AppWorldStatusRequest, world_status

        repo = Repository.find(seeded_workspace / "knowledge")
        report = world_status(repo, AppWorldStatusRequest())
        sidecar = _world_store_path(seeded_workspace)
        conn = sqlite3.connect(sidecar)
        try:
            sql_justification_count = conn.execute(
                "SELECT COUNT(*) FROM justification"
            ).fetchone()[0]
        finally:
            conn.close()

        assert report.predicate_count == 2
        assert report.rule_count == 2
        assert report.authored_justification_count == sql_justification_count
        assert report.stance_count == 1

    def test_default_hides_draft_blocked_promotion(self, seeded_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli, ["-C", str(seeded_workspace / "knowledge"), "world", "status"]
        )
        assert result.exit_code == 0, result.output
        # Only the 'clean' claim should count under the default policy.
        assert "Claims:         1" in result.output
        assert "Predicates:     2" in result.output
        assert "Rules:          2" in result.output
        assert "Authored justifications: 1" in result.output
        assert "Justifications:" not in result.output
        assert "Stances:        1" in result.output
        assert "Conflict witnesses:" in result.output
        assert "Conflicts:" not in result.output

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
        assert "Claims:         2" in result.output

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
        assert "Claims:         3" in result.output

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
        assert "Claims:         4" in result.output
        # --show-quarantined should also add a Diagnostics line.
        assert "Diagnostics:" in result.output

    def test_status_json_uses_report_shape(self, seeded_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-C",
                str(seeded_workspace / "knowledge"),
                "world",
                "status",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0, result.output

        data = json.loads(result.output)
        assert data["visible_claim_count"] == 1
        assert data["predicate_count"] == 2
        assert "conflict_count" in data


# ── `pks world query` ───────────────────────────────────────────────


class TestWorldQueryFlags:
    """`pks world query <concept>` lists claims under policy."""

    def test_owner_report_default_hides_draft(self, seeded_workspace: Path) -> None:
        aid = _concept_id(seeded_workspace)
        repo = Repository.find(seeded_workspace / "knowledge")
        wm = WorldQuery(repo)
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
        wm = WorldQuery(repo)
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

    def test_unambiguous_short_name_prints_resolution(
        self,
        seeded_workspace: Path,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-C",
                str(seeded_workspace / "knowledge"),
                "world",
                "query",
                "definition",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Resolved definition ->" in result.output
        assert "claim_fixture_final" in result.output

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

    def test_query_json_uses_report_shape(self, seeded_workspace: Path) -> None:
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
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0, result.output

        data = json.loads(result.output)
        assert data["canonical_name"] == "pitch"
        assert data["claims"][0]["display_id"] == "claim_fixture_final"


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
