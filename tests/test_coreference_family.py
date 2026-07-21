"""Coreference merge-argument proposal family: charter, projection, non-commitment.

Proves the storage half of the render-time coreference path: rival merge-argument
hypotheses are stored side by side on the ``proposal/coreference`` branch and
EVERY one — including two mutually-attacking rivals — reaches the sidecar. Which
(if any) merge survives is a render-time verdict, tested at the app layer.
"""

from __future__ import annotations

from pathlib import Path

from quire.git_store import GitStore
from quire.sqlalchemy_store import readonly_session
from sqlalchemy import select

from propstore.families.coreference import (
    COREFERENCE_PROPOSAL_BRANCH,
    CoreferenceMergeArgumentDoc,
    CoreferenceMergeArgumentRepository,
    coreference_proposal_branch,
    derive_coreference_argument_id,
    stated_provenance,
)
from propstore.families.registry import registered_family_names
from propstore.provenance import ProvenanceStatus
from propstore.repository import Repository


def _rival_docs() -> tuple[CoreferenceMergeArgumentDoc, CoreferenceMergeArgumentDoc]:
    """Two mutually-attacking rival merges over an overlapping claim set."""

    first = CoreferenceMergeArgumentDoc(
        argument_id="cma:one",
        supports=("claim_a", "claim_b"),
        description_claim_ids=("claim_a", "claim_b"),
        attacks=("cma:two",),
        provenance=stated_provenance(),
    )
    second = CoreferenceMergeArgumentDoc(
        argument_id="cma:two",
        supports=("claim_b", "claim_c"),
        description_claim_ids=("claim_b", "claim_c"),
        attacks=("cma:one",),
        provenance=stated_provenance(),
    )
    return first, second


def test_branch_and_id_are_fixed_and_content_derived() -> None:
    assert coreference_proposal_branch() == "proposal/coreference"
    assert COREFERENCE_PROPOSAL_BRANCH.fixed_branch == "proposal/coreference"
    # Content-derived and order-insensitive: same supports -> same id.
    assert derive_coreference_argument_id(("a", "b")) == derive_coreference_argument_id(
        ("b", "a")
    )
    assert derive_coreference_argument_id(("a", "b")) != derive_coreference_argument_id(
        ("a", "c")
    )


def test_family_is_registered() -> None:
    assert "proposal_coreference" in registered_family_names()


def test_standalone_round_trip_and_sidecar_projects_every_rival(tmp_path: Path) -> None:
    repository = CoreferenceMergeArgumentRepository(backend=GitStore.init_memory())
    first, second = _rival_docs()
    repository.author(first, message="propose cma:one")
    repository.author(second, message="propose cma:two")

    # git round-trip
    loaded = repository.get("cma:one")
    assert loaded is not None
    assert loaded.supports == ("claim_a", "claim_b")
    assert loaded.attacks == ("cma:two",)
    assert loaded.provenance is not None
    assert loaded.provenance.status is ProvenanceStatus.STATED

    # sidecar projection: EVERY row, including mutually-attacking rivals (non-commitment)
    sidecar = tmp_path / "coreference.sqlite"
    schema = repository.build_sidecar(sidecar)
    model = schema.model("proposal_coreference")
    with readonly_session(sidecar, schema) as session:
        rows = {row.argument_id: row for row in session.scalars(select(model))}
    assert set(rows) == {"cma:one", "cma:two"}
    assert tuple(rows["cma:one"].attacks) == ("cma:two",)
    assert tuple(rows["cma:two"].attacks) == ("cma:one",)


def test_repo_backed_repository_authors_to_fresh_proposal_branch(tmp_path: Path) -> None:
    """Authoring creates the ``proposal/coreference`` branch on a real repo.

    The proposal references canonical claims that may live on another branch (or
    not be promoted yet); a merge-argument proposal is a heuristic-layer candidate,
    so authoring never requires the supported claims to already resolve.
    """

    repo = Repository.init(tmp_path)
    repository = CoreferenceMergeArgumentRepository(backend=repo.require_git())
    doc = CoreferenceMergeArgumentDoc(
        argument_id="cma:x",
        supports=("claim_a", "claim_b"),
        description_claim_ids=("claim_a", "claim_b"),
        provenance=stated_provenance(),
    )
    repository.author(doc, message="propose cma:x")

    assert repo.require_git().branch_sha(coreference_proposal_branch()) is not None
    ids = {document.argument_id for document in repository.iter_arguments()}
    assert ids == {"cma:x"}
    assert repository.get("cma:x") is not None
