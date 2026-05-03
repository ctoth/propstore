"""Construction and composition tests for the repository-overview report.

Step 1 pins the dataclass surface. Step 2 adds composition via
`KIND_REGISTRY` and `build_repository_overview`.
"""

from __future__ import annotations

import dataclasses
from typing import cast, get_args

import pytest

from propstore.app.claim_views import ClaimSummaryEntry, ClaimSummaryReport
from propstore.app.concepts import (
    ConceptListEntry,
    ConceptListReport,
    ConceptSidecarMissingError,
)
from propstore.app.rendering import (
    AppRenderPolicyRequest,
    RenderPolicySummary,
)
from propstore.app import repository_overview
from propstore.app.repository_overview import (
    InventoryRow,
    KindContributor,
    NotableConflictPointer,
    NotableConflicts,
    OverviewState,
    ProvenanceStateCount,
    ProvenanceSummary,
    RecentActivity,
    RecentActivityEntry,
    RepositoryOverviewReport,
    RepositoryOverviewRequest,
    SourcePointer,
    build_repository_overview,
)
from propstore.app.repository_views import AppRepositoryViewRequest
from propstore.app.world import WorldSidecarMissingError
from propstore.repository import Repository


def _render_policy_summary() -> RenderPolicySummary:
    return RenderPolicySummary(
        reasoning_backend="claim_graph",
        strategy="default",
        semantics="grounded",
        set_comparison="elitist",
        decision_criterion="pignistic",
        pessimism_index=0.5,
        praf_strategy="auto",
        praf_epsilon=0.01,
        praf_confidence=0.95,
        praf_seed=None,
        include_drafts=False,
        include_blocked=False,
        show_quarantined=False,
    )


def test_overview_state_alias_admits_only_documented_values() -> None:
    assert set(get_args(OverviewState)) == {"known", "vacuous", "not_implemented"}


def test_repository_overview_request_is_frozen_with_default_subrequests() -> None:
    request = RepositoryOverviewRequest()

    assert dataclasses.is_dataclass(request)
    assert isinstance(request.render_policy, AppRenderPolicyRequest)
    assert isinstance(request.repository_view, AppRepositoryViewRequest)

    with pytest.raises(dataclasses.FrozenInstanceError):
        request.render_policy = AppRenderPolicyRequest()  # type: ignore[misc]


def test_inventory_row_carries_kind_count_state_sentence_href() -> None:
    row = InventoryRow(
        kind="claims",
        count=42,
        state="known",
        sentence="42 claims are present in the sidecar.",
        href="/claims",
    )

    assert row.kind == "claims"
    assert row.count == 42
    assert row.state == "known"
    assert row.sentence == "42 claims are present in the sidecar."
    assert row.href == "/claims"

    with pytest.raises(dataclasses.FrozenInstanceError):
        row.count = 43  # type: ignore[misc]


def test_inventory_row_admits_none_href_for_kinds_without_route() -> None:
    row = InventoryRow(
        kind="unrouted",
        count=0,
        state="vacuous",
        sentence="No canonical web page for this kind yet.",
        href=None,
    )

    assert row.href is None


def test_source_pointer_construction_and_state() -> None:
    pointer = SourcePointer(
        state="known",
        source_id="src-1",
        slug="paper-foo",
        kind="paper",
        sentence="Paper foo, 3 claims.",
        href="/source/src-1",
    )

    assert pointer.state == "known"
    assert pointer.source_id == "src-1"
    assert pointer.slug == "paper-foo"
    assert pointer.kind == "paper"
    assert pointer.href == "/source/src-1"


def test_provenance_summary_with_state_counts() -> None:
    counts = (
        ProvenanceStateCount(state="measured", count=10),
        ProvenanceStateCount(state="calibrated", count=3),
        ProvenanceStateCount(state="vacuous", count=8),
    )
    summary = ProvenanceSummary(
        state="known",
        counts=counts,
        sentence="21 claims across 3 provenance states.",
    )

    assert summary.state == "known"
    assert summary.counts == counts
    assert isinstance(summary.counts, tuple)


def test_provenance_summary_can_be_not_implemented() -> None:
    summary = ProvenanceSummary(
        state="not_implemented",
        counts=(),
        sentence="Provenance aggregation is not yet computed.",
    )

    assert summary.state == "not_implemented"
    assert summary.counts == ()


def test_recent_activity_entry_construction() -> None:
    entry = RecentActivityEntry(
        when="2026-05-02T19:40:32",
        what="Added claim X",
        href="/claim/x",
    )

    assert entry.when == "2026-05-02T19:40:32"
    assert entry.what == "Added claim X"
    assert entry.href == "/claim/x"


def test_recent_activity_with_entries() -> None:
    activity = RecentActivity(
        state="known",
        entries=(
            RecentActivityEntry(when="2026-05-02", what="x", href=None),
        ),
        sentence="1 recent change.",
    )

    assert activity.state == "known"
    assert isinstance(activity.entries, tuple)
    assert len(activity.entries) == 1


def test_notable_conflict_pointer_construction() -> None:
    pointer = NotableConflictPointer(
        claim_id="c1",
        sentence="claim c1 is attacked by 2 claims.",
        href="/claim/c1",
    )

    assert pointer.claim_id == "c1"
    assert pointer.href == "/claim/c1"


def test_notable_conflicts_with_pointers() -> None:
    conflicts = NotableConflicts(
        state="known",
        entries=(
            NotableConflictPointer(claim_id="c1", sentence="x", href=None),
        ),
        sentence="1 contested claim.",
    )

    assert conflicts.state == "known"
    assert len(conflicts.entries) == 1


def test_repository_overview_report_carries_all_typed_sections() -> None:
    policy = _render_policy_summary()
    report = RepositoryOverviewReport(
        repository_state="current worktree",
        render_policy=policy,
        inventory_rows=(
            InventoryRow(
                kind="claims",
                count=42,
                state="known",
                sentence="42 claims.",
                href="/claims",
            ),
        ),
        source_pointers=(),
        provenance_summary=ProvenanceSummary(
            state="not_implemented",
            counts=(),
            sentence="not yet computed",
        ),
        recent_activity=RecentActivity(
            state="not_implemented",
            entries=(),
            sentence="not yet computed",
        ),
        notable_conflicts=NotableConflicts(
            state="not_implemented",
            entries=(),
            sentence="not yet computed",
        ),
        prose_summary="The repository holds 42 claims under grounded semantics.",
    )

    assert dataclasses.is_dataclass(report)
    assert report.repository_state == "current worktree"
    assert report.render_policy is policy
    assert isinstance(report.inventory_rows, tuple)
    assert report.inventory_rows[0].kind == "claims"
    assert isinstance(report.source_pointers, tuple)
    assert report.provenance_summary.state == "not_implemented"
    assert report.recent_activity.state == "not_implemented"
    assert report.notable_conflicts.state == "not_implemented"
    assert "42 claims" in report.prose_summary

    with pytest.raises(dataclasses.FrozenInstanceError):
        report.repository_state = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Step 2 — KIND_REGISTRY composition
# ---------------------------------------------------------------------------


def _fake_repo() -> Repository:
    return cast(Repository, object())


def test_kind_contributor_is_frozen_dataclass_with_count_callable() -> None:
    contributor = KindContributor(
        kind="example",
        href="/example",
        count=lambda _repo: 0,
        sidecar_missing=(),
    )

    assert contributor.kind == "example"
    assert contributor.href == "/example"
    assert callable(contributor.count)
    assert contributor.sidecar_missing == ()

    with pytest.raises(dataclasses.FrozenInstanceError):
        contributor.kind = "other"  # type: ignore[misc]


def test_kind_registry_is_a_nonempty_tuple_of_kind_contributors() -> None:
    registry = repository_overview.KIND_REGISTRY

    assert isinstance(registry, tuple)
    assert len(registry) > 0
    for entry in registry:
        assert isinstance(entry, KindContributor)


def test_kind_registry_kinds_are_unique() -> None:
    kinds = tuple(kc.kind for kc in repository_overview.KIND_REGISTRY)
    assert len(kinds) == len(set(kinds))


def _replace_registry(
    monkeypatch: pytest.MonkeyPatch,
    contributors: tuple[KindContributor, ...],
) -> None:
    monkeypatch.setattr(repository_overview, "KIND_REGISTRY", contributors)


def test_overview_inventory_has_one_row_per_registered_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = tuple(
        KindContributor(
            kind=f"kind-{i}",
            href=f"/{i}",
            count=lambda _repo, _i=i: 100 + _i,
            sidecar_missing=(),
        )
        for i in range(3)
    )
    _replace_registry(monkeypatch, fake)

    report = build_repository_overview(_fake_repo(), RepositoryOverviewRequest())

    assert {row.kind for row in report.inventory_rows} == {kc.kind for kc in fake}
    assert len(report.inventory_rows) == len(fake)


def test_overview_row_count_and_state_when_counter_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = (
        KindContributor(
            kind="exemplar",
            href="/exemplar",
            count=lambda _repo: 42,
            sidecar_missing=(),
        ),
    )
    _replace_registry(monkeypatch, fake)

    report = build_repository_overview(_fake_repo(), RepositoryOverviewRequest())

    row = report.inventory_rows[0]
    assert row.count == 42
    assert row.state == "known"
    assert row.kind == "exemplar"
    assert row.href == "/exemplar"


def test_overview_row_state_is_vacuous_when_counter_raises_sidecar_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeMissing(Exception):
        pass

    def _raises(_repo: Repository) -> int:
        raise FakeMissing("sidecar gone")

    fake = (
        KindContributor(
            kind="vacant",
            href="/vacant",
            count=_raises,
            sidecar_missing=(FakeMissing,),
        ),
    )
    _replace_registry(monkeypatch, fake)

    report = build_repository_overview(_fake_repo(), RepositoryOverviewRequest())

    assert len(report.inventory_rows) == 1
    row = report.inventory_rows[0]
    assert row.state == "vacuous"
    assert row.count == 0
    assert "vacant" in row.sentence or "sidecar" in row.sentence.lower()


def test_overview_row_propagates_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Unrelated(Exception):
        pass

    def _raises(_repo: Repository) -> int:
        raise Unrelated("not a sidecar issue")

    fake = (
        KindContributor(
            kind="boom",
            href=None,
            count=_raises,
            sidecar_missing=(),
        ),
    )
    _replace_registry(monkeypatch, fake)

    with pytest.raises(Unrelated):
        build_repository_overview(_fake_repo(), RepositoryOverviewRequest())


def test_overview_unwired_sections_are_not_implemented(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = (
        KindContributor(
            kind="anything",
            href=None,
            count=lambda _repo: 0,
            sidecar_missing=(),
        ),
    )
    _replace_registry(monkeypatch, fake)

    report = build_repository_overview(_fake_repo(), RepositoryOverviewRequest())

    assert report.source_pointers == ()
    assert report.provenance_summary.state == "not_implemented"
    assert report.recent_activity.state == "not_implemented"
    assert report.notable_conflicts.state == "not_implemented"


# Production-wiring tests — these intentionally pin the kind names "claims"
# and "concepts" to specific underlying list_* functions, since the plan
# requires verifying the production registry's wiring for those two kinds.


def _claim_summary_entry(claim_id: str) -> ClaimSummaryEntry:
    return ClaimSummaryEntry(
        claim_id=claim_id,
        logical_id=claim_id,
        concept_id="c1",
        concept_name="example",
        concept_display="example",
        claim_type="parameter",
        value_display="x",
        condition_display="(vacuous)",
        status_state="known",
        status_reason="visible",
    )


def _isolate_to_kind(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    """Replace KIND_REGISTRY with only the contributor for the named kind."""
    target = next(
        kc for kc in repository_overview.KIND_REGISTRY if kc.kind == kind
    )
    monkeypatch.setattr(repository_overview, "KIND_REGISTRY", (target,))


def test_real_registry_claims_count_matches_list_claim_views_entries_length(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_report = ClaimSummaryReport(
        entries=tuple(_claim_summary_entry(f"c{i}") for i in range(5))
    )
    monkeypatch.setattr(
        repository_overview,
        "list_claim_views",
        lambda _repo, _req: fake_report,
    )
    _isolate_to_kind(monkeypatch, "claims")

    report = build_repository_overview(_fake_repo(), RepositoryOverviewRequest())

    assert report.inventory_rows[0].kind == "claims"
    assert report.inventory_rows[0].count == 5
    assert report.inventory_rows[0].state == "known"


def test_real_registry_concepts_count_matches_list_concepts_entries_length(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_report = ConceptListReport(
        concepts_found=True,
        entries=tuple(
            ConceptListEntry(handle=f"h{i}", canonical_name=f"n{i}", status="active")
            for i in range(7)
        ),
    )
    monkeypatch.setattr(
        repository_overview,
        "list_concepts",
        lambda _repo, _req: fake_report,
    )
    _isolate_to_kind(monkeypatch, "concepts")

    report = build_repository_overview(_fake_repo(), RepositoryOverviewRequest())

    assert report.inventory_rows[0].kind == "concepts"
    assert report.inventory_rows[0].count == 7
    assert report.inventory_rows[0].state == "known"


def test_real_registry_concepts_row_is_vacuous_on_concept_sidecar_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raises(_repo: Repository, _req: object) -> ConceptListReport:
        raise ConceptSidecarMissingError("sidecar not found")

    monkeypatch.setattr(repository_overview, "list_concepts", _raises)
    _isolate_to_kind(monkeypatch, "concepts")

    report = build_repository_overview(_fake_repo(), RepositoryOverviewRequest())

    assert report.inventory_rows[0].kind == "concepts"
    assert report.inventory_rows[0].state == "vacuous"
    assert report.inventory_rows[0].count == 0


def test_real_registry_claims_row_is_vacuous_on_world_sidecar_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raises(_repo: Repository, _req: object) -> ClaimSummaryReport:
        raise WorldSidecarMissingError()

    monkeypatch.setattr(repository_overview, "list_claim_views", _raises)
    _isolate_to_kind(monkeypatch, "claims")

    report = build_repository_overview(_fake_repo(), RepositoryOverviewRequest())

    assert report.inventory_rows[0].kind == "claims"
    assert report.inventory_rows[0].state == "vacuous"
    assert report.inventory_rows[0].count == 0
