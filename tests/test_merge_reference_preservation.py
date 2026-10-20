"""The branch-instance maps of a merge must preserve FK incidence.

Schultz/Wisnesky §§3.2,4.1,6.1 require h(f(x)) = f(h(x)). Keeping a
single edge while mapping its target to distinct rival versions cannot satisfy
that equation. Until a canonical transport is supplied, reject before moving
the target ref; neither dropping the edge nor a Cartesian expansion is valid.
"""

from pathlib import Path

import pytest

from propstore.families.contexts import Context
from propstore.families.justifications import Justification
from propstore.families.micropublications import Micropublication
from propstore.families.relations import Stance
from propstore.merge.merge_commit import MergeReferenceConflict, create_merge_commit
from propstore.stances import StanceType
from propstore.verify import verify_claim_tree
from tests.merge_commit_helpers import author_concept, author_param_claim, init_repo


@pytest.mark.parametrize(
    ("family", "source", "target", "expected_fk"),
    [
        ("stance", "c", "s", "stance_source_claim"),
        ("stance", "s", "c", "stance_target_claim"),
        ("justification", "c", "s", "justification_premises"),
        ("justification", "s", "c", "justification_conclusion"),
        ("micropublication", "s", "c", "micropublication_claims"),
    ],
)
@pytest.mark.parametrize("existing_target", [False, True])
def test_reference_without_a_preserving_transport_cannot_advance_target(
    tmp_path: Path,
    family: str,
    source: str,
    target: str,
    expected_fk: str,
    existing_target: bool,
) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    author_param_claim(repo, "s", "x", 100.0)
    if family == "stance":
        document = Stance(
            stance_id="edge", source_claim_id=source,
            target_claim_id=target, stance_type=StanceType.SUPPORTS,
        )
        repo.families.stance.save("edge", document, message="support")
    elif family == "justification":
        document = Justification(
            justification_id="edge", conclusion=target, premises=(source,),
        )
        repo.families.justification.save("edge", document, message="justification")
    else:
        repo.families.context.save(
            "ctx", Context(context_id="ctx", name="ctx"), message="context"
        )
        document = Micropublication(
            artifact_id="edge", context_id="ctx", claims=(target,),
            source="urn:source:paper",
        )
        repo.families.micropublication.save("edge", document, message="bundle")

    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    author_param_claim(repo, "c", "x", 300.0)
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    left, right = git.branch_sha("master"), git.branch_sha("peer")
    assert left is not None and right is not None
    assert verify_claim_tree(repo, commit=left).ok
    assert verify_claim_tree(repo, commit=right).ok
    if existing_target:
        git.create_branch("result", source_commit=left)
    before = git.branch_sha("result")

    with pytest.raises(MergeReferenceConflict) as caught:
        create_merge_commit(repo, "master", "peer", target_branch="result")

    assert caught.value.source_commit == left
    assert caught.value.source_family == family
    assert caught.value.foreign_key.name == expected_fk
    assert "'c' does not resolve" in str(caught.value)
    assert git.branch_sha("result") == before
    assert git.branch_sha("master") == left
    assert git.branch_sha("peer") == right
    # The rejected transformation never mutates either original evidence row.
    for commit in (left, right):
        assert repo.families.by_name(family).require("edge", commit=commit) == document


def test_reference_to_one_surviving_claim_identity_still_merges(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    repo.families.stance.save(
        "edge", Stance(stance_id="edge", source_claim_id="c", target_claim_id="c"),
        message="self relation",
    )
    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    author_param_claim(repo, "c", "x", 300.0)
    author_param_claim(repo, "c", "x", 300.0, branch="peer")
    merged = create_merge_commit(repo, "master", "peer", target_branch="result")
    assert verify_claim_tree(repo, commit=merged).ok
    assert repo.families.claim.require("c", commit=merged).value == 300.0
    assert repo.families.stance.require("edge", commit=merged).target_claim_id == "c"
