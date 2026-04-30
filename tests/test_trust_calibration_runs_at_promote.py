from __future__ import annotations

from pathlib import Path

import yaml

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.registry import SourceRef
from propstore.opinion import Opinion
from propstore.provenance import ProvenanceStatus
from propstore.repository import Repository
from propstore.source import (
    finalize_source_branch,
    init_source_branch,
    promote_source_branch,
    source_branch_name,
)


def _write_matching_rule(repo: Repository) -> None:
    rules_root = repo.root / "rules" / "open-science-collaboration-2015"
    rules_root.mkdir(parents=True)
    (rules_root / "direct-replication.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "osc-direct-replication",
                "effect": "support",
                "conditions": {
                    "domain": "psychology",
                    "replication": "direct",
                },
                "weight": 0.6,
                "base_rate": 0.4,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_trust_calibration_runs_at_promote(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _write_matching_rule(repo)

    init_source_branch(
        repo,
        "direct_replication_source",
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value="direct_replication_source",
    )
    repo.families.source_metadata.save(
        SourceRef("direct_replication_source"),
        {"domain": "psychology", "replication": "direct"},
        message="Write metadata for direct_replication_source",
    )
    finalize_source_branch(repo, "direct_replication_source")

    branch = source_branch_name("direct_replication_source")
    source_head_before_promote = repo.git.branch_sha(branch)
    source_before = yaml.safe_load(repo.git.read_file("source.yaml", commit=source_head_before_promote))
    assert source_before["trust"]["status"] == "defaulted"
    assert "prior_base_rate" not in source_before["trust"]

    promotion = promote_source_branch(repo, "direct_replication_source")

    source_head_after_promote = repo.git.branch_sha(branch)
    source_after = yaml.safe_load(repo.git.read_file("source.yaml", commit=source_head_after_promote))
    assert promotion.commit_sha
    assert source_head_after_promote != source_head_before_promote
    assert source_after["trust"]["status"] == ProvenanceStatus.CALIBRATED.value
    expected_prior = Opinion(0.6, 0.0, 0.4, 0.4)
    assert source_after["trust"]["prior_base_rate"] == {
        "b": expected_prior.b,
        "d": expected_prior.d,
        "u": expected_prior.u,
        "a": expected_prior.a,
    }
    assert source_after["trust"]["derived_from"] == ["osc-direct-replication"]
