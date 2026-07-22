"""Owner-layer worldline workflows over a real :class:`Repository`.

Drives :mod:`propstore.app.worldlines` — create / materialize / show / list /
diff / delete plus staleness — asserting typed reports and the
:class:`WorldlineAppError` hierarchy. The owner takes typed requests and returns
typed reports; it never touches Click, stdout, or ``sys.exit``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.app.world import open_app_world_model
from propstore.app.worldlines import (
    WorldlineAlreadyExistsError,
    WorldlineCreateRequest,
    WorldlineDiffRequest,
    WorldlineNotFoundError,
    WorldlinePolicyOptions,
    WorldlineRunRequest,
    WorldlineShowRequest,
    WorldlineValidationError,
    create_worldline,
    delete_worldline,
    diff_worldlines,
    list_worldlines,
    materialize_worldline,
    show_worldline,
    worldline_is_stale,
)
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.predicates import Predicate
from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.fragility import rank_fragility
from propstore.grounding.bundle import GroundingStatus
from propstore.repository import Repository
from propstore.world.resolution import resolve
from propstore.world.types import (
    Environment,
    ReasoningBackend,
    RenderPolicy,
    ResolutionStrategy,
    ValueStatus,
)
from propstore.worldline.runner import run_worldline


def _repo(tmp_path: Path) -> Repository:
    """A repo with one concept (Speed) backed by a single parameter claim."""

    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="c1",
            value=10.0,
        ),
        message="m",
    )
    return repo


def test_create_worldline_persists_and_show_loads_it(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = create_worldline(
        repo, WorldlineCreateRequest(name="wl", targets=("Speed",))
    )
    assert report.name == "wl"
    assert report.path.endswith("wl.yaml")

    shown = show_worldline(repo, WorldlineShowRequest(name="wl"))
    assert shown.definition.id == "wl"
    assert shown.definition.targets == ["Speed"]
    assert shown.stale is None  # staleness not requested


def test_create_worldline_twice_raises_already_exists(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    create_worldline(repo, WorldlineCreateRequest(name="wl", targets=("Speed",)))
    with pytest.raises(WorldlineAlreadyExistsError) as excinfo:
        create_worldline(repo, WorldlineCreateRequest(name="wl", targets=("Speed",)))
    assert excinfo.value.name == "wl"


def test_show_missing_worldline_raises_not_found(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(WorldlineNotFoundError) as excinfo:
        show_worldline(repo, WorldlineShowRequest(name="ghost"))
    assert excinfo.value.name == "ghost"


def test_materialize_new_worldline_returns_result(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = materialize_worldline(
        repo, WorldlineRunRequest(name="wl", targets=("Speed",))
    )
    assert report.name == "wl"
    assert "Speed" in report.result.values
    assert report.result.content_hash

    shown = show_worldline(repo, WorldlineShowRequest(name="wl"))
    assert shown.definition.results is not None


def test_materialize_requires_targets_for_new_worldline(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(WorldlineValidationError):
        materialize_worldline(repo, WorldlineRunRequest(name="wl"))


def test_incomplete_aspic_worldline_is_diagnostic_but_not_materialized(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    repo.families.claim.save(
        "cl2",
        Claim(
            claim_id="cl2",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="c1",
            value=11.0,
        ),
        message="m",
    )
    repo.families.predicate.save(
        "has_value",
        Predicate(
            predicate_id="has_value",
            arity=1,
            arg_types=("Claim",),
            derived_from="claim.attribute:value",
        ),
        message="m",
    )
    repo.families.predicate.save(
        "important",
        Predicate(predicate_id="important", arity=1, arg_types=("Claim",)),
        message="m",
    )
    repo.families.defeasible_rule.save(
        "r1",
        DefeasibleRule(
            rule_id="r1",
            kind="defeasible",
            head=Atom(predicate="important", terms=(Term(kind="var", name="X"),)),
            body=(
                BodyLiteral(
                    kind="positive",
                    atom=Atom(
                        predicate="has_value",
                        terms=(Term(kind="var", name="X"),),
                    ),
                ),
            ),
        ),
        message="m",
    )
    repo.require_git().commit_files(
        {"propstore.yaml": b"grounding_max_arguments: 1\n"},
        "Set tiny grounding budget",
    )
    policy = WorldlinePolicyOptions(
        strategy="argumentation",
        reasoning_backend="aspic",
    )
    create_worldline(
        repo,
        WorldlineCreateRequest(name="wl", targets=("Speed",), policy=policy),
    )
    definition = show_worldline(repo, WorldlineShowRequest(name="wl")).definition

    with open_app_world_model(repo) as world:
        bound = world.bind(Environment())
        resolved = resolve(
            bound,
            "c1",
            policy=RenderPolicy(
                strategy=ResolutionStrategy.ARGUMENTATION,
                reasoning_backend=ReasoningBackend.ASPIC,
            ),
            world=world,
        )
        diagnostic = run_worldline(definition, world)
        fragility = rank_fragility(
            bound,
            concept_id="c1",
            include_atms=False,
            include_discovery=False,
            include_conflict=False,
            include_grounding=True,
            include_bridge=False,
        )
    assert resolved.status is ValueStatus.CONFLICTED
    assert resolved.reason is not None
    assert diagnostic.argumentation is not None
    assert diagnostic.argumentation.backend == "aspic"
    assert diagnostic.argumentation.status == "grounding_budget_exceeded"
    assert diagnostic.argumentation.reason is not None
    assert resolved.reason == diagnostic.argumentation.reason
    assert fragility.grounding_status is GroundingStatus.BUDGET_EXCEEDED
    assert fragility.grounding_budget_reason == diagnostic.argumentation.reason

    head_before = repo.require_git().head_sha()
    with pytest.raises(
        WorldlineValidationError,
        match="argument enumeration budget exceeded",
    ):
        materialize_worldline(repo, WorldlineRunRequest(name="wl"))
    assert repo.require_git().head_sha() == head_before
    assert (
        show_worldline(repo, WorldlineShowRequest(name="wl")).definition.results
        is None
    )


def test_freshly_materialized_worldline_is_not_stale(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    materialize_worldline(repo, WorldlineRunRequest(name="wl", targets=("Speed",)))
    assert worldline_is_stale(repo, "wl") is False

    shown = show_worldline(repo, WorldlineShowRequest(name="wl", check_staleness=True))
    assert shown.stale is False
    assert shown.staleness_unavailable is False


def test_show_unmaterialized_worldline_is_never_stale(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    create_worldline(repo, WorldlineCreateRequest(name="wl", targets=("Speed",)))
    shown = show_worldline(repo, WorldlineShowRequest(name="wl", check_staleness=True))
    # No stored result ⇒ never stale (nothing to be stale against).
    assert shown.stale is False


def test_list_worldlines_reports_status_and_targets(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    create_worldline(
        repo, WorldlineCreateRequest(name="pending_wl", targets=("Speed",))
    )
    materialize_worldline(repo, WorldlineRunRequest(name="done_wl", targets=("Speed",)))

    report = list_worldlines(repo)
    by_name = {entry.name: entry for entry in report.entries}
    assert set(by_name) == {"pending_wl", "done_wl"}
    assert by_name["pending_wl"].status == "pending"
    assert by_name["done_wl"].status == "materialized"
    assert by_name["pending_wl"].targets == ("Speed",)
    assert by_name["pending_wl"].error is None


def test_diff_worldlines_reports_input_differences(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    materialize_worldline(repo, WorldlineRunRequest(name="left", targets=("Speed",)))
    materialize_worldline(
        repo,
        WorldlineRunRequest(
            name="right",
            targets=("Speed",),
            overrides={"Speed": 5.0},
        ),
    )

    report = diff_worldlines(repo, WorldlineDiffRequest("left", "right"))
    assert report.left_id == "left"
    assert report.right_id == "right"
    labels = {difference.label for difference in report.input_differences}
    assert "Overrides" in labels


def test_diff_requires_both_materialized(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    create_worldline(repo, WorldlineCreateRequest(name="left", targets=("Speed",)))
    materialize_worldline(repo, WorldlineRunRequest(name="right", targets=("Speed",)))
    with pytest.raises(WorldlineValidationError):
        diff_worldlines(repo, WorldlineDiffRequest("left", "right"))


def test_delete_worldline_removes_it(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    create_worldline(repo, WorldlineCreateRequest(name="wl", targets=("Speed",)))
    report = delete_worldline(repo, "wl")
    assert report.name == "wl"

    with pytest.raises(WorldlineNotFoundError):
        show_worldline(repo, WorldlineShowRequest(name="wl"))


def test_delete_missing_worldline_raises_not_found(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(WorldlineNotFoundError):
        delete_worldline(repo, "ghost")


def test_policy_options_are_compiled_into_the_definition(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    create_worldline(
        repo,
        WorldlineCreateRequest(
            name="wl",
            targets=("Speed",),
            policy=WorldlinePolicyOptions(strategy="recency"),
        ),
    )
    shown = show_worldline(repo, WorldlineShowRequest(name="wl"))
    assert shown.definition.policy.strategy is ResolutionStrategy.RECENCY
