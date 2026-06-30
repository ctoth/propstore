"""The concrete repo-backed ``WorldQuery`` reader (Phase 9-1).

Rewrite-native port of the reference ``test_world_query.py`` sidecar / historical
/ build-diagnostics / form-algebra / grounding / schema-validation cases
(``docs/rewrite/deferred-tests.md`` §7a-world-C3 / §7a-worldline). The reference
is ``*Row`` / ``*Document``-shaped over a hand-authored projection schema; these
exercise the same behaviours over ``Repository.init`` -> author charters ->
``materialize_world_sidecar`` -> ``WorldQuery``.

The reader satisfies the ``WorldStore`` protocol and reuses the ``world.model``
C3 free-function glue (``bind`` / ``chain_query`` / ``intervene`` / ``observe``)
unchanged; the embedding-similarity cases are deferred to Phase 10 (no sqlite-vec
index in this slice) and assert the honest-empty contract here.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from propstore.core.environment import Environment, WorldStore
from propstore.core.micropublications import ActiveMicropublication
from propstore.families.claims import Claim, ClaimStatus, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.micropublications import Micropublication
from propstore.families.relations import Stance
from propstore.repository import Repository
from propstore.stances import StanceType
from propstore.world import RenderPolicy, WorldQuery
from propstore.world.model import (
    _active_graph,
    _bind,
    _chain_query,
    _compiled_graph,
    _intervene,
    _observe,
    active_graph,
    bind,
    chain_query,
    compiled_graph,
    intervene,
    observe,
)


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.concept.save(
        "c2", Concept(concept_id="c2", canonical_name="Distance"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1",
            context_id="ctx1",
            claim_type=ClaimType.OBSERVATION,
            output_concept="c1",
            value=3.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "cl2",
        Claim(
            claim_id="cl2",
            context_id="ctx1",
            claim_type=ClaimType.OBSERVATION,
            output_concept="c1",
            value=4.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "cl3",
        Claim(
            claim_id="cl3",
            context_id="ctx1",
            claim_type=ClaimType.OBSERVATION,
            output_concept="c2",
            value=9.0,
            status=ClaimStatus.BLOCKED,
        ),
        message="m",
    )
    repo.families.stance.save(
        "s1",
        Stance(
            stance_id="s1",
            source_claim_id="cl1",
            target_claim_id="cl2",
            stance_type=StanceType.REBUTS,
        ),
        message="m",
    )
    return repo


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    return _repo(tmp_path)


@pytest.fixture
def world(repo: Repository) -> WorldQuery:
    return WorldQuery(repo)


# ── construction / lifecycle ─────────────────────────────────────────────────


def test_satisfies_world_store_protocol(world: WorldQuery) -> None:
    assert isinstance(world, WorldStore)


def test_construct_from_repo_auto_materializes(repo: Repository) -> None:
    # No prior build; the reader materializes the sidecar on construction.
    with WorldQuery(repo) as world:
        assert world.stats().concepts == 2


def test_from_path(repo: Repository) -> None:
    with WorldQuery.from_path(repo.root) as world:
        assert world.stats().claims == 3


def test_context_manager_closes(repo: Repository) -> None:
    world = WorldQuery(repo)
    with world:
        assert world.stats().concepts == 2
    # The session is closed; reopening works independently.
    with WorldQuery(repo) as reopened:
        assert reopened.stats().concepts == 2


def test_missing_sidecar_is_honest(repo: Repository, tmp_path: Path) -> None:
    from propstore.derived_build import materialize_world_sidecar

    handle, _ = materialize_world_sidecar(repo)
    Path(handle.path).unlink()
    with pytest.raises(FileNotFoundError, match="pks build"):
        WorldQuery(repo, derived_store=handle)


def test_requires_repo_or_store() -> None:
    with pytest.raises(TypeError):
        WorldQuery()


# ── concepts ─────────────────────────────────────────────────────────────────


def test_get_concept(world: WorldQuery) -> None:
    concept = world.get_concept("c1")
    assert concept is not None
    assert concept.canonical_name == "Speed"
    assert isinstance(concept, Concept)


def test_get_concept_by_canonical_name(world: WorldQuery) -> None:
    concept = world.get_concept("Distance")
    assert concept is not None
    assert concept.concept_id == "c2"


def test_get_concept_missing(world: WorldQuery) -> None:
    assert world.get_concept("nope") is None


def test_all_concepts(world: WorldQuery) -> None:
    assert sorted(c.concept_id for c in world.all_concepts()) == ["c1", "c2"]


def test_resolve_concept_by_id_and_name(world: WorldQuery) -> None:
    assert world.resolve_concept("c1") == "c1"
    assert world.resolve_concept("Distance") == "c2"
    assert world.resolve_concept("missing") is None


def test_resolve_alias_is_honest_empty(world: WorldQuery) -> None:
    assert world.resolve_alias("anything") is None


def test_search(world: WorldQuery) -> None:
    hits = world.search("Spe")
    assert [str(hit.concept_id) for hit in hits] == ["c1"]


# ── claims ───────────────────────────────────────────────────────────────────


def test_get_claim(world: WorldQuery) -> None:
    claim = world.get_claim("cl1")
    assert claim is not None
    assert claim.value == 3.0
    assert isinstance(claim, Claim)


def test_get_claim_missing(world: WorldQuery) -> None:
    assert world.get_claim("nope") is None


def test_claims_for_concept(world: WorldQuery) -> None:
    assert sorted(c.claim_id for c in world.claims_for("c1")) == ["cl1", "cl2"]


def test_claims_for_none_returns_all(world: WorldQuery) -> None:
    # Non-commitment: storage returns every claim, including the blocked one.
    assert len(world.claims_for(None)) == 3


def test_claims_by_ids(world: WorldQuery) -> None:
    by_id = world.claims_by_ids({"cl1", "cl3"})
    assert set(by_id) == {"cl1", "cl3"}
    assert by_id["cl1"].value == 3.0


def test_claims_with_policy_hides_blocked_by_default(world: WorldQuery) -> None:
    visible = world.claims_with_policy(None, RenderPolicy())
    assert sorted(c.claim_id for c in visible) == ["cl1", "cl2"]


def test_claims_with_policy_include_blocked(world: WorldQuery) -> None:
    visible = world.claims_with_policy(None, RenderPolicy(include_blocked=True))
    assert sorted(c.claim_id for c in visible) == ["cl1", "cl2", "cl3"]


# ── stances ──────────────────────────────────────────────────────────────────


def test_stances_between(world: WorldQuery) -> None:
    stances = world.stances_between({"cl1", "cl2"})
    assert [s.stance_id for s in stances] == ["s1"]


def test_stances_between_disjoint_is_empty(world: WorldQuery) -> None:
    assert world.stances_between({"cl1"}) == []


def test_all_claim_stances(world: WorldQuery) -> None:
    assert [s.stance_id for s in world.all_claim_stances()] == ["s1"]


def test_explain_returns_incident_stances(world: WorldQuery) -> None:
    assert [s.stance_id for s in world.explain("cl1")] == ["s1"]


def test_explain_no_stances(world: WorldQuery) -> None:
    assert world.explain("cl3") == []


# ── conflicts / stats / relationships ────────────────────────────────────────


def test_conflicts(world: WorldQuery) -> None:
    # The two same-concept observations do not produce a conflict record here.
    assert list(world.conflicts()) == []


def test_stats(world: WorldQuery) -> None:
    stats = world.stats()
    assert stats.concepts == 2
    assert stats.claims == 3
    assert stats.conflicts == 0


def test_all_relationships_is_empty(world: WorldQuery) -> None:
    assert list(world.all_relationships()) == []


# ── embedding similarity (deferred to Phase 10) ──────────────────────────────


def test_similar_claims_honest_empty(world: WorldQuery) -> None:
    assert world.similar_claims("cl1") == []


def test_similar_concepts_honest_empty(world: WorldQuery) -> None:
    assert world.similar_concepts("c1") == []


# ── condition solver + render glue delegation ────────────────────────────────


def test_condition_solver(world: WorldQuery) -> None:
    from condition_ir import ConditionSolver

    assert isinstance(world.condition_solver(), ConditionSolver)


def test_compiled_graph(world: WorldQuery) -> None:
    graph = world.compiled_graph()
    assert len(graph.claims) == 3
    assert len(graph.concepts) == 2


def test_bind_activates_claims(world: WorldQuery) -> None:
    bound = world.bind(Environment())
    assert len(bound.active_claims()) == 3


def test_chain_query_returns_result(world: WorldQuery) -> None:
    result = world.chain_query("c1")
    assert str(result.target_concept_id) == "c1"


def test_intervene_and_observe(world: WorldQuery) -> None:
    # Both build over the compiled graph; smoke that the delegation wires up.
    assert world.intervene({}) is not None
    assert world.observe({}) is not None


def test_render_glue_methods_delegate_to_free_functions() -> None:
    # ZEN: the reader reuses the C3 free functions (the private aliases ARE the
    # module-level free functions), it does not re-implement the glue.
    assert _bind is bind
    assert _active_graph is active_graph
    assert _chain_query is chain_query
    assert _compiled_graph is compiled_graph
    assert _intervene is intervene
    assert _observe is observe


# ── render diagnostics (quarantine surface) ──────────────────────────────────


def test_build_diagnostics_hidden_by_default(world: WorldQuery) -> None:
    assert world.build_diagnostics(RenderPolicy()) == []


def test_build_diagnostics_surfaced_on_opt_in(tmp_path: Path) -> None:
    # A claim with no recognized claim_type produces an authoring-lint diagnostic
    # at build time; it is present in the sidecar and surfaced only on opt-in.
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(claim_id="cl1", context_id="ctx1", output_concept="c1", statement="untyped"),
        message="m",
    )
    with WorldQuery(repo) as world:
        assert world.build_diagnostics(RenderPolicy()) == []
        surfaced = world.build_diagnostics(RenderPolicy(show_quarantined=True))
        assert any("cl1" in diagnostic.message for diagnostic in surfaced)


# ── micropublications ────────────────────────────────────────────────────────


def test_all_micropublications(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "kn")
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(claim_id="cl1", context_id="ctx1", claim_type=ClaimType.OBSERVATION),
        message="m",
    )
    repo.families.micropublication.save(
        "mp1",
        Micropublication(artifact_id="mp1", context_id="ctx1", claims=("cl1",)),
        message="m",
    )
    with WorldQuery(repo) as world:
        micropubs = world.all_micropublications()
        assert len(micropubs) == 1
        assert isinstance(micropubs[0], ActiveMicropublication)
        assert micropubs[0].claim_ids == ("cl1",)


# ── derived parameterization graph ───────────────────────────────────────────


def test_parameterization_derived_from_equation_claims(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "kn")
    for concept_id, name in (("v", "Speed"), ("d", "Distance"), ("t", "Time")):
        repo.families.concept.save(
            concept_id, Concept(concept_id=concept_id, canonical_name=name), message="m"
        )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "eq1",
        Claim(
            claim_id="eq1",
            context_id="ctx1",
            claim_type=ClaimType.EQUATION,
            output_concept="v",
            concepts=("d", "t"),
            expression="d / t",
        ),
        message="m",
    )
    with WorldQuery(repo) as world:
        edges = list(world.all_parameterizations())
        assert len(edges) == 1
        assert str(edges[0].output_concept_id) == "v"
        assert sorted(str(i) for i in edges[0].input_concept_ids) == ["d", "t"]
        # ``build_parameterization_groups`` unions an output only with inputs that
        # are themselves outputs (nodes); leaf inputs d/t are not outputs, so the
        # group containing v is just {v}.
        assert world.group_members("v") == ["v"]
        assert world.concept_ids_for_group(0) == {"v"}
        assert [str(e.output_concept_id) for e in world.parameterizations_for("v")] == ["v"]


# ── historical query + schema validation ─────────────────────────────────────


def test_historical_query(world: WorldQuery, repo: Repository) -> None:
    head = repo.require_git().head_sha()
    with world.historical_query(head) as historical:
        assert historical.stats().concepts == 2


def test_schema_version_mismatch_raises(repo: Repository) -> None:
    from propstore.derived_build import materialize_world_sidecar

    handle, _ = materialize_world_sidecar(repo)
    conn = sqlite3.connect(handle.path)
    try:
        conn.execute("UPDATE meta SET schema_version = 999 WHERE key = 'sidecar'")
        conn.commit()
    finally:
        conn.close()
    with pytest.raises(ValueError, match="Rebuild with 'pks build'"):
        WorldQuery(repo, derived_store=handle)
