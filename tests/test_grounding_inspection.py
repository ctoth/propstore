from __future__ import annotations

import pytest

from argumentation.aspic import GroundAtom
from propstore.demo import materialize_reasoning_demo
from propstore.grounding.inspection import (
    GroundingInspectionError,
    inspect_grounding_arguments,
    inspect_grounding_explain,
    inspect_grounding_query,
    inspect_grounding_show,
    inspect_grounding_status,
    parse_query_atom,
)
from propstore.repository import Repository


def test_grounding_status_report_classifies_ready_surface(tmp_path) -> None:
    repo = materialize_reasoning_demo(tmp_path / "knowledge")

    report = inspect_grounding_status(repo)

    assert report.surface_state == "ready"
    assert report.message is None
    assert report.surface.predicate_files == ("reasoning_demo.yaml",)
    assert report.surface.rule_files == ("reasoning_demo.yaml",)
    assert report.facts_count == 1
    assert dict(report.section_counts)["definitely"] == 1
    assert dict(report.section_counts)["defeasibly"] == 2


def test_grounding_show_report_projects_rules_sections_and_arguments(tmp_path) -> None:
    repo = materialize_reasoning_demo(tmp_path / "knowledge")

    show = inspect_grounding_show(repo)
    arguments = inspect_grounding_arguments(repo)

    assert show.facts == ("bird(tweety)",)
    assert [rule.text for rule in show.rules] == [
        "r_flies_from_bird: flies(tweety) -< bird(tweety)"
    ]
    sections = dict(show.sections)
    assert "bird(tweety)" in sections["definitely"]
    assert "flies(tweety)" in sections["defeasibly"]
    assert "bird(tweety) <= fact" in arguments.arguments
    assert "flies(tweety) <= r_flies_from_bird" in arguments.arguments


def test_grounding_explain_report_exposes_gunray_text(tmp_path) -> None:
    repo = materialize_reasoning_demo(tmp_path / "knowledge")

    report = inspect_grounding_explain(repo, "flies(tweety)")

    assert report.atom == GroundAtom(predicate="flies", arguments=("tweety",))
    assert report.matched_sections == ("defeasibly",)
    assert report.explained_atom == report.atom
    assert report.prose == (
        "flies(tweety) is YES.\n"
        "An argument supports flies(tweety) from {bird(tweety)} via r_flies_from_bird."
    )
    assert report.tree is not None
    assert "flies(tweety)" in report.tree
    assert "r_flies_from_bird" in report.tree
    assert report.message is None


def test_grounding_query_report_uses_typed_atom_parser(tmp_path) -> None:
    repo = materialize_reasoning_demo(tmp_path / "knowledge")

    parsed = parse_query_atom('mixed(1, 2.5, true, false, "x", y)')
    result = inspect_grounding_query(repo, "flies(tweety)")
    absent = inspect_grounding_query(repo, "penguin(tweety)")

    assert parsed == GroundAtom(
        predicate="mixed",
        arguments=(1, 2.5, True, False, "x", "y"),
    )
    assert result.atom == GroundAtom(predicate="flies", arguments=("tweety",))
    assert result.matched_sections == ("defeasibly",)
    assert absent.matched_sections == ()


def test_grounding_inspection_rejects_rules_without_predicates(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {"rules/only-rules.yaml": b"rules: []\n"},
        "Seed invalid grounding surface",
    )
    repo.git.sync_worktree()

    status = inspect_grounding_status(repo)

    assert status.surface_state == "invalid"
    assert status.message == "Invalid grounding surface: rules/ has YAML files but predicates/ has none."
    with pytest.raises(GroundingInspectionError, match="rules/ has YAML files but predicates/ has none"):
        inspect_grounding_show(repo)
