from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import sqlite3

import pytest
import yaml
from click.testing import CliRunner
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from propstore.sidecar.build import build_sidecar
from propstore.cli import cli
from propstore.repository import Repository
from propstore.source import parameterization_group_merge_preview
from tests.builders import (
    SourceClaimSpec,
    SourceJustificationSpec,
    SourceStanceSpec,
    source_claims_document,
    source_justifications_document,
    source_stances_document,
)
from tests.conftest import normalize_concept_payloads


def _init_source(runner: CliRunner, repo: Repository, name: str) -> None:
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            name,
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            name,
        ],
    )
    assert result.exit_code == 0, result.output


def _seed_master_concept(repo: Repository, *, name: str, form: str = "structural") -> str:
    concept = normalize_concept_payloads(
        [
            {
                "id": name,
                "canonical_name": name,
                "status": "accepted",
                "definition": f"{name} definition",
                "domain": "source",
                "form": form,
            }
        ],
        default_domain="source",
    )[0]
    repo.git.commit_batch(
        adds={
            f"concepts/{name}.yaml": yaml.safe_dump(
                concept,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
        deletes=[],
        message=f"Seed concept {name}",
        branch="master",
    )
    return str(concept["artifact_id"])


def _seed_master_concepts(repo: Repository, concepts: list[dict]) -> list[dict]:
    normalized = normalize_concept_payloads(concepts, default_domain="source")
    adds = {
        f"concepts/{concept['canonical_name']}.yaml": yaml.safe_dump(
            concept,
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8")
        for concept in normalized
    }
    repo.git.commit_batch(
        adds=adds,
        deletes=[],
        message="Seed concepts",
        branch="master",
    )
    return normalized


def test_source_add_claim_rejects_unknown_concept_reference(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _init_source(runner, repo, "demo")

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            source_claims_document(
                [
                    SourceClaimSpec(
                        local_id="claim1",
                        claim_type="parameter",
                        concept="claims_identical",
                        value=1.0,
                        unit="probability",
                        page=1,
                    )
                ]
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "demo",
            "--batch",
            str(claims_file),
        ],
    )
    assert result.exit_code != 0
    assert "unknown concept reference" in result.output


def test_source_add_justification_batch_rewrites_local_claim_ids(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_master_concept(repo, name="claims_identical")
    _init_source(runner, repo, "demo")

    propose = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--name",
            "claims_identical",
            "--definition",
            "A weak identity relation.",
            "--form",
            "structural",
        ],
    )
    assert propose.exit_code == 0, propose.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            source_claims_document(
                [
                    SourceClaimSpec(
                        local_id="claim1",
                        claim_type="observation",
                        statement="A first claim.",
                        concepts=("claims_identical",),
                        page=1,
                    ),
                    SourceClaimSpec(
                        local_id="claim2",
                        claim_type="observation",
                        statement="A second claim.",
                        concepts=("claims_identical",),
                        page=2,
                    ),
                ]
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_claims = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "demo",
            "--batch",
            str(claims_file),
        ],
    )
    assert add_claims.exit_code == 0, add_claims.output

    justifications_file = tmp_path / "justifications.yaml"
    justifications_file.write_text(
        yaml.safe_dump(
            source_justifications_document(
                [
                    SourceJustificationSpec(
                        local_id="just1",
                        conclusion="claim2",
                        premises=("claim1",),
                        rule_kind="empirical_support",
                        page=3,
                    )
                ]
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-justification",
            "demo",
            "--batch",
            str(justifications_file),
        ],
    )
    assert result.exit_code == 0, result.output

    branch_tip = repo.git.branch_sha("source/demo")
    stored_claims = yaml.safe_load(repo.git.read_file("claims.yaml", commit=branch_tip))
    stored_justifications = yaml.safe_load(repo.git.read_file("justifications.yaml", commit=branch_tip))
    claim_ids = {claim["source_local_id"]: claim["artifact_id"] for claim in stored_claims["claims"]}
    justification = stored_justifications["justifications"][0]
    assert justification["conclusion"] == claim_ids["claim2"]
    assert justification["premises"] == [claim_ids["claim1"]]


def test_source_add_stance_batch_rewrites_local_targets_and_preserves_cross_source_refs(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_master_concept(repo, name="claims_identical")
    _init_source(runner, repo, "demo")

    propose = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--name",
            "claims_identical",
            "--definition",
            "A weak identity relation.",
            "--form",
            "structural",
        ],
    )
    assert propose.exit_code == 0, propose.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            source_claims_document(
                [
                    SourceClaimSpec(
                        local_id="claim1",
                        claim_type="observation",
                        statement="A first claim.",
                        concepts=("claims_identical",),
                        page=1,
                    ),
                    SourceClaimSpec(
                        local_id="claim2",
                        claim_type="observation",
                        statement="A second claim.",
                        concepts=("claims_identical",),
                        page=2,
                    ),
                ]
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_claims = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "demo",
            "--batch",
            str(claims_file),
        ],
    )
    assert add_claims.exit_code == 0, add_claims.output

    stances_file = tmp_path / "stances.yaml"
    stances_file.write_text(
        yaml.safe_dump(
            source_stances_document(
                [
                    SourceStanceSpec(
                        source_claim="claim1",
                        target="claim2",
                        stance_type="supports",
                        note="Local support edge.",
                    ),
                    SourceStanceSpec(
                        source_claim="claim2",
                        target="other_source:claim9",
                        stance_type="rebuts",
                        note="Cross-source disagreement.",
                    ),
                ]
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-stance",
            "demo",
            "--batch",
            str(stances_file),
        ],
    )
    assert result.exit_code == 0, result.output

    branch_tip = repo.git.branch_sha("source/demo")
    stored_claims = yaml.safe_load(repo.git.read_file("claims.yaml", commit=branch_tip))
    stored_stances = yaml.safe_load(repo.git.read_file("stances.yaml", commit=branch_tip))
    claim_ids = {claim["source_local_id"]: claim["artifact_id"] for claim in stored_claims["claims"]}
    first, second = stored_stances["stances"]
    assert first["source_claim"] == claim_ids["claim1"]
    assert first["target"] == claim_ids["claim2"]
    assert second["source_claim"] == claim_ids["claim2"]
    assert second["target"] == "other_source:claim9"


def test_source_finalize_blocks_on_unresolved_cross_source_stance_target(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_master_concept(repo, name="claims_identical")
    _init_source(runner, repo, "demo")

    runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--name",
            "claims_identical",
            "--definition",
            "A weak identity relation.",
            "--form",
            "structural",
        ],
    )
    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "observation",
                        "statement": "A first claim.",
                        "concepts": ["claims_identical"],
                        "provenance": {"page": 1},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "demo",
            "--batch",
            str(claims_file),
        ],
    )

    stances_file = tmp_path / "stances.yaml"
    stances_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "stances": [
                    {
                        "source_claim": "claim1",
                        "type": "rebuts",
                        "target": "missing_source:claim404",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-stance",
            "demo",
            "--batch",
            str(stances_file),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "finalize",
            "demo",
        ],
    )
    assert result.exit_code == 0, result.output

    branch_tip = repo.git.branch_sha("source/demo")
    report = yaml.safe_load(repo.git.read_file("merge/finalize/demo.yaml", commit=branch_tip))
    assert report["status"] == "blocked"
    assert report["stance_reference_errors"] == ["missing_source:claim404"]


def test_source_add_stance_auto_finalize_is_advisory_on_validation_issues(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_master_concept(repo, name="claims_identical")
    _init_source(runner, repo, "demo")

    propose = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--name",
            "claims_identical",
            "--definition",
            "A weak identity relation.",
            "--form",
            "structural",
        ],
    )
    assert propose.exit_code == 0, propose.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "observation",
                        "statement": "A first claim.",
                        "concepts": ["claims_identical"],
                        "provenance": {"page": 1},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_claims = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "demo",
            "--batch",
            str(claims_file),
        ],
    )
    assert add_claims.exit_code == 0, add_claims.output

    stances_file = tmp_path / "stances.yaml"
    stances_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "stances": [
                    {
                        "source_claim": "claim1",
                        "type": "rebuts",
                        "target": "missing_source:claim404",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-stance",
            "demo",
            "--batch",
            str(stances_file),
        ],
    )
    assert result.exit_code == 0, result.output

    branch_tip = repo.git.branch_sha("source/demo")
    assert branch_tip is not None
    report = yaml.safe_load(repo.git.read_file("merge/finalize/demo.yaml", commit=branch_tip))
    assert report["status"] == "blocked"
    assert report["stance_reference_errors"] == ["missing_source:claim404"]


def test_source_finalize_reports_parameterization_group_merges(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    seeded = _seed_master_concepts(
        repo,
        [
            {
                "id": "input_a",
                "canonical_name": "input_a",
                "status": "accepted",
                "definition": "Input A.",
                "domain": "source",
                "form": "scalar",
            },
            {
                "id": "derived_a",
                "canonical_name": "derived_a",
                "status": "accepted",
                "definition": "Derived from input A.",
                "domain": "source",
                "form": "scalar",
                "parameterization_relationships": [
                    {"inputs": ["input_a"], "formula": "f(input_a)"}
                ],
            },
            {
                "id": "input_b",
                "canonical_name": "input_b",
                "status": "accepted",
                "definition": "Input B.",
                "domain": "source",
                "form": "scalar",
            },
            {
                "id": "derived_b",
                "canonical_name": "derived_b",
                "status": "accepted",
                "definition": "Derived from input B.",
                "domain": "source",
                "form": "scalar",
                "parameterization_relationships": [
                    {"inputs": ["input_b"], "formula": "g(input_b)"}
                ],
            },
        ],
    )
    artifacts = {concept["canonical_name"]: concept["artifact_id"] for concept in seeded}
    _init_source(runner, repo, "demo")
    repo.git.commit_batch(
        adds={
            "concepts.yaml": yaml.safe_dump(
                {
                    "concepts": [
                        {
                            "local_name": "bridge",
                            "proposed_name": "bridge",
                            "definition": "Connects the two parameter spaces.",
                            "form": "scalar",
                            "status": "proposed",
                            "parameterization_relationships": [
                                {
                                    "inputs": ["derived_a", "derived_b"],
                                    "formula": "h(derived_a, derived_b)",
                                }
                            ],
                        }
                    ]
                },
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
        deletes=[],
        message="Write source concepts",
        branch="source/demo",
    )

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "finalize",
            "demo",
        ],
    )
    assert result.exit_code == 0, result.output

    branch_tip = repo.git.branch_sha("source/demo")
    report = yaml.safe_load(repo.git.read_file("merge/finalize/demo.yaml", commit=branch_tip))
    assert report["status"] == "ready"
    assert len(report["parameterization_group_merges"]) == 1
    merge = report["parameterization_group_merges"][0]
    assert merge["previous_groups"] == [
        sorted([artifacts["derived_a"], artifacts["input_a"]]),
        sorted([artifacts["derived_b"], artifacts["input_b"]]),
    ]
    assert len(merge["introduced_by"]) == 1


@given(master_order=st.permutations([0, 1, 2, 3]), projected_order=st.permutations([0, 1]))
@settings(deadline=None)
def test_parameterization_group_merge_preview_is_order_invariant(
    master_order: tuple[int, ...],
    projected_order: tuple[int, ...],
) -> None:
    master_concepts = normalize_concept_payloads(
        [
            {
                "id": "input_a",
                "canonical_name": "input_a",
                "status": "accepted",
                "definition": "Input A.",
                "domain": "source",
                "form": "scalar",
            },
            {
                "id": "derived_a",
                "canonical_name": "derived_a",
                "status": "accepted",
                "definition": "Derived from input A.",
                "domain": "source",
                "form": "scalar",
                "parameterization_relationships": [
                    {"inputs": ["input_a"], "formula": "f(input_a)"}
                ],
            },
            {
                "id": "input_b",
                "canonical_name": "input_b",
                "status": "accepted",
                "definition": "Input B.",
                "domain": "source",
                "form": "scalar",
            },
            {
                "id": "derived_b",
                "canonical_name": "derived_b",
                "status": "accepted",
                "definition": "Derived from input B.",
                "domain": "source",
                "form": "scalar",
                "parameterization_relationships": [
                    {"inputs": ["input_b"], "formula": "g(input_b)"}
                ],
            },
        ],
        default_domain="source",
    )
    artifacts = {concept["canonical_name"]: concept["artifact_id"] for concept in master_concepts}
    projected_concepts = [
        {
            "artifact_id": "ps:concept:bridge",
            "canonical_name": "bridge",
            "form": "scalar",
            "parameterization_relationships": [
                {
                    "inputs": [artifacts["derived_a"], artifacts["derived_b"]],
                    "formula": "h(derived_a, derived_b)",
                }
            ],
        },
        {
            "artifact_id": "ps:concept:spectator",
            "canonical_name": "spectator",
            "form": "scalar",
            "parameterization_relationships": [],
        },
    ]
    expected = parameterization_group_merge_preview(
        master_concepts,
        projected_concepts,
        parameterized_artifacts={"ps:concept:bridge"},
    )

    reordered_master = [master_concepts[index] for index in master_order]
    reordered_projected = [projected_concepts[index] for index in projected_order]
    actual = parameterization_group_merge_preview(
        reordered_master,
        reordered_projected,
        parameterized_artifacts={"ps:concept:bridge"},
    )
    assert actual == expected


@given(
    source_local_ids=st.lists(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            min_size=1,
            max_size=8,
        ),
        min_size=2,
        max_size=4,
        unique=True,
    )
)
@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_source_add_justification_rewrites_all_local_references(source_local_ids: list[str], tmp_path: Path) -> None:
    case_key = hashlib.sha1("|".join(source_local_ids).encode("utf-8")).hexdigest()[:12]
    repo_root = tmp_path / case_key / "knowledge"
    if repo_root.exists():
        shutil.rmtree(repo_root)
    repo = Repository.init(repo_root)
    runner = CliRunner()
    _seed_master_concept(repo, name="claims_identical")
    _init_source(runner, repo, "demo")
    propose = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--name",
            "claims_identical",
            "--definition",
            "A weak identity relation.",
            "--form",
            "structural",
        ],
    )
    assert propose.exit_code == 0, propose.output

    claims_file = tmp_path / "claims.yaml"
    claims = [
        {
            "id": local_id,
            "type": "observation",
            "statement": f"claim {index}",
            "concepts": ["claims_identical"],
            "provenance": {"page": index + 1},
        }
        for index, local_id in enumerate(source_local_ids)
    ]
    claims_file.write_text(
        yaml.safe_dump({"source": {"paper": "demo"}, "claims": claims}, sort_keys=False),
        encoding="utf-8",
    )
    add_claims = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "demo",
            "--batch",
            str(claims_file),
        ],
    )
    assert add_claims.exit_code == 0, add_claims.output

    justifications_file = tmp_path / "justifications.yaml"
    justifications_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "justifications": [
                    {
                        "id": "just1",
                        "conclusion": source_local_ids[-1],
                        "premises": source_local_ids[:-1],
                        "rule_kind": "empirical_support",
                        "provenance": {"page": 9},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-justification",
            "demo",
            "--batch",
            str(justifications_file),
        ],
    )
    assert result.exit_code == 0, result.output

    branch_tip = repo.git.branch_sha("source/demo")
    stored = yaml.safe_load(repo.git.read_file("justifications.yaml", commit=branch_tip))
    refs = [stored["justifications"][0]["conclusion"], *stored["justifications"][0]["premises"]]
    assert all(ref not in source_local_ids for ref in refs)
    assert all(ref.startswith("ps:claim:") for ref in refs)


def test_source_promote_writes_master_claims_stances_sources_and_justifications(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    canonical_concept_id = _seed_master_concept(repo, name="claims_identical")
    _init_source(runner, repo, "demo")

    propose = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--name",
            "claims_identical",
            "--definition",
            "A weak identity relation.",
            "--form",
            "structural",
        ],
    )
    assert propose.exit_code == 0, propose.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            source_claims_document(
                [
                    SourceClaimSpec(
                        local_id="claim1",
                        claim_type="parameter",
                        concept="claims_identical",
                        value=1.0,
                        unit="probability",
                        page=1,
                    ),
                    SourceClaimSpec(
                        local_id="claim2",
                        claim_type="observation",
                        statement="A second claim.",
                        concepts=("claims_identical",),
                        page=2,
                    ),
                ]
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_claims = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "demo",
            "--batch",
            str(claims_file),
        ],
    )
    assert add_claims.exit_code == 0, add_claims.output

    justifications_file = tmp_path / "justifications.yaml"
    justifications_file.write_text(
        yaml.safe_dump(
            source_justifications_document(
                [
                    SourceJustificationSpec(
                        local_id="just1",
                        conclusion="claim2",
                        premises=("claim1",),
                        rule_kind="empirical_support",
                        page=3,
                    )
                ]
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_justifications = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-justification",
            "demo",
            "--batch",
            str(justifications_file),
        ],
    )
    assert add_justifications.exit_code == 0, add_justifications.output

    stances_file = tmp_path / "stances.yaml"
    stances_file.write_text(
        yaml.safe_dump(
            source_stances_document(
                [
                    SourceStanceSpec(
                        source_claim="claim1",
                        target="claim2",
                        stance_type="supports",
                        note="Local support edge.",
                    )
                ]
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_stances = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-stance",
            "demo",
            "--batch",
            str(stances_file),
        ],
    )
    assert add_stances.exit_code == 0, add_stances.output

    finalize = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "finalize",
            "demo",
        ],
    )
    assert finalize.exit_code == 0, finalize.output

    promote = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "promote",
            "demo",
        ],
    )
    assert promote.exit_code == 0, promote.output

    claims_doc = yaml.safe_load(repo.git.read_file("claims/demo.yaml"))
    promoted_claims = claims_doc["claims"]
    parameter_claim = next(claim for claim in promoted_claims if claim["type"] == "parameter")
    observation_claim = next(claim for claim in promoted_claims if claim["type"] == "observation")
    assert parameter_claim["concept"] == canonical_concept_id
    assert observation_claim["concepts"] == [canonical_concept_id]

    source_claim_id = parameter_claim["artifact_id"]
    stance_file_name = source_claim_id.replace(":", "__") + ".yaml"
    stance_doc = yaml.safe_load(repo.git.read_file(f"stances/{stance_file_name}"))
    assert stance_doc["source_claim"] == source_claim_id
    assert stance_doc["stances"][0]["target"] == observation_claim["artifact_id"]

    justification_doc = yaml.safe_load(repo.git.read_file("justifications/demo.yaml"))
    assert justification_doc["justifications"][0]["conclusion"] == observation_claim["artifact_id"]
    assert justification_doc["justifications"][0]["premises"] == [parameter_claim["artifact_id"]]

    source_doc = yaml.safe_load(repo.git.read_file("sources/demo.yaml"))
    assert source_doc["id"].startswith("tag:")

    build_sidecar(repo.tree(), repo.sidecar_path, force=True, commit_hash=repo.git.head_sha())
    conn = sqlite3.connect(repo.sidecar_path)
    try:
        justification_ids = {
            row[0]
            for row in conn.execute("SELECT id FROM justification").fetchall()
        }
    finally:
        conn.close()
    assert justification_ids == {"just1"}


def test_source_promote_materializes_unique_proposed_concepts(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _init_source(runner, repo, "demo")

    propose = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--name",
            "novel_concept",
            "--definition",
            "A source-local concept that is not yet on master.",
            "--form",
            "structural",
        ],
    )
    assert propose.exit_code == 0, propose.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "observation",
                        "statement": "A first claim.",
                        "concepts": ["novel_concept"],
                        "provenance": {"page": 1},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_claims = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "demo",
            "--batch",
            str(claims_file),
        ],
    )
    assert add_claims.exit_code == 0, add_claims.output

    finalize = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "finalize",
            "demo",
        ],
    )
    assert finalize.exit_code == 0, finalize.output

    promote = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "promote",
            "demo",
        ],
    )
    assert promote.exit_code == 0, promote.output

    concept_doc = yaml.safe_load(repo.git.read_file("concepts/novel_concept.yaml"))
    assert concept_doc["canonical_name"] == "novel_concept"
    assert concept_doc["artifact_id"].startswith("ps:concept:")
    assert concept_doc["version_id"].startswith("sha256:")

    claims_doc = yaml.safe_load(repo.git.read_file("claims/demo.yaml"))
    promoted_claim = claims_doc["claims"][0]
    assert promoted_claim["concepts"] == [concept_doc["artifact_id"]]


def test_source_promote_blocks_on_ambiguous_new_concept_slug_collision(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_master_concept(repo, name="novel_concept")
    _init_source(runner, repo, "demo")

    propose = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--name",
            "novel concept",
            "--definition",
            "Looks new by handle, but collides after slug normalization.",
            "--form",
            "structural",
        ],
    )
    assert propose.exit_code == 0, propose.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "observation",
                        "statement": "A first claim.",
                        "concepts": ["novel concept"],
                        "provenance": {"page": 1},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_claims = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "demo",
            "--batch",
            str(claims_file),
        ],
    )
    assert add_claims.exit_code == 0, add_claims.output

    finalize = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "finalize",
            "demo",
        ],
    )
    assert finalize.exit_code == 0, finalize.output

    promote = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "promote",
            "demo",
        ],
    )
    assert promote.exit_code != 0
    assert "novel concept" in promote.output

