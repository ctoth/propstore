from __future__ import annotations

from pathlib import Path

import yaml

from propstore.repository import Repository
from propstore.storage.repository_import import commit_repository_import, plan_repository_import


def test_imported_concept_without_status_defaults_to_proposed(tmp_path: Path) -> None:
    destination = Repository.init(tmp_path / "destination" / "knowledge")
    source = Repository.init(tmp_path / "source" / "knowledge")
    source.git.commit_files(
        {
            "concepts/novel.yaml": yaml.safe_dump(
                {
                    "canonical_name": "novel",
                    "definition": "A source-proposed concept.",
                    "form": "structural",
                },
                sort_keys=False,
            ).encode("utf-8")
        },
        "Seed source concept",
    )

    result = commit_repository_import(
        destination,
        plan_repository_import(destination, source.root.parent),
    )

    imported = yaml.safe_load(
        destination.git.read_file("concepts/novel.yaml", commit=result.commit_sha)
    )
    assert imported["status"] == "proposed"
