"""Phase 9-3: source artifact-code recompute + origin verify + CEL revalidation.

Covers the verify-recompute owner surface (``verify_source_artifact_codes``: it
recomputes each source artifact's content code and verifies the origin ni-URI,
world-free), the world-layer ATMS-label serialization that the same audit surface
composes (the A8 split — no storage→world upward import), and the promote-time
full CEL re-validation that quarantines a semantically invalid promoted claim.
"""

from __future__ import annotations

from pathlib import Path

import msgspec
from condition_ir import KindType

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims import ClaimType
from propstore.families.contexts import Context
from propstore.families.forms import FormDefinition
from propstore.families.registry import SourceRef
from propstore.repository import Repository
from propstore.source import (
    finalize_source_branch,
    init_source_branch,
    promote_source_branch,
    source_branch_name,
)
from propstore.source.claims import commit_source_claim_proposal
from propstore.source.common import load_source_claims_document
from propstore.source.concepts import commit_source_concept_proposal
from propstore.verify import verify_source_artifact_codes
from propstore.world import WorldQuery, serialize_claim_atms_label

_SOURCE = "Verify Demo 2026"


def _new_source(
    tmp_path: Path,
    *,
    origin_type: SourceOriginType = SourceOriginType.MANUAL,
    origin_value: str = "manual",
    content_file: Path | None = None,
) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.form.save(
        "dimensionless",
        FormDefinition(
            name="dimensionless", kind=KindType.QUANTITY, is_dimensionless=True
        ),
        message="seed dimensionless form",
    )
    init_source_branch(
        repo,
        _SOURCE,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=origin_type,
        origin_value=origin_value,
        content_file=content_file,
    )
    return repo


def _seed_context(repo: Repository, context_id: str = "ctx") -> None:
    repo.families.context.save(
        context_id,
        Context(context_id=context_id, name=context_id),
        message=f"seed context {context_id}",
    )


def _author_claim(
    repo: Repository,
    *,
    claim_id: str,
    concept: str = "widget",
    context: str = "ctx",
    statement: str | None = "it holds",
    claim_type: ClaimType = ClaimType.OBSERVATION,
) -> str:
    commit_source_concept_proposal(
        repo, _SOURCE, local_name=concept, definition="a thing", form="dimensionless"
    )
    stored = commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id=claim_id,
        claim_type=claim_type,
        context=context,
        statement=statement,
        concepts=(concept,),
        page=1,
    )
    assert stored.artifact_id is not None
    return stored.artifact_id


def test_verify_source_artifact_codes_ok(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    _author_claim(repo, claim_id="c1")
    finalize_source_branch(repo, _SOURCE)

    report = verify_source_artifact_codes(repo, _SOURCE)

    assert report.ok
    assert any(m.artifact_kind == "source" for m in report.matches)
    assert all(m.status in {"ok", "unstamped"} for m in report.matches)
    # A MANUAL source carries no content_ref, so the origin is honestly unavailable.
    assert report.origin.status == "unavailable"


def test_verify_detects_tampered_artifact_code(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    _author_claim(repo, claim_id="c1")
    finalize_source_branch(repo, _SOURCE)

    claims_doc = load_source_claims_document(repo, _SOURCE)
    assert claims_doc is not None and claims_doc.claims
    tampered_claim = msgspec.structs.replace(
        claims_doc.claims[0], artifact_code="sha256:" + ("0" * 64)
    )
    repo.families.source_claims.save(
        SourceRef(_SOURCE),
        msgspec.structs.replace(claims_doc, claims=(tampered_claim,)),
        message="tamper claim artifact code",
    )

    report = verify_source_artifact_codes(repo, _SOURCE)

    assert not report.ok
    mismatched = [m for m in report.matches if m.status == "mismatch"]
    assert mismatched and all(m.artifact_kind == "claim" for m in mismatched)


def test_verify_origin_matches_retained_content(tmp_path: Path) -> None:
    content_file = tmp_path / "paper.pdf"
    content_file.write_bytes(b"%PDF-demo-bytes\n")
    repo = _new_source(
        tmp_path,
        origin_type=SourceOriginType.FILE,
        origin_value="paper.pdf",
        content_file=content_file,
    )
    _seed_context(repo)
    _author_claim(repo, claim_id="c1")
    finalize_source_branch(repo, _SOURCE)

    # The retained content lives under ../papers/<slug>/ for verify to find it.
    from propstore.source.common import source_paper_slug

    papers_dir = repo.root.parent / "papers" / source_paper_slug(_SOURCE)
    papers_dir.mkdir(parents=True, exist_ok=True)
    (papers_dir / "paper.pdf").write_bytes(content_file.read_bytes())

    report = verify_source_artifact_codes(repo, _SOURCE)

    assert report.origin.status == "matched"
    assert report.origin.path is not None
    assert report.ok


def test_serialize_claim_atms_label_lives_in_world(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    claim_id = _author_claim(repo, claim_id="c1")
    finalize_source_branch(repo, _SOURCE)
    promote_source_branch(repo, _SOURCE)

    with WorldQuery(repo) as world:
        label = serialize_claim_atms_label(world, claim_id)

    # A promoted claim under no assumptions is supported by the empty environment.
    assert label == ((),)


def test_verify_module_has_no_world_import() -> None:
    # A8: the artifact-code recompute is storage-layer and must not reach up into
    # the world layer (one-way layer deps, PLAN.md §12.6).
    import propstore.verify as verify_module

    source = Path(verify_module.__file__).read_text(encoding="utf-8")
    assert "from propstore.world" not in source
    assert "import propstore.world" not in source


def test_promote_quarantines_cel_invalid_claim(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    valid_id = _author_claim(repo, claim_id="ok", statement="it holds")
    # An OBSERVATION with no statement violates its type contract — semantically
    # invalid, but otherwise promotable (resolvable concept, on-master context).
    invalid_id = _author_claim(repo, claim_id="bad", statement=None)
    finalize_source_branch(repo, _SOURCE)

    result = promote_source_branch(repo, _SOURCE)

    # The valid claim promoted; the CEL/contract-invalid one was quarantined...
    assert repo.families.claim.load(valid_id) is not None
    assert repo.families.claim.load(invalid_id) is None
    blocked_ids = {claim.artifact_id for claim in result.blocked_claims}
    assert invalid_id in blocked_ids
    reasons = result.blocked_diagnostics[invalid_id]
    assert any(kind == "claim_validation" for kind, _ in reasons)
    # ...and is still PRESENT on the source branch (quarantine, never drop).
    claims_doc = load_source_claims_document(repo, _SOURCE)
    assert claims_doc is not None
    assert invalid_id in {claim.artifact_id for claim in claims_doc.claims}
    assert repo.require_git().branch_sha(source_branch_name(_SOURCE)) is not None
