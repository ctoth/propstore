"""Phase 10-1: ``pks source`` CLI adapter tests (CliRunner over real owners).

Ports the behavioural intent of the reference ``test_source_cli.py`` /
``test_cli_source_status.py`` onto the rewrite owner API. Each test drives the
command through ``from propstore.cli import cli`` with ``CliRunner`` and asserts
on exit codes, rendered output, and git/owner-visible state. Seeding uses the
rewrite family ``save`` surface (the idiom the owner tests use), which commits to
git master so the CLI's freshly resolved repository sees it.

SKIPPED reference subcommands (no owner in the rewrite): ``source list``
(no source-branch lister owner) and ``source stamp-provenance`` (deprecated;
no ``stamp_source_provenance`` owner). The reference ``add-*`` auto-finalize
assertions are intentionally not ported: the rewrite batch owners do not
auto-finalize and the CLI must not own finalize semantics.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from condition_ir import KindType

from propstore.cli import cli
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.forms import FormDefinition
from propstore.repository import Repository
from propstore.source.common import (
    load_source_concepts_document,
    load_source_document,
)
from propstore.uri import verify_ni_uri

_RUNNER = CliRunner()

_ADDITIONAL_SOURCE_KINDS = (
    "chat_message",
    "dataset_release",
    "encyclopedia_article",
    "forum_message",
    "handbook_chapter",
    "issue_comment",
    "legal_document",
    "monograph_chapter",
    "reference_entry",
    "software_revision",
    "technical_report",
    "technical_specification",
    "textbook_chapter",
    "web_page_snapshot",
)


def _init_repo(tmp_path: Path) -> Repository:
    return Repository.init(tmp_path / "knowledge")


def _seed_form(repo: Repository, name: str = "dimensionless") -> None:
    repo.families.form.save(
        name,
        FormDefinition(name=name, kind=KindType.QUANTITY, is_dimensionless=True),
        message=f"seed form {name}",
    )


def _seed_context(repo: Repository, context_id: str = "ctx") -> None:
    repo.families.context.save(
        context_id,
        Context(context_id=context_id, name=context_id),
        message=f"seed context {context_id}",
    )


def _invoke(repo: Repository, *args: str):
    return _RUNNER.invoke(cli, ["-C", str(repo.root), "source", *args])


def _init_source(repo: Repository, name: str = "demo") -> None:
    result = _invoke(
        repo,
        "init",
        name,
        "--kind",
        "academic_paper",
        "--origin-type",
        "manual",
        "--origin-value",
        name,
    )
    assert result.exit_code == 0, result.output


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


def test_source_init_creates_branch_and_manifest(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    result = _invoke(
        repo,
        "init",
        "Halpin_2010",
        "--kind",
        "academic_paper",
        "--origin-type",
        "doi",
        "--origin-value",
        "10.1007/x",
    )
    assert result.exit_code == 0, result.output
    assert "Initialized source/Halpin_2010" in result.output
    assert repo.require_git().branch_sha("source/Halpin_2010") is not None
    sd = load_source_document(Repository.find(repo.root), "Halpin_2010")
    assert sd.kind.value == "academic_paper"
    assert sd.origin.type == "doi"
    assert sd.origin.value == "10.1007/x"
    assert sd.id is not None and sd.id.startswith("tag:")


def test_source_init_accepts_mailing_list_message_with_content_digest(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    content = b"From: author@example.org\nSubject: Federation\n\nMessage body.\n"
    message = tmp_path / "message.eml"
    message.write_bytes(content)

    result = _invoke(
        repo,
        "init",
        "Federation_2026_07_12",
        "--kind",
        "mailing_list_message",
        "--origin-type",
        "file",
        "--origin-value",
        "federation/2026-07-12.eml",
        "--content-file",
        str(message),
    )

    assert result.exit_code == 0, result.output
    source = load_source_document(
        Repository.find(repo.root), "Federation_2026_07_12"
    )
    assert source.kind.value == "mailing_list_message"
    assert source.origin.type == "file"
    assert source.origin.value == "federation/2026-07-12.eml"
    assert source.origin.content_ref is not None
    assert verify_ni_uri(source.origin.content_ref, content)


@pytest.mark.parametrize("source_kind", _ADDITIONAL_SOURCE_KINDS)
def test_source_init_accepts_closed_source_vocabulary(
    tmp_path: Path, source_kind: str
) -> None:
    repo = _init_repo(tmp_path)

    result = _invoke(
        repo,
        "init",
        "demo",
        "--kind",
        source_kind,
        "--origin-type",
        "manual",
        "--origin-value",
        "fixture",
    )

    assert result.exit_code == 0, result.output
    source = load_source_document(Repository.find(repo.root), "demo")
    assert source.kind.value == source_kind


def test_source_init_accepts_immutable_encyclopedia_article_url(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    content = b"Wikipedia article revision content"
    article = tmp_path / "article.wikitext"
    article.write_bytes(content)
    revision_url = "https://en.wikipedia.org/w/index.php?title=Logic&oldid=1324583158"

    result = _invoke(
        repo,
        "init",
        "Wikipedia_Logic_1324583158",
        "--kind",
        "encyclopedia_article",
        "--origin-type",
        "url",
        "--origin-value",
        revision_url,
        "--content-file",
        str(article),
    )

    assert result.exit_code == 0, result.output
    source = load_source_document(
        Repository.find(repo.root), "Wikipedia_Logic_1324583158"
    )
    assert source.kind.value == "encyclopedia_article"
    assert source.origin.type == "url"
    assert source.origin.value == revision_url
    assert source.origin.content_ref is not None
    assert verify_ni_uri(source.origin.content_ref, content)


def test_source_init_rejects_unknown_kind(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    result = _invoke(
        repo,
        "init",
        "demo",
        "--kind",
        "bogus_kind",
        "--origin-type",
        "manual",
        "--origin-value",
        "demo",
    )
    assert result.exit_code != 0
    assert "Unsupported source kind" in result.output


def test_source_init_rejects_unknown_origin_type(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    result = _invoke(
        repo,
        "init",
        "demo",
        "--kind",
        "encyclopedia_article",
        "--origin-type",
        "mutable_web_location",
        "--origin-value",
        "https://example.org/wiki/Logic",
    )
    assert result.exit_code != 0
    assert "Unsupported source origin type" in result.output


# ---------------------------------------------------------------------------
# write-notes / write-metadata
# ---------------------------------------------------------------------------


def test_write_notes_commits_only_to_source_branch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _init_source(repo)
    notes = tmp_path / "notes.md"
    notes.write_text("# Notes\n\nbody\n", encoding="utf-8")

    result = _invoke(repo, "write-notes", "demo", "--file", str(notes))
    assert result.exit_code == 0, result.output

    tip = repo.require_git().branch_sha("source/demo")
    assert tip is not None
    stored = repo.require_git().read_file("notes.md", commit=tip).decode("utf-8")
    assert stored.replace("\r\n", "\n") == "# Notes\n\nbody\n"
    try:
        repo.require_git().read_file("notes.md")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("notes.md should not be on master")


def test_write_metadata_commits_json(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _init_source(repo)
    meta = tmp_path / "metadata.json"
    meta.write_text(json.dumps({"title": "Demo", "year": "2026"}), encoding="utf-8")

    result = _invoke(repo, "write-metadata", "demo", "--file", str(meta))
    assert result.exit_code == 0, result.output

    tip = repo.require_git().branch_sha("source/demo")
    assert tip is not None
    loaded = json.loads(repo.require_git().read_file("metadata.json", commit=tip))
    assert loaded["title"] == "Demo"


# ---------------------------------------------------------------------------
# propose-concept
# ---------------------------------------------------------------------------


def test_propose_concept_reports_proposed(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_form(repo)
    _init_source(repo)
    result = _invoke(
        repo,
        "propose-concept",
        "demo",
        "--concept-name",
        "brand_new",
        "--definition",
        "a new thing",
        "--form",
        "dimensionless",
    )
    assert result.exit_code == 0, result.output
    assert "Proposed new concept" in result.output
    assert "brand_new" in result.output


def test_propose_concept_reports_linked(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_form(repo)
    repo.families.concept.save(
        "ps:concept:widget",
        Concept(concept_id="ps:concept:widget", canonical_name="widget"),
        message="seed concept",
    )
    _init_source(repo)
    result = _invoke(
        repo,
        "propose-concept",
        "demo",
        "--concept-name",
        "widget",
        "--definition",
        "a widget",
        "--form",
        "dimensionless",
    )
    assert result.exit_code == 0, result.output
    assert "Linked" in result.output
    assert "ps:concept:widget" in result.output


def test_propose_concept_rejects_unknown_form(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_form(repo, "dimensionless")
    _init_source(repo)
    result = _invoke(
        repo,
        "propose-concept",
        "demo",
        "--concept-name",
        "c",
        "--definition",
        "d",
        "--form",
        "bogus_form",
    )
    assert result.exit_code != 0
    assert "Unknown form" in result.output
    assert "bogus_form" in result.output


def test_propose_concept_category_values_and_closed(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_form(repo, "category")
    _init_source(repo)
    result = _invoke(
        repo,
        "propose-concept",
        "demo",
        "--concept-name",
        "severity",
        "--definition",
        "levels",
        "--form",
        "category",
        "--values",
        "low,medium,high",
        "--closed",
    )
    assert result.exit_code == 0, result.output
    doc = load_source_concepts_document(Repository.find(repo.root), "demo")
    assert doc is not None
    params = doc.concepts[0].form_parameters
    assert params is not None
    assert params.values == ("low", "medium", "high")
    assert params.extensible is False


# ---------------------------------------------------------------------------
# add-concepts (batch)
# ---------------------------------------------------------------------------


def test_add_concepts_batch_stores_inventory(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_form(repo)
    _init_source(repo)
    concepts_file = tmp_path / "concepts.yaml"
    concepts_file.write_text(
        yaml.safe_dump(
            {
                "concepts": [
                    {
                        "local_name": "bridge",
                        "proposed_name": "bridge",
                        "definition": "bridges things",
                        "form": "dimensionless",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    result = _invoke(repo, "add-concepts", "demo", "--batch", str(concepts_file))
    assert result.exit_code == 0, result.output

    doc = load_source_concepts_document(Repository.find(repo.root), "demo")
    assert doc is not None
    assert doc.concepts[0].local_name == "bridge"
    assert doc.concepts[0].status == "proposed"


def test_add_concepts_batch_rejects_unknown_form(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_form(repo)
    _init_source(repo)
    concepts_file = tmp_path / "concepts.yaml"
    concepts_file.write_text(
        yaml.safe_dump(
            {"concepts": [{"local_name": "c", "definition": "d", "form": "bogus"}]}
        ),
        encoding="utf-8",
    )
    result = _invoke(repo, "add-concepts", "demo", "--batch", str(concepts_file))
    assert result.exit_code != 0
    assert "Unknown form" in result.output


# ---------------------------------------------------------------------------
# propose-claim / add-claim
# ---------------------------------------------------------------------------


def _propose_widget_and_claim(repo: Repository, claim_id: str = "c1") -> None:
    _seed_form(repo)
    _init_source(repo)
    assert (
        _invoke(
            repo,
            "propose-concept",
            "demo",
            "--concept-name",
            "widget",
            "--definition",
            "a widget",
            "--form",
            "dimensionless",
        ).exit_code
        == 0
    )


def test_propose_claim_reports_artifact(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _propose_widget_and_claim(repo)
    result = _invoke(
        repo,
        "propose-claim",
        "demo",
        "--id",
        "c1",
        "--type",
        "observation",
        "--context",
        "ctx",
        "--statement",
        "widgets exist",
        "--concept-ref",
        "widget",
    )
    assert result.exit_code == 0, result.output
    assert "Proposed claim 'c1'" in result.output
    assert "ps:claim:" in result.output


def test_propose_claim_unknown_concept_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_form(repo)
    _init_source(repo)
    result = _invoke(
        repo,
        "propose-claim",
        "demo",
        "--id",
        "c1",
        "--type",
        "observation",
        "--context",
        "ctx",
        "--statement",
        "s",
        "--concept-ref",
        "not_proposed",
    )
    assert result.exit_code != 0
    assert "unknown concept reference" in result.output


def test_add_claim_batch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _propose_widget_and_claim(repo)
    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "c1",
                        "type": "observation",
                        "context": "ctx",
                        "statement": "s",
                        "concepts": ["widget"],
                        "provenance": {"page": 1},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = _invoke(repo, "add-claim", "demo", "--batch", str(claims_file))
    assert result.exit_code == 0, result.output
    assert "Wrote claims" in result.output


# ---------------------------------------------------------------------------
# propose-stance / propose-justification
# ---------------------------------------------------------------------------


def _two_claims(repo: Repository) -> None:
    _propose_widget_and_claim(repo)
    for handle in ("c1", "c2"):
        assert (
            _invoke(
                repo,
                "propose-claim",
                "demo",
                "--id",
                handle,
                "--type",
                "observation",
                "--context",
                "ctx",
                "--statement",
                handle,
                "--concept-ref",
                "widget",
            ).exit_code
            == 0
        )


def test_propose_stance(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _two_claims(repo)
    result = _invoke(
        repo,
        "propose-stance",
        "demo",
        "--source-claim",
        "c1",
        "--target",
        "c2",
        "--type",
        "supports",
    )
    assert result.exit_code == 0, result.output
    assert "Proposed stance" in result.output


def test_propose_stance_unknown_type_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _two_claims(repo)
    result = _invoke(
        repo,
        "propose-stance",
        "demo",
        "--source-claim",
        "c1",
        "--target",
        "c2",
        "--type",
        "not_a_stance",
    )
    assert result.exit_code != 0
    assert "Unknown stance_type" in result.output


def test_propose_justification(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _two_claims(repo)
    result = _invoke(
        repo,
        "propose-justification",
        "demo",
        "--id",
        "j1",
        "--conclusion",
        "c1",
        "--premises",
        "c2",
        "--rule-kind",
        "empirical_support",
        "--rule-strength",
        "defeasible",
    )
    assert result.exit_code == 0, result.output
    assert "Proposed justification 'j1'" in result.output


def test_propose_justification_invalid_rule_kind(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _two_claims(repo)
    result = _invoke(
        repo,
        "propose-justification",
        "demo",
        "--id",
        "j1",
        "--conclusion",
        "c1",
        "--premises",
        "c2",
        "--rule-kind",
        "made_up",
    )
    assert result.exit_code != 0
    assert "rule_kind must be one of" in result.output


# ---------------------------------------------------------------------------
# finalize / promote
# ---------------------------------------------------------------------------


def _author_one(repo: Repository, *, claim_id: str, context: str) -> None:
    assert (
        _invoke(
            repo,
            "propose-claim",
            "demo",
            "--id",
            claim_id,
            "--type",
            "observation",
            "--context",
            context,
            "--statement",
            claim_id,
            "--concept-ref",
            "widget",
            "--page",
            "1",
        ).exit_code
        == 0
    )


def test_finalize_and_promote_success(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_context(repo, "ctx")
    _propose_widget_and_claim(repo)
    _author_one(repo, claim_id="c1", context="ctx")

    assert _invoke(repo, "finalize", "demo").exit_code == 0
    promote = _invoke(repo, "promote", "demo")
    assert promote.exit_code == 0, promote.output
    assert "to master" in promote.output

    fresh = Repository.find(repo.root)
    assert len(list(fresh.families.claim.iter_handles())) == 1


def test_promote_partial_quarantine(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_context(repo, "ctx")
    _propose_widget_and_claim(repo)
    _author_one(repo, claim_id="ok", context="ctx")
    _author_one(repo, claim_id="bad", context="ghost_ctx")

    assert _invoke(repo, "finalize", "demo").exit_code == 0
    promote = _invoke(repo, "promote", "demo")
    assert promote.exit_code == 0, promote.output
    assert "blocked" in promote.output

    fresh = Repository.find(repo.root)
    assert len(list(fresh.families.claim.iter_handles())) == 1


def test_promote_all_blocked_exits_nonzero(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    # No context seeded on master, so the only claim is blocked.
    _propose_widget_and_claim(repo)
    _author_one(repo, claim_id="bad", context="ghost_ctx")

    assert _invoke(repo, "finalize", "demo").exit_code == 0
    promote = _invoke(repo, "promote", "demo")
    assert promote.exit_code != 0
    assert "all 1 claims blocked" in promote.output


def test_promote_requires_finalize(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_context(repo, "ctx")
    _propose_widget_and_claim(repo)
    _author_one(repo, claim_id="c1", context="ctx")
    result = _invoke(repo, "promote", "demo")
    assert result.exit_code != 0
    assert "must be finalized" in result.output


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


def test_status_no_branch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    result = _invoke(repo, "status", "never-made")
    assert result.exit_code == 0, result.output
    assert "No source branch" in result.output


def test_status_clean_source_no_claims(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _init_source(repo)
    result = _invoke(repo, "status", "demo")
    assert result.exit_code == 0, result.output
    assert "No claims" in result.output


def test_status_lists_blocked(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_context(repo, "ctx")
    _propose_widget_and_claim(repo)
    _author_one(repo, claim_id="ok", context="ctx")
    _author_one(repo, claim_id="bad", context="ghost_ctx")

    result = _invoke(repo, "status", "demo")
    assert result.exit_code == 0, result.output
    assert "blocked" in result.output
    assert "ghost_ctx" in result.output


# ---------------------------------------------------------------------------
# sync
# ---------------------------------------------------------------------------


def test_sync_materializes_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "project" / "knowledge")
    _init_source(repo)
    notes = tmp_path / "notes.md"
    notes.write_text("# Notes\n", encoding="utf-8")
    assert _invoke(repo, "write-notes", "demo", "--file", str(notes)).exit_code == 0

    out_dir = tmp_path / "synced"
    result = _invoke(repo, "sync", "demo", "--output-dir", str(out_dir))
    assert result.exit_code == 0, result.output
    assert (out_dir / "notes.md").read_text(encoding="utf-8") == "# Notes\n"
