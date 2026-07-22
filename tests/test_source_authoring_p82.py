"""Phase 8-2 source-branch authoring tests (owner-API over a real Repository).

These port the behavioural assertions of the reference source-authoring tests
(test_source_propose / test_source_claims / test_source_relations /
test_source_cannot_mint_canonical_ids / test_source_claim_concept_rewrite /
test_local_handle_collision_blocks_commit) to the rewrite's owner-layer API and
charter shapes. The reference suites drove the CLI; here we call the owner
functions directly over ``Repository.init`` in a tmp dir.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from quire.references import AmbiguousReferenceError

from propstore.canonical_namespaces import ReservedNamespaceViolation
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims import ClaimType
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.families.registry import SourceRef
from propstore.families.sources import (
    SourceClaimDocument,
    SourceClaimsDocument,
    SourceConceptFormParametersDocument,
)
from propstore.repository import Repository
from propstore.source.claim_concepts import rewrite_claim_concept_refs
from propstore.source.claims import (
    commit_source_claim_proposal,
    normalize_source_claims_payload,
)
from propstore.source.common import (
    init_source_branch,
    load_source_document,
    source_branch_name,
)
from propstore.source.concepts import commit_source_concept_proposal
from propstore.source.reference_indexes import (
    resolve_source_or_primary_claim_id,
    source_claim_index,
)
from propstore.source.relations import (
    commit_source_justification_proposal,
    commit_source_stance_proposal,
)
from propstore.stances import StanceType

from condition_ir import KindType

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


# ---------------------------------------------------------------------------
# init + manifest
# ---------------------------------------------------------------------------


def test_init_source_branch_creates_branch_and_manifest(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    branch = source_branch_name(_SOURCE)
    assert repo.require_git().branch_sha(branch) is not None
    manifest = load_source_document(repo, _SOURCE)
    assert manifest.kind is SourceKind.ACADEMIC_PAPER
    assert manifest.id.startswith("tag:")
    assert manifest.metadata is not None and manifest.metadata.name == "Demo_Paper_2024"


def test_load_source_document_missing_branch_raises(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    with pytest.raises(ValueError, match="does not exist"):
        load_source_document(repo, "never-initialized")


# ---------------------------------------------------------------------------
# concept proposals
# ---------------------------------------------------------------------------


def test_concept_proposal_is_stored_as_proposed(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    entry = commit_source_concept_proposal(
        repo, _SOURCE, local_name="widget", definition="a widget", form="dimensionless"
    )
    assert entry.local_name == "widget"
    assert entry.status == "proposed"
    assert entry.registry_match is None


def test_concept_proposal_rejects_non_cel_proposed_name(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)

    with pytest.raises(ValueError, match="proposed_name.*is not a CEL identifier"):
        commit_source_concept_proposal(
            repo,
            _SOURCE,
            local_name="Draft Concept",
            definition="a draft concept",
            form="dimensionless",
        )


def test_concept_proposal_rejects_unknown_form_when_forms_exist(
    tmp_path: Path,
) -> None:
    repo = _new_source(tmp_path)
    repo.families.form.save(
        "dimensionless",
        FormDefinition(
            name="dimensionless", kind=KindType.QUANTITY, is_dimensionless=True
        ),
        message="seed form",
    )
    with pytest.raises(ValueError, match="Unknown form"):
        commit_source_concept_proposal(
            repo, _SOURCE, local_name="w", definition="d", form="bogus"
        )


def test_concept_proposal_links_to_master_concept(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    repo.families.concept.save(
        "ps:concept:widget",
        Concept(concept_id="ps:concept:widget", canonical_name="widget"),
        message="seed concept",
    )
    entry = commit_source_concept_proposal(
        repo, _SOURCE, local_name="widget", definition="a widget", form="dimensionless"
    )
    assert entry.status == "linked"
    assert entry.registry_match is not None
    assert entry.registry_match.artifact_id == "ps:concept:widget"


# ---------------------------------------------------------------------------
# claim proposals + identity stamping
# ---------------------------------------------------------------------------


def test_claim_proposal_stamps_canonical_identity(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    commit_source_concept_proposal(
        repo, _SOURCE, local_name="widget", definition="a widget", form="dimensionless"
    )
    claim = commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id="c1",
        claim_type=ClaimType.OBSERVATION,
        context="ctx",
        statement="widgets exist",
        concepts=("widget",),
    )
    assert claim.artifact_id is not None and claim.artifact_id.startswith("ps:claim:")
    assert claim.version_id is not None and claim.version_id.startswith("sha256:")
    assert claim.source_local_id == "c1"
    namespaces = {logical.namespace for logical in claim.logical_ids}
    assert namespaces == {"Demo_Paper_2024"}
    values = {logical.value for logical in claim.logical_ids}
    assert "c1" in values  # the source-local handle survives as a logical id


def test_claim_proposal_unknown_concept_is_rejected(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    with pytest.raises(ValueError, match="unknown concept reference"):
        commit_source_claim_proposal(
            repo,
            _SOURCE,
            claim_id="c1",
            claim_type=ClaimType.OBSERVATION,
            context="ctx",
            statement="about a thing",
            concepts=("not_proposed",),
        )


def test_claim_proposal_replaces_same_handle(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    commit_source_concept_proposal(
        repo, _SOURCE, local_name="widget", definition="a widget", form="dimensionless"
    )
    commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id="c1",
        claim_type=ClaimType.OBSERVATION,
        context="ctx",
        statement="first",
        concepts=("widget",),
    )
    commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id="c1",
        claim_type=ClaimType.OBSERVATION,
        context="ctx",
        statement="second",
        concepts=("widget",),
    )
    index = source_claim_index(repo, _SOURCE)
    assert len(index.records_by_id) == 1


# ---------------------------------------------------------------------------
# reserved-namespace guard (source cannot mint canonical ids)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("reserved", ["ps", "propstore"])
def test_normalize_rejects_reserved_namespace(reserved: str) -> None:
    data = SourceClaimsDocument(
        claims=(SourceClaimDocument(id="c1", type=ClaimType.OBSERVATION),)
    )
    with pytest.raises(ReservedNamespaceViolation):
        normalize_source_claims_payload(
            data, source_uri="tag:test", source_namespace=reserved
        )


def test_normalize_non_reserved_namespace_succeeds() -> None:
    data = SourceClaimsDocument(
        claims=(SourceClaimDocument(id="c1", type=ClaimType.OBSERVATION),)
    )
    normalized, local_map = normalize_source_claims_payload(
        data, source_uri="tag:test", source_namespace="my_paper"
    )
    (claim,) = normalized.claims
    assert claim.artifact_id is not None and claim.artifact_id.startswith("ps:claim:")
    assert local_map == {"c1": claim.logical_ids[0].value}


def test_typed_claim_identity_is_independent_of_condition_order() -> None:
    first, _ = normalize_source_claims_payload(
        SourceClaimsDocument(
            claims=(
                SourceClaimDocument(
                    id="c1",
                    type=ClaimType.OBSERVATION,
                    conditions=("b == 2", "a == 1"),
                ),
            )
        ),
        source_uri="tag:test",
        source_namespace="my_paper",
    )
    second, _ = normalize_source_claims_payload(
        SourceClaimsDocument(
            claims=(
                SourceClaimDocument(
                    id="c1",
                    type=ClaimType.OBSERVATION,
                    conditions=("a == 1", "b == 2"),
                ),
            )
        ),
        source_uri="tag:test",
        source_namespace="my_paper",
    )

    assert first.claims[0].artifact_id == second.claims[0].artifact_id
    assert first.claims[0].version_id == second.claims[0].version_id


# ---------------------------------------------------------------------------
# value-bound guard
# ---------------------------------------------------------------------------


def _seed_bounded_form(repo: Repository) -> None:
    repo.families.form.save(
        "temperature",
        FormDefinition(
            name="temperature",
            kind=KindType.QUANTITY,
            min_value=0.0,
            max_value=100.0,
        ),
        message="seed bounded form",
    )


def test_claim_value_above_form_max_is_rejected(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_bounded_form(repo)
    commit_source_concept_proposal(
        repo, _SOURCE, local_name="temp", definition="a temperature", form="temperature"
    )
    with pytest.raises(ValueError, match="is above form"):
        commit_source_claim_proposal(
            repo,
            _SOURCE,
            claim_id="hot",
            claim_type=ClaimType.PARAMETER,
            context="ctx",
            concept="temp",
            value=200.0,
        )


def test_claim_value_within_form_bounds_is_accepted(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _seed_bounded_form(repo)
    commit_source_concept_proposal(
        repo, _SOURCE, local_name="temp", definition="a temperature", form="temperature"
    )
    claim = commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id="warm",
        claim_type=ClaimType.PARAMETER,
        context="ctx",
        concept="temp",
        value=37.0,
    )
    assert claim.value == 37.0


def test_parameter_claim_uses_closed_category_vocabulary(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    repo.families.form.save(
        "severity",
        FormDefinition(
            name="severity",
            kind=KindType.CATEGORY,
            min_value=0.0,
            max_value=1.0,
        ),
        message="seed closed category form",
    )
    commit_source_concept_proposal(
        repo,
        _SOURCE,
        local_name="severity",
        definition="A severity label.",
        form="severity",
        form_parameters=SourceConceptFormParametersDocument(
            values=("low", "high"),
            extensible=False,
        ),
    )

    accepted = commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id="known-severity",
        claim_type=ClaimType.PARAMETER,
        context="ctx",
        concept="severity",
        value="low",
    )
    assert accepted.value == "low"

    with pytest.raises(ValueError, match="closed category vocabulary"):
        commit_source_claim_proposal(
            repo,
            _SOURCE,
            claim_id="unknown-severity",
            claim_type=ClaimType.PARAMETER,
            context="ctx",
            concept="severity",
            value="critical",
        )


def test_parameter_claim_accepts_extensible_category_value(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    repo.families.form.save(
        "label",
        FormDefinition(name="label", kind=KindType.CATEGORY),
        message="seed extensible category form",
    )
    commit_source_concept_proposal(
        repo,
        _SOURCE,
        local_name="label",
        definition="An extensible label.",
        form="label",
        form_parameters=SourceConceptFormParametersDocument(
            values=("known",),
            extensible=True,
        ),
    )

    claim = commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id="new-label",
        claim_type=ClaimType.PARAMETER,
        context="ctx",
        concept="label",
        value="new",
    )
    assert claim.value == "new"


def test_parameter_claim_requires_boolean_value(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    repo.families.form.save(
        "enabled",
        FormDefinition(name="enabled", kind=KindType.BOOLEAN),
        message="seed boolean form",
    )
    commit_source_concept_proposal(
        repo,
        _SOURCE,
        local_name="enabled",
        definition="Whether the feature is enabled.",
        form="enabled",
    )

    accepted = commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id="enabled-bool",
        claim_type=ClaimType.PARAMETER,
        context="ctx",
        concept="enabled",
        value=True,
    )
    assert accepted.value is True

    with pytest.raises(ValueError, match="value must be boolean"):
        commit_source_claim_proposal(
            repo,
            _SOURCE,
            claim_id="enabled-text",
            claim_type=ClaimType.PARAMETER,
            context="ctx",
            concept="enabled",
            value="true",
        )


def test_source_claim_cel_uses_closed_category_metadata(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    repo.families.form.save(
        "category",
        FormDefinition(name="category", kind=KindType.CATEGORY),
        message="seed category form",
    )
    commit_source_concept_proposal(
        repo,
        _SOURCE,
        local_name="severity",
        definition="A severity label.",
        form="category",
        form_parameters=SourceConceptFormParametersDocument(
            values=("low", "medium", "high"),
            extensible=False,
        ),
    )

    accepted = commit_source_claim_proposal(
        repo,
        _SOURCE,
        claim_id="known_severity",
        claim_type=ClaimType.OBSERVATION,
        context="ctx",
        statement="Known severity.",
        concepts=("severity",),
        conditions=("severity == 'low'",),
    )
    assert accepted.conditions == ("severity == 'low'",)

    with pytest.raises(ValueError, match="invalid CEL condition"):
        commit_source_claim_proposal(
            repo,
            _SOURCE,
            claim_id="unknown_severity",
            claim_type=ClaimType.OBSERVATION,
            context="ctx",
            statement="Unknown severity.",
            concepts=("severity",),
            conditions=("severity == 'critical'",),
        )


# ---------------------------------------------------------------------------
# stance / justification resolution (reference lowering)
# ---------------------------------------------------------------------------


def _two_claims(repo: Repository) -> None:
    commit_source_concept_proposal(
        repo, _SOURCE, local_name="widget", definition="a widget", form="dimensionless"
    )
    for handle, statement in (("c1", "first"), ("c2", "second")):
        commit_source_claim_proposal(
            repo,
            _SOURCE,
            claim_id=handle,
            claim_type=ClaimType.OBSERVATION,
            context="ctx",
            statement=statement,
            concepts=("widget",),
        )


def test_stance_resolves_handles_to_canonical_ids(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _two_claims(repo)
    stance = commit_source_stance_proposal(
        repo, _SOURCE, source_claim="c1", target="c2", stance_type=StanceType.SUPPORTS
    )
    assert stance.source_claim is not None
    assert stance.source_claim.startswith("ps:claim:")
    assert stance.target is not None and stance.target.startswith("ps:claim:")
    assert stance.type is StanceType.SUPPORTS


def test_stance_unresolved_target_raises(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _two_claims(repo)
    with pytest.raises(ValueError, match="unresolved stance target"):
        commit_source_stance_proposal(
            repo,
            _SOURCE,
            source_claim="c1",
            target="ghost",
            stance_type=StanceType.REBUTS,
        )


def test_justification_resolves_and_validates_rule_kind(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _two_claims(repo)
    just = commit_source_justification_proposal(
        repo,
        _SOURCE,
        just_id="j1",
        conclusion="c1",
        premises=("c2",),
        rule_kind="empirical_support",
        rule_strength="defeasible",
    )
    assert just.conclusion is not None and just.conclusion.startswith("ps:claim:")
    assert just.premises[0].startswith("ps:claim:")


def test_justification_invalid_rule_kind_raises(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _two_claims(repo)
    with pytest.raises(ValueError, match="rule_kind must be one of"):
        commit_source_justification_proposal(
            repo,
            _SOURCE,
            just_id="j1",
            conclusion="c1",
            premises=("c2",),
            rule_kind="made_up_rule",
        )


# ---------------------------------------------------------------------------
# reference lowering helpers
# ---------------------------------------------------------------------------


def test_resolve_source_or_primary_claim_id(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    _two_claims(repo)
    index = source_claim_index(repo, _SOURCE)
    resolved = resolve_source_or_primary_claim_id("c1", source=index)
    assert resolved is not None and resolved.startswith("ps:claim:")
    assert resolve_source_or_primary_claim_id("nope", source=index) is None


def test_local_handle_collision_blocks_index_build(tmp_path: Path) -> None:
    repo = _new_source(tmp_path)
    # Two claims sharing one source-local handle would map one reference to two
    # artifact ids — quire's reference index rejects the ambiguity rather than
    # silently picking one (no truncated identity).
    data = SourceClaimsDocument(
        claims=(
            SourceClaimDocument(
                artifact_id="ps:claim:aaa",
                source_local_id="dup",
                type=ClaimType.OBSERVATION,
                statement="a",
            ),
            SourceClaimDocument(
                artifact_id="ps:claim:bbb",
                source_local_id="dup",
                type=ClaimType.OBSERVATION,
                statement="b",
            ),
        )
    )
    repo.families.source_claims.save(
        SourceRef(_SOURCE), data, message="ambiguous handles"
    )
    with pytest.raises(AmbiguousReferenceError):
        source_claim_index(repo, _SOURCE)


# ---------------------------------------------------------------------------
# claim-side concept-handle rewriting (claim_concepts)
# ---------------------------------------------------------------------------


def test_rewrite_claim_concept_refs_lowers_known_handles() -> None:
    claim = SourceClaimDocument(
        id="c1",
        type=ClaimType.OBSERVATION,
        concept="local_widget",
        concepts=("local_widget", "ps:concept:already"),
    )
    unresolved: set[str] = set()
    rewritten = rewrite_claim_concept_refs(
        claim, {"local_widget": "ps:concept:widget"}, unresolved=unresolved
    )
    assert rewritten.concept == "ps:concept:widget"
    assert rewritten.concepts == ("ps:concept:widget", "ps:concept:already")
    assert unresolved == set()


def test_rewrite_claim_concept_refs_records_unresolved() -> None:
    claim = SourceClaimDocument(
        id="c1", type=ClaimType.OBSERVATION, concept="missing_handle"
    )
    unresolved: set[str] = set()
    rewritten = rewrite_claim_concept_refs(claim, {}, unresolved=unresolved)
    assert rewritten.concept == "missing_handle"  # left in place, not dropped
    assert unresolved == {"missing_handle"}
