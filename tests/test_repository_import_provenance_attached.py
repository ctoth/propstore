from __future__ import annotations

from pathlib import Path

import yaml

from propstore.provenance import read_provenance_note
from propstore.repository import Repository


def _init_project(root: Path) -> Repository:
    return Repository.init(root / "knowledge")


def test_repository_import_attaches_import_provenance_note(tmp_path) -> None:
    from propstore.storage.repository_import import (
        commit_repository_import,
        plan_repository_import,
    )

    destination = _init_project(tmp_path / "dest")
    source = _init_project(tmp_path / "source")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files(
        {
            "claims/source.yaml": yaml.safe_dump(
                {"claims": [{"id": "claim_one", "context": {"id": "ctx"}}]},
                sort_keys=False,
            ).encode()
        },
        "seed source",
    )

    result = commit_repository_import(destination, plan_repository_import(destination, source.root.parent))

    assert destination.git is not None
    provenance = read_provenance_note(destination.git.raw_repo, result.commit_sha)
    assert provenance is not None
    assert provenance.operations == ("repository-import",)
    assert provenance.derived_from == (source.snapshot.head_sha(),)
    assert provenance.witnesses[0].method == "repository-import"
