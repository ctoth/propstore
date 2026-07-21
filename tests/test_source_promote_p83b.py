"""Phase 8-3b tests: source-branch promotion + trust calibration.

Ports the behavioural assertions of the reference promote/trust suites
(test_promote_atomicity, test_promote_claim_immutability,
test_promote_writes_provenance_note, test_source_promote_dangling_refs,
test_trust_calibration_runs_at_promote, test_source_trust) to the rewrite's owner
API and canonical charter shapes, and adds the two store-write-boundary invariant
tests the non-commitment discipline turns on:

* ``test_blocked_claim_is_quarantined_not_dropped`` — a claim that cannot promote
  cleanly stays on the source branch (present) and is surfaced; it is never
  dropped (Z1).
* ``test_low_trust_claim_still_promotes`` — a low-trust source still promotes its
  claims, carrying its honest calibrated provenance; calibration stamps, never
  gates (Z2).

Reference suites needing the derived-store/projection pipeline (Phase 9), the CLI
render surface, proposals (8-4), or import (8-5) are recorded in
docs/rewrite/deferred-tests.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from condition_ir import KindType

from propstore.compiler.context import build_compilation_context_from_repo
from propstore.core.scalars import ScalarValue
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims import Claim, ClaimStatus, ClaimType
from propstore.families.contexts import Context
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.families.sources import SourceConceptFormParametersDocument
from propstore.provenance import ProvenanceStatus, read_provenance_note
from propstore.repository import Repository
from propstore.source import (
    finalize_source_branch,
    init_source_branch,
    promote_source_branch,
    source_branch_name,
)
from propstore.source.common import (
    commit_source_metadata,
    load_source_claims_document,
)
from propstore.source.claims import commit_source_claim_proposal
from propstore.source.concepts import commit_source_concept_proposal
from propstore.world import WorldQuery

_SOURCE = "Demo Paper 2024"


def _new_source(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path)
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
        origin_type=SourceOriginType.MANUAL,
        origin_value="manual",
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
) -> str:
    commit_source_concept_proposal(
        repo, _SOURCE, local_name=concept, definition="a thing", form="dimensionless"
    )
    stored = commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id=claim_id,
        claim_type=ClaimType.OBSERVATION,
        context=context,
        statement="it holds",
        concepts=(concept,),
        page=1,
    )
    assert stored.artifact_id is not None
    return stored.artifact_id


def _write_metadata(repo: Repository, payload: dict[str, str]) -> None:
    metadata_file = repo.root / "metadata.json"
    metadata_file.write_text(json.dumps(payload), encoding="utf-8")
    commit_source_metadata(repo, _SOURCE, metadata_file)


def _write_rule(repo: Repository, rule: dict[str, object]) -> None:
    rules_dir = repo.root / "rules" / "demo"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / "rule.yaml").write_text(yaml.safe_dump(rule), encoding="utf-8")


def _source_trust(repo: Repository) -> dict[str, object]:
    branch = source_branch_name(_SOURCE)
    tip = repo.require_git().branch_sha(branch)
    assert tip is not None
    document = yaml.safe_load(repo.require_git().read_file("source.yaml", commit=tip))
    # ``trust`` is a json-blob charter field, so it serializes as a JSON string.
    trust = json.loads(document["trust"])
    assert isinstance(trust, dict)
    return trust


# ---------------------------------------------------------------------------
# finalize precondition
# ---------------------------------------------------------------------------


def test_promote_requires_finalize(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    _author_claim(repo, claim_id="c1")
    with pytest.raises(ValueError, match="must be finalized"):
        promote_source_branch(repo, _SOURCE)


# ---------------------------------------------------------------------------
# atomic master write + immutable rebuild
# ---------------------------------------------------------------------------


def test_promote_writes_valid_claims_and_concepts_to_master(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    artifact_a = _author_claim(repo, claim_id="c1")
    finalize_source_branch(repo, _SOURCE)

    result = promote_source_branch(repo, _SOURCE)

    assert result.commit_sha
    assert result.blocked_claims == ()
    promoted = repo.families.claim.load(artifact_a)
    assert promoted is not None
    # The minted canonical concept is on master in the same promotion.
    assert len(promoted.concepts) == 1
    assert repo.families.concept.load(promoted.concepts[0]) is not None


@pytest.mark.parametrize(
    ("value", "expected_type"),
    (
        ("red", str),
        (True, bool),
        (7, int),
        (7.5, float),
        (None, type(None)),
    ),
)
def test_claim_scalar_preserves_type_from_source_through_world_query(
    tmp_path: Path,
    value: ScalarValue | None,
    expected_type: type[object],
) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    commit_source_concept_proposal(
        repo,
        _SOURCE,
        local_name="widget",
        definition="a thing",
        form="dimensionless",
    )
    stored = commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id="c1",
        claim_type=ClaimType.OBSERVATION,
        context="ctx",
        statement="it holds",
        concepts=("widget",),
        value=value,
    )
    assert stored.artifact_id is not None
    source_document = load_source_claims_document(repo, _SOURCE)
    assert source_document is not None
    assert source_document.claims[0].value == value
    assert type(source_document.claims[0].value) is expected_type

    finalize_source_branch(repo, _SOURCE)
    promote_source_branch(repo, _SOURCE)

    promoted = repo.families.claim.load(stored.artifact_id)
    assert promoted is not None
    assert promoted.value == value
    assert type(promoted.value) is expected_type
    with WorldQuery(repo) as world:
        projected = world.get_claim(stored.artifact_id)
    assert projected is not None
    assert projected.value == value
    assert type(projected.value) is expected_type
    assert projected.claim_id == stored.artifact_id


def test_promoted_claim_is_immutable_rebuild_with_lowered_concept(
    tmp_path: Path,
) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    artifact_a = _author_claim(repo, claim_id="c1", concept="widget")
    finalize_source_branch(repo, _SOURCE)
    promote_source_branch(repo, _SOURCE)

    promoted = repo.families.claim.load(artifact_a)
    assert isinstance(promoted, Claim)
    # Identity is the source claim's already-derived artifact id (no new mint).
    assert promoted.claim_id == artifact_a
    assert promoted.status is ClaimStatus.AUTHORED
    # The source-local handle "widget" was lowered to a canonical concept FK.
    assert len(promoted.concepts) == 1
    assert promoted.concepts[0].startswith("ps:concept:")
    assert promoted.concepts[0] != "widget"
    assert repo.families.concept.load(promoted.concepts[0]) is not None
    assert promoted.context_id == "ctx"


def test_promoted_concepts_preserve_form_and_category_semantics(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    repo.families.form.save(
        "category",
        FormDefinition(name="category", kind=KindType.CATEGORY),
        message="seed category form",
    )
    repo.families.form.save(
        "quantity",
        FormDefinition(name="quantity", kind=KindType.QUANTITY, is_dimensionless=True),
        message="seed quantity form",
    )
    commit_source_concept_proposal(
        repo,
        _SOURCE,
        local_name="severity",
        definition="An ordered severity label.",
        form="category",
        form_parameters=SourceConceptFormParametersDocument(
            values=("low", "medium", "high"),
            extensible=False,
        ),
    )
    commit_source_concept_proposal(
        repo,
        _SOURCE,
        local_name="score",
        definition="A numeric score.",
        form="quantity",
    )
    finalize_source_branch(repo, _SOURCE)

    promote_source_branch(repo, _SOURCE)

    promoted = {
        handle.document.canonical_name: handle.document
        for handle in repo.families.concept.iter_handles()
        if isinstance(handle.document, Concept)
    }
    severity = promoted["severity"]
    reloaded_severity = repo.families.concept.load(severity.concept_id)
    assert reloaded_severity == severity
    assert reloaded_severity is not None
    assert reloaded_severity.lexical_entry is not None
    assert reloaded_severity.lexical_entry.physical_dimension_form == "category"
    assert reloaded_severity.category_values == ("low", "medium", "high")
    assert reloaded_severity.category_extensible is False

    score = promoted["score"]
    reloaded_score = repo.families.concept.load(score.concept_id)
    assert reloaded_score == score
    assert reloaded_score is not None
    assert reloaded_score.lexical_entry is not None
    assert reloaded_score.lexical_entry.physical_dimension_form == "quantity"
    assert reloaded_score.category_values == ()
    assert reloaded_score.category_extensible is True

    compiler_info = build_compilation_context_from_repo(repo).condition_registry[
        "severity"
    ]
    with WorldQuery(repo) as world:
        world_info = world.condition_solver().registry["severity"]
    assert compiler_info == world_info
    assert compiler_info.id == reloaded_severity.concept_id
    assert compiler_info.category_values == list(reloaded_severity.category_values)
    assert compiler_info.category_extensible is reloaded_severity.category_extensible


def test_promotion_rejects_category_metadata_on_quantity_without_claims(
    tmp_path: Path,
) -> None:
    repo = _new_source(tmp_path)
    commit_source_concept_proposal(
        repo,
        _SOURCE,
        local_name="invalid_quantity",
        definition="A quantity with category metadata.",
        form="dimensionless",
        form_parameters=SourceConceptFormParametersDocument(values=("low", "high")),
    )
    finalize_source_branch(repo, _SOURCE)

    with pytest.raises(ValueError, match="concept validation failed during promotion"):
        promote_source_branch(repo, _SOURCE)


# ---------------------------------------------------------------------------
# provenance note carrier
# ---------------------------------------------------------------------------


def test_promote_writes_provenance_note(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    _author_claim(repo, claim_id="c1")
    finalize_source_branch(repo, _SOURCE)

    result = promote_source_branch(repo, _SOURCE)

    provenance = read_provenance_note(repo.require_git().raw_repo, result.commit_sha)
    assert provenance is not None
    assert provenance.status is ProvenanceStatus.STATED
    assert provenance.operations == ("promote",)
    assert provenance.graph_name == f"urn:propstore:source-promote:{result.commit_sha}"


# ---------------------------------------------------------------------------
# Z1 — quarantine, never drop
# ---------------------------------------------------------------------------


def test_blocked_claim_is_quarantined_not_dropped(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo, "ctx")
    valid_id = _author_claim(repo, claim_id="ok", context="ctx")
    # A claim whose context is not on master cannot promote cleanly.
    blocked_id = _author_claim(repo, claim_id="bad", context="ghost_ctx")
    finalize_source_branch(repo, _SOURCE)

    result = promote_source_branch(repo, _SOURCE)

    # The valid claim promoted; the blocked one did NOT reach master...
    assert repo.families.claim.load(valid_id) is not None
    assert repo.families.claim.load(blocked_id) is None
    # ...it is surfaced with its reason...
    blocked_ids = {claim.artifact_id for claim in result.blocked_claims}
    assert blocked_id in blocked_ids
    assert result.blocked_diagnostics[blocked_id]
    # ...and is still PRESENT on the source branch (never dropped).
    claims_doc = load_source_claims_document(repo, _SOURCE)
    assert claims_doc is not None
    assert blocked_id in {claim.artifact_id for claim in claims_doc.claims}


def test_promote_aborts_only_when_every_claim_is_blocked(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    # No context seeded on master, so the only claim is blocked.
    _author_claim(repo, claim_id="bad", context="ghost_ctx")
    finalize_source_branch(repo, _SOURCE)
    with pytest.raises(ValueError, match="all 1 claims blocked"):
        promote_source_branch(repo, _SOURCE)


# ---------------------------------------------------------------------------
# Z2 — calibration stamps, never gates
# ---------------------------------------------------------------------------


def test_trust_calibration_runs_at_promote(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    _author_claim(repo, claim_id="c1")
    _write_metadata(repo, {"domain": "psychology", "replication": "direct"})
    _write_rule(
        repo,
        {
            "id": "osc-direct-replication",
            "effect": "support",
            "conditions": {"domain": "psychology", "replication": "direct"},
            "weight": 0.6,
            "base_rate": 0.4,
        },
    )
    finalize_source_branch(repo, _SOURCE)
    assert _source_trust(repo)["status"] == ProvenanceStatus.DEFAULTED.value

    promote_source_branch(repo, _SOURCE)

    trust = _source_trust(repo)
    assert trust["status"] == ProvenanceStatus.CALIBRATED.value
    assert trust["prior_base_rate"] == {"b": 0.6, "d": 0.0, "u": 0.4, "a": 0.4}
    assert trust["derived_from"] == ["osc-direct-replication"]


def test_low_trust_claim_still_promotes_with_calibrated_provenance(
    tmp_path: Path,
) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    artifact_a = _author_claim(repo, claim_id="c1")
    _write_metadata(repo, {"domain": "psychology"})
    # An attack rule yields high disbelief: a LOW-trust prior.
    _write_rule(
        repo,
        {
            "id": "weak-source",
            "effect": "attack",
            "conditions": {"domain": "psychology"},
            "weight": 0.7,
            "base_rate": 0.3,
        },
    )
    finalize_source_branch(repo, _SOURCE)

    result = promote_source_branch(repo, _SOURCE)

    # The low-trust claim STILL promoted (calibration did not gate it)...
    assert repo.families.claim.load(artifact_a) is not None
    assert result.blocked_claims == ()
    # ...and the honest calibrated low-trust prior is stamped on the source.
    trust = _source_trust(repo)
    assert trust["status"] == ProvenanceStatus.CALIBRATED.value
    assert trust["prior_base_rate"] == {
        "b": 0.0,
        "d": 0.7,
        "u": 0.30000000000000004,
        "a": 0.3,
    }


def test_promote_without_matching_rule_leaves_defaulted_trust(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_context(repo)
    artifact_a = _author_claim(repo, claim_id="c1")
    _write_metadata(repo, {"domain": "physics"})
    finalize_source_branch(repo, _SOURCE)

    promote_source_branch(repo, _SOURCE)

    # No rule fired: claim still promoted, trust honestly defaulted (no prior).
    assert repo.families.claim.load(artifact_a) is not None
    trust = _source_trust(repo)
    assert trust["status"] == ProvenanceStatus.DEFAULTED.value
    assert "prior_base_rate" not in trust
