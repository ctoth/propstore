"""CLI tests for ``pks verify tree`` (adapter over ``verify_claim_tree``).

The feature-peak ``test_verify_cli`` exercised a per-claim verify surface
(``verify tree <claim_ref>`` with origin + ATMS-label assertions). The rewrite
owner :func:`propstore.verify.verify_claim_tree` is the whole-tree foreign-key
integrity auditor (no claim-ref argument), so these tests target that surface; the
per-claim origin/ATMS cases are deferred (the owner shape does not exist here).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner
from quire.families import BoundFamily

from propstore.cli import cli
from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.repository import Repository


def test_verify_tree_reports_ok_on_clean_tree(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.concept.save(
        "concept:mass", Concept(concept_id="concept:mass", canonical_name="mass"), message="m"
    )
    repo.families.claim.save(
        "cl:ok",
        Claim(claim_id="cl:ok", output_concept="concept:mass", concepts=("concept:mass",)),
        message="author claim",
    )

    result = CliRunner().invoke(cli, ["-C", str(repo.root), "verify", "tree"])
    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["ok"] is True
    assert payload["dangling"] == []


def test_verify_tree_reports_dangling_and_exits_nonzero(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    # Write a claim whose concept reference dangles, bypassing the commit-time FK
    # gate the same way an import/merge can leave a reference unresolved.
    raw: BoundFamily[object, str, Claim] = BoundFamily(
        repo.families.store, Claim.__charter__.family.artifact_family
    )
    raw.save(
        "cl:dangling",
        Claim(claim_id="cl:dangling", output_concept="concept:ghost"),
        message="raw dangling claim",
    )

    result = CliRunner().invoke(cli, ["-C", str(repo.root), "verify", "tree"])
    assert result.exit_code == 2, result.output
    payload = yaml.safe_load(result.output)
    assert payload["ok"] is False
    assert len(payload["dangling"]) == 1
    failure = payload["dangling"][0]
    assert failure["foreign_key"] == "claim_output_concept"
    assert failure["source_id"] == "cl:dangling"
    # Non-commitment: verify reported, it did not drop the broken row.
    assert repo.families.claim.load("cl:dangling") is not None
