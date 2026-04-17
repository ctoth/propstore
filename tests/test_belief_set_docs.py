from __future__ import annotations

from pathlib import Path


def test_belief_set_revision_docs_exist_and_cite_surfaces() -> None:
    text = Path("docs/belief-set-revision.md").read_text(encoding="utf-8")

    assert "propstore.belief_set" in text
    assert "Alchourron" in text
    assert "Gardenfors" in text
    assert "Darwiche" in text
    assert "Booth" in text
    assert "propstore.support_revision" in text


def test_ic_merge_docs_exist_and_separate_assignment_selection() -> None:
    text = Path("docs/ic-merge.md").read_text(encoding="utf-8")

    assert "propstore.belief_set.ic_merge" in text
    assert "Konieczny" in text
    assert "mu-models" in text
    assert "propstore.world.assignment_selection_merge" in text


def test_af_revision_docs_exist_and_cite_af_surfaces() -> None:
    text = Path("docs/af-revision.md").read_text(encoding="utf-8")

    assert "propstore.belief_set.af_revision" in text
    assert "Baumann" in text
    assert "Diller" in text
    assert "Cayrol" in text
    assert "faithful" in text
