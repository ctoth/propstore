"""Tests for semantic merge classification (Phase 2).

TDD red phase: these tests define the contract for merge_classifier.py
and merge_commit.py. All should FAIL (ImportError) since neither module
exists yet.

Literature grounding:
- Konieczny & Pino Pérez 2002: IC merging postulates IC0-IC4
- Coste-Marquis et al. 2007: PAF three-valued relation, concordance, clash-free
"""
from __future__ import annotations

import yaml
import pytest

from propstore.repo import KnowledgeRepo
from propstore.repo.branch import create_branch, branch_head, merge_base
from propstore.repo.merge_classifier import (
    MergeClassification,
    MergeItem,
    classify_merge,
)
from propstore.repo.merge_commit import create_merge_commit


# ── Helpers ──────────────────────────────────────────────────────────────


def _claim_yaml(claims: list[dict], paper: str = "test_paper") -> bytes:
    """Build a valid claim YAML document from a list of claim dicts."""
    doc = {
        "source": {
            "paper": paper,
            "extraction_model": "test",
            "extraction_date": "2026-01-01",
        },
        "claims": claims,
    }
    return yaml.dump(doc, sort_keys=False).encode()


def _obs_claim(
    cid: str,
    statement: str,
    concepts: list[str],
    *,
    conditions: list[str] | None = None,
) -> dict:
    """Build an observation claim dict."""
    c: dict = {
        "id": cid,
        "type": "observation",
        "statement": statement,
        "concepts": concepts,
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        c["conditions"] = conditions
    return c


def _param_claim(
    cid: str,
    concept: str,
    value: float,
    unit: str = "K",
    *,
    conditions: list[str] | None = None,
) -> dict:
    """Build a parameter claim dict."""
    c: dict = {
        "id": cid,
        "type": "parameter",
        "concept": concept,
        "value": value,
        "unit": unit,
        "concepts": [concept],
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        c["conditions"] = conditions
    return c


@pytest.fixture
def branched_repo(tmp_path):
    """Create a KnowledgeRepo with a base commit and a branch.

    Returns (kr, branch_name, base_sha).
    The base commit contains one claim file under claims/.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    base_claims = [
        _obs_claim("claim1", "Base observation", ["concept_x"]),
    ]
    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml(base_claims)},
        "seed: base claims",
    )

    branch_name = "paper/test"
    create_branch(kr, branch_name, source_commit=base_sha)

    return kr, branch_name, base_sha


# ── Group 1: MergeClassification Enum and MergeItem Type ────────────────


def test_classification_enum_values():
    """MergeClassification has all six values from the proposal.

    Per proposals/semantic-merge-spec.md Phase 2: the enum must
    distinguish identical, compatible, phi_node, conflict, novel_left,
    and novel_right.
    """
    expected = {"IDENTICAL", "COMPATIBLE", "PHI_NODE", "CONFLICT", "NOVEL_LEFT", "NOVEL_RIGHT"}
    actual = {m.name for m in MergeClassification}
    assert actual == expected


def test_merge_item_fields():
    """MergeItem carries classification, claim_id, concept_id, values, and branch names.

    Per proposals/semantic-merge-spec.md Phase 2: MergeItem is a frozen
    dataclass with fields for classification, claim identity, concept
    identity, three-way values (left/right/base), and branch provenance.
    """
    item = MergeItem(
        classification=MergeClassification.IDENTICAL,
        claim_id="claim1",
        concept_id="concept_x",
        left_value="A",
        right_value="A",
        base_value="A",
        left_branch="master",
        right_branch="paper/test",
    )
    assert item.classification == MergeClassification.IDENTICAL
    assert item.claim_id == "claim1"
    assert item.concept_id == "concept_x"
    assert item.left_value == "A"
    assert item.right_value == "A"
    assert item.base_value == "A"
    assert item.left_branch == "master"
    assert item.right_branch == "paper/test"


# ── Group 2: Three-Way Diff Classification ──────────────────────────────


def test_classify_identical_claims(branched_repo):
    """Claims unchanged on both branches classified as IDENTICAL.

    Per Coste-Marquis et al. 2007, claim 8 (p.17): the clash-free part
    is preserved in every merge result. Claims untouched by either branch
    are trivially clash-free and must be classified IDENTICAL.
    """
    kr, branch_name, base_sha = branched_repo

    # Neither side modifies claim1 — just add unrelated files
    kr.commit_files(
        {"claims/left_extra.yaml": _claim_yaml([_obs_claim("claimL", "Left extra", ["concept_a"])])},
        "left: add unrelated claim",
    )
    kr.commit_files(
        {"claims/right_extra.yaml": _claim_yaml([_obs_claim("claimR", "Right extra", ["concept_b"])])},
        "right: add unrelated claim",
        branch=branch_name,
    )

    items = classify_merge(kr, "master", branch_name)
    claim1_items = [i for i in items if i.claim_id == "claim1"]

    assert len(claim1_items) == 1
    assert claim1_items[0].classification == MergeClassification.IDENTICAL


def test_classify_novel_left(branched_repo):
    """Claim added only on left branch classified as NOVEL_LEFT.

    Per Konieczny & Pino Pérez 2002, IC4 (p.4): merging cannot
    completely reject a source that individually satisfies the integrity
    constraint. A novel claim on the left must be acknowledged.
    """
    kr, branch_name, base_sha = branched_repo

    kr.commit_files(
        {"claims/novel.yaml": _claim_yaml([_obs_claim("claim2", "Novel left", ["concept_a"])])},
        "left: add claim2",
    )

    items = classify_merge(kr, "master", branch_name)
    claim2_items = [i for i in items if i.claim_id == "claim2"]

    assert len(claim2_items) == 1
    assert claim2_items[0].classification == MergeClassification.NOVEL_LEFT


def test_classify_novel_right(branched_repo):
    """Claim added only on right branch classified as NOVEL_RIGHT.

    Symmetric to NOVEL_LEFT. Per Konieczny & Pino Pérez 2002, IC4 (p.4):
    neither source may be entirely rejected.
    """
    kr, branch_name, base_sha = branched_repo

    kr.commit_files(
        {"claims/novel.yaml": _claim_yaml([_obs_claim("claim3", "Novel right", ["concept_b"])])},
        "right: add claim3",
        branch=branch_name,
    )

    items = classify_merge(kr, "master", branch_name)
    claim3_items = [i for i in items if i.claim_id == "claim3"]

    assert len(claim3_items) == 1
    assert claim3_items[0].classification == MergeClassification.NOVEL_RIGHT


def test_classify_compatible_additions(branched_repo):
    """Both branches add different non-conflicting claims → COMPATIBLE.

    Per Konieczny & Pino Pérez 2002, IC2 (p.4): when all sources are
    jointly consistent with the integrity constraint, the merge is
    their conjunction (union). Different concepts means no conflict.
    """
    kr, branch_name, base_sha = branched_repo

    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_param_claim("claim2", "concept_a", 100.0)])},
        "left: add claim2 about concept_a",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_param_claim("claim3", "concept_b", 200.0)])},
        "right: add claim3 about concept_b",
        branch=branch_name,
    )

    items = classify_merge(kr, "master", branch_name)
    ids_and_classes = {i.claim_id: i.classification for i in items}

    assert ids_and_classes.get("claim2") == MergeClassification.COMPATIBLE
    assert ids_and_classes.get("claim3") == MergeClassification.COMPATIBLE


def test_classify_phi_node(tmp_path):
    """Same concept modified on both branches under mutually exclusive conditions → PHI_NODE.

    Per Coste-Marquis et al. 2007, claim 1 (p.5): PAF extends Dung AF
    with a three-valued attack relation distinguishing attack, non-attack,
    and ignorance. PHI_NODE represents the ignorance case — both values
    coexist because their conditions never overlap.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    base_claims = [_param_claim("claim1", "concept_x", 250.0)]
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml(base_claims)},
        "seed: base claim",
    )

    branch_name = "paper/phi"
    create_branch(kr, branch_name, source_commit=base_sha)

    # Left: modify claim1 with condition "temp > 300"
    left_claims = [_param_claim("claim1", "concept_x", 300.0, conditions=["temp > 300"])]
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml(left_claims)},
        "left: claim1 value B with high-temp condition",
    )

    # Right: modify claim1 with condition "temp < 200"
    right_claims = [_param_claim("claim1", "concept_x", 150.0, conditions=["temp < 200"])]
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml(right_claims)},
        "right: claim1 value C with low-temp condition",
        branch=branch_name,
    )

    items = classify_merge(kr, "master", branch_name)
    claim1_items = [i for i in items if i.claim_id == "claim1"]

    assert len(claim1_items) == 1
    assert claim1_items[0].classification == MergeClassification.PHI_NODE


def test_classify_conflict(tmp_path):
    """Same concept modified on both branches with no conditions → CONFLICT.

    This is a genuine conflict — both sides modify the same claim with
    overlapping (unconditional) applicability. Per the non-commitment
    principle: both sides are kept with provenance, not resolved.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    base_claims = [_param_claim("claim1", "concept_x", 250.0)]
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml(base_claims)},
        "seed: base claim",
    )

    branch_name = "paper/conflict"
    create_branch(kr, branch_name, source_commit=base_sha)

    # Left: modify claim1 to value B (no conditions)
    left_claims = [_param_claim("claim1", "concept_x", 300.0)]
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml(left_claims)},
        "left: claim1 value B unconditional",
    )

    # Right: modify claim1 to value C (no conditions)
    right_claims = [_param_claim("claim1", "concept_x", 150.0)]
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml(right_claims)},
        "right: claim1 value C unconditional",
        branch=branch_name,
    )

    items = classify_merge(kr, "master", branch_name)
    claim1_items = [i for i in items if i.claim_id == "claim1"]

    assert len(claim1_items) == 1
    assert claim1_items[0].classification == MergeClassification.CONFLICT


def test_classify_deleted_on_one_branch(tmp_path):
    """Claim deleted on one branch but unchanged on the other.

    Per Coste-Marquis et al. 2007, claim 1 (p.5): PAF three-valued
    relation distinguishes 'claim absent from branch' (ignorance) from
    'claim explicitly removed' (non-attack/deletion). The classification
    must reflect the deletion.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    base_claims = [
        _obs_claim("claim1", "Will be deleted on left", ["concept_x"]),
        _obs_claim("claim2", "Stays on both", ["concept_y"]),
    ]
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml(base_claims)},
        "seed: two claims",
    )

    branch_name = "paper/deletion"
    create_branch(kr, branch_name, source_commit=base_sha)

    # Left: remove claim1, keep claim2
    left_claims = [_obs_claim("claim2", "Stays on both", ["concept_y"])]
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml(left_claims)},
        "left: delete claim1",
    )

    # Right: no changes (branch stays at base)

    items = classify_merge(kr, "master", branch_name)
    claim1_items = [i for i in items if i.claim_id == "claim1"]

    assert len(claim1_items) == 1
    # The classification should indicate deletion — the exact enum value
    # is implementation-defined but must NOT be IDENTICAL or COMPATIBLE
    assert claim1_items[0].classification not in (
        MergeClassification.IDENTICAL,
        MergeClassification.COMPATIBLE,
    )


# ── Group 3: Syntax Independence (IC3) ──────────────────────────────────


def test_syntax_independence_claim_order(tmp_path):
    """Reordering claims within a YAML file produces same classification.

    Per Konieczny & Pino Pérez 2002, IC3 (p.4): the merging result is
    syntax-independent. Logically equivalent inputs (same claims in
    different YAML order) must produce equivalent classification output.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    c1 = _obs_claim("claimA", "First", ["concept_a"])
    c2 = _obs_claim("claimB", "Second", ["concept_b"])

    # Base has both claims in order A, B
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([c1, c2])},
        "seed: A then B",
    )

    branch_name = "paper/reorder"
    create_branch(kr, branch_name, source_commit=base_sha)

    # Left: reorder to B, A (same content, different order)
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([c2, c1])},
        "left: reorder to B then A",
    )

    # Right: keep original order
    # (no commit on branch — it stays at base)

    items = classify_merge(kr, "master", branch_name)

    # Both claims should be IDENTICAL — reordering is not a semantic change
    classifications = {i.claim_id: i.classification for i in items}
    assert classifications.get("claimA") == MergeClassification.IDENTICAL
    assert classifications.get("claimB") == MergeClassification.IDENTICAL


def test_syntax_independence_file_name(tmp_path):
    """Renaming claim file (keeping content) produces same classification.

    Per Konieczny & Pino Pérez 2002, IC3 (p.4): syntax independence
    means classification is keyed by claim ID, not filename.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    claims = [_obs_claim("claimA", "Observation A", ["concept_a"])]

    base_sha = kr.commit_files(
        {"claims/original.yaml": _claim_yaml(claims)},
        "seed: original filename",
    )

    branch_name = "paper/rename"
    create_branch(kr, branch_name, source_commit=base_sha)

    # Left: move to a differently-named file
    kr.commit_batch(
        adds={"claims/renamed.yaml": _claim_yaml(claims)},
        deletes=["claims/original.yaml"],
        message="left: rename file",
    )

    # Right: no changes

    items = classify_merge(kr, "master", branch_name)
    claimA_items = [i for i in items if i.claim_id == "claimA"]

    assert len(claimA_items) == 1
    assert claimA_items[0].classification == MergeClassification.IDENTICAL


# ── Group 4: Merge Commit Creation ──────────────────────────────────────


def test_merge_commit_two_parents(tmp_path):
    """Merge commit has two parent SHAs.

    This is the storage representation of IC merging — both sources
    are preserved as parents. Per Konieczny & Pino Pérez 2002: the
    merge operator takes multiple belief bases as input; the two-parent
    commit preserves this multi-source provenance.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )

    branch_name = "paper/merge_test"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_obs_claim("claimL", "Left", ["concept_a"])])},
        "left: add claim",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_obs_claim("claimR", "Right", ["concept_b"])])},
        "right: add claim",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(kr, "master", branch_name)

    # Verify two parents via dulwich
    commit_obj = kr._repo[merge_sha.encode()]
    assert len(commit_obj.parents) == 2


def test_merge_commit_preserves_both_sides(tmp_path):
    """After merge, claims from both branches are readable.

    Per the non-commitment principle: merge never collapses disagreement.
    Both branches' claims must be present in the merged tree.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )

    branch_name = "paper/preserve"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_obs_claim("claimL", "Left only", ["concept_a"])])},
        "left: add claimL",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_obs_claim("claimR", "Right only", ["concept_b"])])},
        "right: add claimR",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(kr, "master", branch_name)

    # Read claims from merge commit — both must be present
    from propstore.tree_reader import GitTreeReader
    from propstore.validate_claims import load_claim_files

    reader = GitTreeReader(kr, commit=merge_sha)
    claim_files = load_claim_files(None, reader=reader)

    all_claim_ids = set()
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            all_claim_ids.add(claim["id"])

    assert "claimL" in all_claim_ids
    assert "claimR" in all_claim_ids


def test_merge_commit_provenance_annotation(tmp_path):
    """Conflicting claims in merge carry branch_origin provenance.

    Per the non-commitment principle: when both branches modify the same
    claim differently (CONFLICT), the merge commit must preserve both
    versions with provenance indicating which branch each came from.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    base_claims = [_param_claim("claim1", "concept_x", 250.0)]
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml(base_claims)},
        "seed",
    )

    branch_name = "paper/provenance"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left: modify claim1",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right: modify claim1",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(kr, "master", branch_name)

    # Read merged tree — both versions of claim1 must be present
    # with branch_origin provenance
    from propstore.tree_reader import GitTreeReader
    from propstore.validate_claims import load_claim_files

    reader = GitTreeReader(kr, commit=merge_sha)
    claim_files = load_claim_files(None, reader=reader)

    claim1_versions = []
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            if claim["id"].startswith("claim1"):
                claim1_versions.append(claim)

    # Must have both versions
    assert len(claim1_versions) >= 2
    # Each must carry branch_origin provenance
    for v in claim1_versions:
        assert "branch_origin" in v.get("provenance", {}), (
            f"Claim version missing branch_origin provenance: {v}"
        )


def test_merge_commit_valid_claims(tmp_path):
    """Merged claim set passes validation.

    Per Konieczny & Pino Pérez 2002, IC0 (p.4): the merged result
    must satisfy the integrity constraint. In propstore the integrity
    constraint is the claim schema — validate_claims() must pass.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )

    branch_name = "paper/valid"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_obs_claim("claimL", "Left", ["concept_a"])])},
        "left: add",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_obs_claim("claimR", "Right", ["concept_b"])])},
        "right: add",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(kr, "master", branch_name)

    from propstore.tree_reader import GitTreeReader
    from propstore.validate_claims import load_claim_files, validate_claims

    reader = GitTreeReader(kr, commit=merge_sha)
    claim_files = load_claim_files(None, reader=reader)

    # validate_claims needs a concept registry — use empty for schema check
    result = validate_claims(claim_files, concept_registry={})
    assert not result.errors, f"Validation errors in merged claims: {result.errors}"


def test_concordance_deterministic(tmp_path):
    """Non-conflicting merges produce unique, deterministic result.

    Per Coste-Marquis et al. 2007, claim 7 (p.15): concordant profiles
    produce a unique merged result regardless of aggregation function.
    When branches make compatible (non-conflicting) changes, repeated
    merges must produce identical trees.
    """
    kr = KnowledgeRepo.init(tmp_path / "knowledge")

    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )

    branch_name = "paper/determinism"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_obs_claim("claimL", "Left", ["concept_a"])])},
        "left: add",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_obs_claim("claimR", "Right", ["concept_b"])])},
        "right: add",
        branch=branch_name,
    )

    # Merge twice — must produce same tree content
    merge_sha_1 = create_merge_commit(kr, "master", branch_name)
    merge_sha_2 = create_merge_commit(kr, "master", branch_name)

    # Tree SHAs must be identical (same input → same output)
    commit_1 = kr._repo[merge_sha_1.encode()]
    commit_2 = kr._repo[merge_sha_2.encode()]
    assert commit_1.tree == commit_2.tree
