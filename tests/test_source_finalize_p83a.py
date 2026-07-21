"""Phase 8-3a tests: source finalize + micropublication identity + artifact codes.

Ports the behavioural assertions of the reference finalize/micropub suites
(test_finalize_micropub_required, test_micropub_identity_trusty_uri,
test_micropub_identity_not_logical_handle, test_micropub_trusty_verification,
test_artifact_identity_policy) to the rewrite's owner API and charter shapes. The
reference suites drove the CLI; here we call the owner functions directly over a
``Repository.init`` in a tmp dir.

Reference suites that need promote (8-3b), the app/cli render surface, or the
sidecar projection pipeline (Phase 9) are recorded in docs/rewrite/deferred-tests.md.
"""

from __future__ import annotations

from pathlib import Path

import msgspec

from propstore.artifact_codes import (
    claim_artifact_code,
    source_artifact_code,
    stamp_source_artifact_codes,
)
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims import ClaimType
from propstore.families.identity.micropubs import (
    canonical_micropub_payload,
    micropub_artifact_id,
    micropub_version_id,
)
from propstore.families.micropublications import MicropublicationEvidence
from propstore.families.registry import SourceRef
from propstore.families.sources import (
    SourceClaimDocument,
    SourceClaimsDocument,
    SourceJustificationDocument,
    SourceJustificationsDocument,
    SourceMicropublicationDocument,
    SourceProvenanceDocument,
    SourceStanceEntryDocument,
    SourceStancesDocument,
)
from propstore.repository import Repository
from propstore.source.claims import (
    commit_source_claim_proposal,
    normalize_source_claims_payload,
)
from propstore.source.common import (
    init_source_branch,
    load_source_claims_document,
    load_source_document,
    load_source_finalize_report,
    load_source_micropubs_document,
)
from propstore.source.concepts import commit_source_concept_proposal
from propstore.source.finalize import _compose_source_micropubs, finalize_source_branch
from propstore.stances import StanceType
from propstore.uri import verify_ni_uri

_SOURCE = "Demo Paper 2024"


def _new_source(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path)
    init_source_branch(
        repo,
        _SOURCE,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value="manual",
    )
    return repo


def _author_contexted_claim(repo: Repository, handle: str = "c1") -> None:
    commit_source_concept_proposal(
        repo, _SOURCE, local_name="widget", definition="a widget", form="dimensionless"
    )
    commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id=handle,
        claim_type=ClaimType.OBSERVATION,
        context="ctx",
        statement="widgets exist",
        concepts=("widget",),
        page=1,
    )


def _save_claims(repo: Repository, *claims: SourceClaimDocument) -> None:
    normalized, _ = normalize_source_claims_payload(
        SourceClaimsDocument(claims=claims),
        source_uri="tag:test",
        source_namespace="demo_paper_2024",
    )
    repo.families.source_claims.save(
        SourceRef(_SOURCE), normalized, message="inject claims"
    )


# ---------------------------------------------------------------------------
# finalize: micropublication-coverage precondition
# ---------------------------------------------------------------------------


def test_finalize_blocks_claim_without_context_before_writing_micropubs(
    tmp_path: Path,
) -> None:
    repo = _new_source(tmp_path)
    _save_claims(
        repo,
        SourceClaimDocument(
            id="no_context",
            type=ClaimType.OBSERVATION,
            statement="A claim without an explicit context.",
        ),
    )

    finalize_source_branch(repo, _SOURCE)

    report = load_source_finalize_report(repo, _SOURCE)
    assert report is not None
    assert report.status == "blocked"
    assert report.artifact_code_status == "incomplete"
    assert report.micropub_coverage_errors == ("no_context",)
    assert report.micropub_status == "blocked"
    # The micropub file is never written for a blocked finalize.
    assert load_source_micropubs_document(repo, _SOURCE) is None
    # No artifact code is stamped onto the source manifest for a blocked finalize.
    assert load_source_document(repo, _SOURCE).artifact_code is None


def test_finalize_ready_stamps_codes_and_composes_micropubs(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _author_contexted_claim(repo)

    finalize_source_branch(repo, _SOURCE)

    report = load_source_finalize_report(repo, _SOURCE)
    assert report is not None
    assert report.status == "ready"
    assert report.artifact_code_status == "complete"
    assert report.micropub_status == "complete"
    assert report.micropub_coverage_errors == ()

    # Source manifest and every claim carry a content artifact code.
    assert load_source_document(repo, _SOURCE).artifact_code is not None
    claims_doc = load_source_claims_document(repo, _SOURCE)
    assert claims_doc is not None
    (claim,) = claims_doc.claims
    assert claim.artifact_code is not None

    micropubs_doc = load_source_micropubs_document(repo, _SOURCE)
    assert micropubs_doc is not None
    (bundle,) = micropubs_doc.micropubs
    assert bundle.claims == (claim.artifact_id,)
    assert bundle.context_id == "ctx"
    # The bundle id is a trusty URI over its own canonical payload.
    assert bundle.artifact_id == micropub_artifact_id(bundle)
    assert bundle.artifact_id.startswith("ni:///sha-256;")
    assert bundle.version_id == micropub_version_id(bundle)


def test_finalize_with_no_claims_is_ready_but_micropub_empty(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    finalize_source_branch(repo, _SOURCE)

    report = load_source_finalize_report(repo, _SOURCE)
    assert report is not None
    assert report.status == "ready"
    assert report.micropub_status == "empty"
    assert load_source_micropubs_document(repo, _SOURCE) is None


def test_finalize_calibration_falls_back_without_derived_priors(
    tmp_path: Path,
) -> None:
    repo = _new_source(tmp_path)
    finalize_source_branch(repo, _SOURCE)
    report = load_source_finalize_report(repo, _SOURCE)
    assert report is not None
    assert report.calibration.prior_base_rate_status == "fallback"
    assert report.calibration.fallback_to_default_base_rate is True
    assert report.calibration.source_quality_status == "vacuous"


# ---------------------------------------------------------------------------
# finalize: reference-integrity precondition (injected dangling refs)
# ---------------------------------------------------------------------------


def test_finalize_blocks_dangling_justification_reference(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _author_contexted_claim(repo)
    claims_doc = load_source_claims_document(repo, _SOURCE)
    assert claims_doc is not None
    (claim,) = claims_doc.claims
    repo.families.source_justifications.save(
        SourceRef(_SOURCE),
        SourceJustificationsDocument(
            justifications=(
                SourceJustificationDocument(
                    id="j1",
                    conclusion=claim.artifact_id,
                    premises=("ps:claim:ghost",),
                ),
            )
        ),
        message="inject dangling justification",
    )

    finalize_source_branch(repo, _SOURCE)

    report = load_source_finalize_report(repo, _SOURCE)
    assert report is not None
    assert report.status == "blocked"
    assert "ps:claim:ghost" in report.justification_reference_errors


def test_finalize_blocks_unresolved_stance_target(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _author_contexted_claim(repo)
    claims_doc = load_source_claims_document(repo, _SOURCE)
    assert claims_doc is not None
    (claim,) = claims_doc.claims
    repo.families.source_stances.save(
        SourceRef(_SOURCE),
        SourceStancesDocument(
            stances=(
                SourceStanceEntryDocument(
                    source_claim=claim.artifact_id,
                    target="ps:claim:ghost",
                    type=StanceType.REBUTS,
                ),
            )
        ),
        message="inject unresolved stance",
    )

    finalize_source_branch(repo, _SOURCE)

    report = load_source_finalize_report(repo, _SOURCE)
    assert report is not None
    assert report.status == "blocked"
    assert "ps:claim:ghost" in report.stance_reference_errors


# ---------------------------------------------------------------------------
# micropublication content identity (trusty URI)
# ---------------------------------------------------------------------------


def _bundle(
    *,
    claims: tuple[str, ...] = ("ps:claim:alpha",),
    context_id: str = "ctx_alpha",
    source_id: str = "tag:local@propstore,2026:source/demo",
    page: int = 1,
    artifact_id: str = "ps:micropub:old",
    version_id: str = "old-version",
) -> SourceMicropublicationDocument:
    return SourceMicropublicationDocument(
        artifact_id=artifact_id,
        context_id=context_id,
        claims=claims,
        version_id=version_id,
        evidence=(
            MicropublicationEvidence(kind="paper_page", reference=f"demo:{page}"),
        ),
        assumptions=("domain == 'argumentation'",),
        provenance=SourceProvenanceDocument(paper="demo", page=page),
        source=source_id,
    )


def test_micropub_id_is_trusty_uri_over_canonical_payload() -> None:
    left = _bundle()
    # Same semantic content, different recursive identity fields.
    right = _bundle(artifact_id="ps:micropub:different", version_id="different-version")
    assert canonical_micropub_payload(left) == canonical_micropub_payload(right)
    assert micropub_artifact_id(left) == micropub_artifact_id(right)
    assert micropub_artifact_id(left).startswith("ni:///sha-256;")

    changed = _bundle(page=2)
    assert micropub_artifact_id(changed) != micropub_artifact_id(left)


def test_micropub_canonical_payload_ignores_claim_order() -> None:
    left = _bundle(claims=("ps:claim:a", "ps:claim:b", "ps:claim:c"))
    right = _bundle(claims=("ps:claim:c", "ps:claim:a", "ps:claim:b"))
    assert canonical_micropub_payload(left) == canonical_micropub_payload(right)
    assert micropub_artifact_id(left) == micropub_artifact_id(right)


def test_micropub_trusty_uri_verifies_exact_canonical_bytes() -> None:
    document = _bundle()
    uri = micropub_artifact_id(document)
    payload = canonical_micropub_payload(document)
    assert verify_ni_uri(uri, payload)
    assert not verify_ni_uri(uri, payload + b"\n")


def test_compose_source_micropubs_assigns_id_from_payload() -> None:
    claims_doc = SourceClaimsDocument(
        claims=(
            SourceClaimDocument(
                artifact_id="ps:claim:alpha",
                context="ctx_alpha",
                conditions=("domain == 'argumentation'",),
                provenance=SourceProvenanceDocument(paper="demo", page=1),
            ),
        )
    )
    micropubs_doc = _compose_source_micropubs(
        source_id="tag:local@propstore,2026:source/demo",
        source_slug="demo",
        claims_doc=claims_doc,
    )
    assert micropubs_doc is not None
    bundle = micropubs_doc.micropubs[0]
    assert bundle.artifact_id == micropub_artifact_id(bundle)
    assert bundle.artifact_id.startswith("ni:///sha-256;")


def test_compose_source_micropubs_skips_claims_without_artifact_id() -> None:
    claims_doc = SourceClaimsDocument(
        claims=(SourceClaimDocument(id="unstamped", context="ctx"),)
    )
    assert (
        _compose_source_micropubs(
            source_id="tag:test", source_slug="demo", claims_doc=claims_doc
        )
        is None
    )


# ---------------------------------------------------------------------------
# artifact codes
# ---------------------------------------------------------------------------


def test_stamp_source_artifact_codes_is_deterministic_and_content_sensitive(
    tmp_path: Path,
) -> None:
    repo = _new_source(tmp_path)
    _author_contexted_claim(repo)
    source_doc = load_source_document(repo, _SOURCE)
    claims_doc = load_source_claims_document(repo, _SOURCE)

    first_source, first_claims, _, _ = stamp_source_artifact_codes(
        source_doc, claims_doc, None, None
    )
    second_source, second_claims, _, _ = stamp_source_artifact_codes(
        source_doc, claims_doc, None, None
    )
    assert first_source.artifact_code == second_source.artifact_code
    assert first_source.artifact_code is not None
    assert first_claims is not None and second_claims is not None
    assert first_claims.claims[0].artifact_code == second_claims.claims[0].artifact_code
    assert first_claims.claims[0].artifact_code is not None

    # Editing claim content changes its code (and not the source code).
    edited_claims = msgspec.structs.replace(
        claims_doc,
        claims=(msgspec.structs.replace(claims_doc.claims[0], statement="edited"),),
    )
    _, edited_out, _, _ = stamp_source_artifact_codes(
        source_doc, edited_claims, None, None
    )
    assert edited_out is not None
    assert edited_out.claims[0].artifact_code != first_claims.claims[0].artifact_code


def test_claim_artifact_code_folds_in_relation_codes() -> None:
    claim = SourceClaimDocument(
        artifact_id="ps:claim:alpha", context="ctx", statement="x"
    )
    base = claim_artifact_code(
        claim, source_code="s", justification_codes=(), stance_codes=()
    )
    with_just = claim_artifact_code(
        claim, source_code="s", justification_codes=("j1",), stance_codes=()
    )
    with_stance = claim_artifact_code(
        claim, source_code="s", justification_codes=(), stance_codes=("st1",)
    )
    assert base != with_just
    assert base != with_stance
    assert with_just != with_stance


def test_source_artifact_code_excludes_recursive_code_field() -> None:
    repo_doc = SourceClaimDocument(
        artifact_id="ps:claim:alpha", context="ctx", statement="x"
    )
    pre = claim_artifact_code(
        repo_doc, source_code="s", justification_codes=(), stance_codes=()
    )
    stamped = msgspec.structs.replace(repo_doc, artifact_code="anything")
    post = claim_artifact_code(
        stamped, source_code="s", justification_codes=(), stance_codes=()
    )
    assert pre == post


def test_source_artifact_code_stable_across_manifest_identity(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    source_doc = load_source_document(repo, _SOURCE)
    assert source_artifact_code(source_doc) == source_artifact_code(source_doc)
