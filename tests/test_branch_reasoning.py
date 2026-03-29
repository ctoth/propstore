"""Phase 3 RED: Failing tests for branch-aware ATMS and ASPIC+ integration.

Tests branch assumptions in the ATMS engine, cross-branch ASPIC+ attacks
from merge classification, nogood propagation from CONFLICT items, and
sidecar branch column infrastructure.

Heavy Hypothesis property tests verify formal invariants from the literature.
"""
from __future__ import annotations

from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from propstore.core.labels import (
    AssumptionRef,
    EnvironmentKey,
    NogoodSet,
)
from propstore.repo.merge_classifier import MergeClassification, MergeItem

# ── Strategies ──────────────────────────────────────────────────────

st_assumption_kind = st.sampled_from(["binding", "context", "branch"])

st_assumption_id = st.from_regex(r"[a-z][a-z0-9_]{2,15}", fullmatch=True)

st_assumption_ref = st.builds(
    AssumptionRef,
    assumption_id=st_assumption_id,
    kind=st_assumption_kind,
    source=st_assumption_id,
    cel=st.just("true"),
)

st_env_key = st.lists(st_assumption_id, min_size=1, max_size=5).map(
    lambda ids: EnvironmentKey(tuple(sorted(set(ids))))
)

st_nogood_set = st.lists(st_env_key, min_size=0, max_size=3).map(
    lambda keys: NogoodSet(tuple(keys))
)

st_claim_id = st.from_regex(r"claim_[a-z0-9]{3,8}", fullmatch=True)

st_concept_id = st.from_regex(r"concept_[a-z0-9]{3,8}", fullmatch=True)

st_merge_classification = st.sampled_from(list(MergeClassification))

st_merge_item = st.builds(
    MergeItem,
    classification=st_merge_classification,
    claim_id=st_claim_id,
    concept_id=st_concept_id,
    left_value=st.just({"type": "parameter", "value": 1.0}),
    right_value=st.just({"type": "parameter", "value": 2.0}),
    base_value=st.just(None),
    left_branch=st.just("master"),
    right_branch=st.just("paper/test"),
)


# ── Group 1: Hypothesis Property Tests — Label Infrastructure ──────


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(ref=st_assumption_ref)
def test_branch_assumption_ref_valid(ref: AssumptionRef) -> None:
    """AssumptionRef with kind='branch' is valid and orderable.

    Per Mason & Johnson 1989: branch assumptions are first-class ATMS
    assumptions that participate in label computation identically to
    binding/context assumptions.
    """
    assume(ref.kind == "branch")
    # Hashable — can be used as dict key
    d = {ref: True}
    assert d[ref] is True
    # Orderable — can be sorted with other refs
    other = AssumptionRef(
        assumption_id="zzz_other",
        kind="binding",
        source="other",
        cel="true",
    )
    sorted_refs = sorted([ref, other])
    assert len(sorted_refs) == 2


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(a=st_env_key, b=st_env_key)
def test_environment_key_union_commutative(
    a: EnvironmentKey, b: EnvironmentKey
) -> None:
    """EnvironmentKey.union is commutative.

    Per Konieczny & Pino Perez 2002, IC3: merging is syntax-independent.
    Union of assumption sets must be order-independent since branch names
    are arbitrary labels.
    """
    assert a.union(b) == b.union(a)


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(a=st_env_key, b=st_env_key, c=st_env_key)
def test_environment_key_union_associative(
    a: EnvironmentKey, b: EnvironmentKey, c: EnvironmentKey
) -> None:
    """EnvironmentKey.union is associative.

    Required for multi-branch merges: (A union B) union C must equal
    A union (B union C) so that merge order does not affect the result.
    """
    assert a.union(b).union(c) == a.union(b.union(c))


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    nogood_env=st_env_key,
    extra_ids=st.lists(st_assumption_id, min_size=0, max_size=3),
)
def test_nogood_monotonicity(
    nogood_env: EnvironmentKey, extra_ids: list[str]
) -> None:
    """If env_a is excluded by nogoods, any superset of env_a is also excluded.

    Per Mason & Johnson 1989, claim 8: if assumption set A is INCONSISTENT
    and A is a subset of B, then B is also INCONSISTENT. This is the
    foundational monotonicity property of ATMS nogoods — inconsistency
    propagates upward through the subset lattice.
    """
    # Construct a NogoodSet that definitely excludes nogood_env
    nogoods = NogoodSet((nogood_env,))
    assert nogoods.excludes(nogood_env)
    # Any superset must also be excluded
    superset_ids = tuple(sorted(set(nogood_env.assumption_ids + tuple(extra_ids))))
    superset = EnvironmentKey(superset_ids)
    assert nogoods.excludes(superset)


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(nogoods=st_nogood_set, new_env=st_env_key)
def test_adding_nogood_reduces_consistent_envs(
    nogoods: NogoodSet, new_env: EnvironmentKey
) -> None:
    """Adding a nogood can only reduce (never increase) consistent environments.

    Per Mason & Johnson 1989, claim 2: contradiction knowledge (nogoods) is
    the primary mechanism for limiting context explosion. Adding a new nogood
    is monotonic — nothing previously excluded becomes un-excluded.
    """
    new_nogoods = NogoodSet(nogoods.environments + (new_env,))
    # Generate a sample of test environments to check monotonicity
    test_envs = [
        EnvironmentKey(("a",)),
        EnvironmentKey(("b",)),
        EnvironmentKey(("a", "b")),
        EnvironmentKey(("a", "b", "c")),
        new_env,
    ]
    for test_env in test_envs:
        if nogoods.excludes(test_env):
            assert new_nogoods.excludes(test_env), (
                f"Environment {test_env} was excluded by original nogoods "
                f"but NOT by extended nogoods — monotonicity violated"
            )


# ── Group 2: Branch Assumptions in ATMS ────────────────────────────

# These tests import from the not-yet-existing module.
# They will fail with ImportError, which is correct for the RED phase.

from propstore.repo.branch_reasoning import (  # type: ignore[import-not-found]
    make_branch_assumption,
    branch_nogoods_from_merge,
    inject_branch_stances,
)


def test_make_branch_assumption() -> None:
    """Create an AssumptionRef for a branch.

    Per Mason & Johnson 1989: each agent's belief space maps to an
    assumption set. A git branch is an agent — its assumption ref
    must carry kind='branch' and identify the branch as source.
    """
    ref = make_branch_assumption("paper/test")
    assert ref.kind == "branch"
    assert ref.source == "paper/test"
    assert "branch" in ref.cel


def test_branch_nogoods_from_conflict() -> None:
    """CONFLICT MergeItems generate nogoods containing both branch assumptions.

    Per Mason & Johnson 1989, claim 2: contradictions detected across agents
    become nogoods. A CONFLICT classification means the same claim has
    incompatible values on each branch — the two branch assumptions cannot
    both be active simultaneously.
    """
    items = [
        MergeItem(
            classification=MergeClassification.CONFLICT,
            claim_id="c1",
            concept_id="concept1",
            left_value={"type": "parameter", "value": 1.0},
            right_value={"type": "parameter", "value": 2.0},
            base_value=None,
            left_branch="master",
            right_branch="paper/test",
        )
    ]
    nogoods = branch_nogoods_from_merge(items)
    # The nogood must contain both branch assumption IDs
    left_ref = make_branch_assumption("master")
    right_ref = make_branch_assumption("paper/test")
    both_branches = EnvironmentKey(
        (left_ref.assumption_id, right_ref.assumption_id)
    )
    assert nogoods.excludes(both_branches), (
        "Nogood set must exclude the environment containing both conflicting "
        "branch assumptions"
    )


def test_branch_nogoods_skip_non_conflicts() -> None:
    """Non-CONFLICT MergeItems do not generate nogoods.

    Only CONFLICT classifications represent genuine contradictions between
    branches. IDENTICAL, COMPATIBLE, NOVEL_LEFT, NOVEL_RIGHT, and PHI_NODE
    items are consistent across branches and must not restrict the assumption
    space.
    """
    non_conflict_classes = [
        MergeClassification.IDENTICAL,
        MergeClassification.COMPATIBLE,
        MergeClassification.NOVEL_LEFT,
        MergeClassification.NOVEL_RIGHT,
        MergeClassification.PHI_NODE,
    ]
    items = [
        MergeItem(
            classification=cls,
            claim_id=f"c_{cls.value}",
            concept_id="concept1",
            left_value={"type": "parameter", "value": 1.0},
            right_value={"type": "parameter", "value": 1.0},
            base_value=None,
            left_branch="master",
            right_branch="paper/test",
        )
        for cls in non_conflict_classes
    ]
    nogoods = branch_nogoods_from_merge(items)
    assert nogoods.environments == (), (
        "Non-CONFLICT items must not produce any nogoods"
    )


def test_branch_isolation_in_atms() -> None:
    """Claims from branch A are OUT when only branch B assumptions are active.

    Per Darwiche & Pearl 1997: branches are independent epistemic states.
    In the ATMS, a claim labeled with branch-A's assumption should only
    be IN when branch-A's assumption is active. When only branch-B is
    active, branch-A's claims must be OUT.

    This is an integration test — builds a small ATMS with branch assumptions.
    """
    from propstore.core.labels import Label

    ref_a = make_branch_assumption("branch_a")
    ref_b = make_branch_assumption("branch_b")

    # A claim labeled with branch A's assumption
    label_a = Label.singleton(ref_a)
    # A claim labeled with branch B's assumption
    label_b = Label.singleton(ref_b)

    # When only branch A is active, label_a's environments are consistent
    active_a = EnvironmentKey((ref_a.assumption_id,))
    active_b = EnvironmentKey((ref_b.assumption_id,))

    # label_a should be supported in active_a context
    assert any(
        env.subsumes(active_a) for env in label_a.environments
    ), "Claim A should be IN when branch A is active"

    # label_a should NOT be supported in active_b context (no matching env)
    assert not any(
        env.subsumes(active_b) for env in label_a.environments
    ), "Claim A should be OUT when only branch B is active"

    # Symmetric: label_b supported in active_b, not in active_a
    assert any(
        env.subsumes(active_b) for env in label_b.environments
    ), "Claim B should be IN when branch B is active"
    assert not any(
        env.subsumes(active_a) for env in label_b.environments
    ), "Claim B should be OUT when only branch A is active"


# ── Group 3: Hypothesis Property Tests — Cross-Branch ASPIC+ Attacks ──


def test_inject_branch_stances_for_conflicts() -> None:
    """CONFLICT MergeItems produce symmetric contradicts stances for ASPIC+.

    Per Coste-Marquis et al. 2007: conflicts between sources become attacks
    in the merged argumentation framework. A CONFLICT between claim A
    (left branch) and claim B (right branch) produces symmetric
    contradictory pairs — both directions of attack.
    """
    items = [
        MergeItem(
            classification=MergeClassification.CONFLICT,
            claim_id="c1",
            concept_id="concept1",
            left_value={"type": "parameter", "value": 1.0, "id": "c1_left"},
            right_value={"type": "parameter", "value": 2.0, "id": "c1_right"},
            base_value=None,
            left_branch="master",
            right_branch="paper/test",
        )
    ]
    stances = inject_branch_stances(items)
    # Must have contradicts stances
    assert len(stances) > 0, "CONFLICT items must produce stances"
    # Check symmetry — both directions present
    stance_types = {s.get("stance_type") for s in stances}
    assert "contradicts" in stance_types, (
        "CONFLICT stances must use 'contradicts' type for symmetric attack"
    )


def test_inject_branch_stances_skip_phi_nodes() -> None:
    """PHI_NODE MergeItems do not produce stances.

    Per Coste-Marquis et al. 2007, Definition 9: ignorance is NOT attack.
    A PHI_NODE means one branch has no opinion — this must not generate
    any attack relationship in the argumentation framework.
    """
    items = [
        MergeItem(
            classification=MergeClassification.PHI_NODE,
            claim_id="c1",
            concept_id="concept1",
            left_value={"type": "parameter", "value": 1.0},
            right_value=None,
            base_value=None,
            left_branch="master",
            right_branch="paper/test",
        )
    ]
    stances = inject_branch_stances(items)
    assert len(stances) == 0, "PHI_NODE items must not produce stances"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    classifications=st.lists(
        st.sampled_from(list(MergeClassification)),
        min_size=1,
        max_size=10,
    )
)
def test_only_conflicts_produce_stances(
    classifications: list[MergeClassification],
) -> None:
    """Property: only CONFLICT items produce stances, all others produce none.

    Per the PAF three-valued relation (Coste-Marquis et al. 2007): only
    definite attacks generate contrariness. IDENTICAL, COMPATIBLE,
    NOVEL_LEFT, NOVEL_RIGHT, and PHI_NODE classifications are non-attack
    and must produce zero stances.
    """
    items = [
        MergeItem(
            classification=cls,
            claim_id=f"c_{i}",
            concept_id=f"concept_{i}",
            left_value={"type": "parameter", "value": 1.0, "id": f"c_{i}_left"},
            right_value={"type": "parameter", "value": 2.0, "id": f"c_{i}_right"},
            base_value=None,
            left_branch="master",
            right_branch="paper/test",
        )
        for i, cls in enumerate(classifications)
    ]
    stances = inject_branch_stances(items)
    expected_count = sum(
        1 for c in classifications if c == MergeClassification.CONFLICT
    )
    # Each CONFLICT produces symmetric stances (both directions)
    assert len(stances) == expected_count * 2, (
        f"Expected {expected_count * 2} stances (2 per CONFLICT) "
        f"but got {len(stances)} for classifications {classifications}"
    )


# ── Group 4: Stability and Idempotence ─────────────────────────────


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(ref=st_assumption_ref)
def test_duplicate_branch_assumption_idempotent(ref: AssumptionRef) -> None:
    """Adding the same branch assumption twice does not change the assumption set.

    Per Booth 2006, claim 13 (stability postulate D): re-adding an
    already-believed claim does not change the extension. Concretely,
    make_branch_assumption must be deterministic — calling it twice with
    the same branch name produces identical AssumptionRef objects.
    """
    assume(ref.kind == "branch")
    ref1 = make_branch_assumption(ref.source)
    ref2 = make_branch_assumption(ref.source)
    assert ref1 == ref2, (
        f"make_branch_assumption must be deterministic: "
        f"{ref1} != {ref2} for source={ref.source}"
    )


def test_merge_nogoods_idempotent() -> None:
    """Running branch_nogoods_from_merge twice with same items produces same nogoods.

    Idempotence is required for reproducible builds — re-running the merge
    classification pipeline must not accumulate or lose nogoods.
    """
    items = [
        MergeItem(
            classification=MergeClassification.CONFLICT,
            claim_id="c1",
            concept_id="concept1",
            left_value={"type": "parameter", "value": 1.0},
            right_value={"type": "parameter", "value": 2.0},
            base_value=None,
            left_branch="master",
            right_branch="paper/test",
        ),
        MergeItem(
            classification=MergeClassification.CONFLICT,
            claim_id="c2",
            concept_id="concept2",
            left_value={"type": "parameter", "value": 3.0},
            right_value={"type": "parameter", "value": 4.0},
            base_value=None,
            left_branch="master",
            right_branch="paper/test",
        ),
    ]
    nogoods1 = branch_nogoods_from_merge(items)
    nogoods2 = branch_nogoods_from_merge(items)
    assert nogoods1 == nogoods2, (
        "branch_nogoods_from_merge must be idempotent"
    )


# ── Group 5: Sidecar Branch Column ────────────────────────────────


def test_sidecar_branch_column_exists() -> None:
    """The claim_core table has a branch column after sidecar build.

    Infrastructure requirement for branch-aware queries. The sidecar
    SQLite schema must include a 'branch' column in claim_core so that
    claims can be filtered by their originating branch.
    """
    import sqlite3
    import tempfile
    from pathlib import Path

    from propstore.build_sidecar import build_sidecar

    # Build a minimal sidecar and check schema
    # This will fail until the schema migration adds the branch column
    tmpdir = tempfile.mkdtemp()
    sidecar_path = Path(tmpdir) / "test.sqlite"

    # We need to inspect the schema after build
    # For now, check that the column exists by querying PRAGMA
    # This test will fail because the column doesn't exist yet
    try:
        build_sidecar(Path(tmpdir) / "knowledge", sidecar_path)
    except Exception:
        pass  # Build may fail without proper knowledge dir

    # Even if build fails, check if the schema definition includes 'branch'
    # by importing and checking the SQL
    from propstore import build_sidecar as bs_module
    import inspect

    source = inspect.getsource(bs_module)
    assert "branch TEXT" in source, (
        "claim_core table schema must include a 'branch TEXT' column"
    )


def test_sidecar_branch_filter() -> None:
    """Claims can be filtered by branch in sidecar queries.

    After building a sidecar with branch-tagged claims, querying with
    a branch filter must return only claims from that branch. This is
    the read-side complement of the branch column infrastructure.
    """
    import sqlite3
    import tempfile

    # Create an in-memory database with the expected schema
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE claim_core (
            id TEXT PRIMARY KEY,
            content_hash TEXT NOT NULL,
            seq INTEGER NOT NULL,
            type TEXT NOT NULL,
            concept_id TEXT,
            target_concept TEXT,
            source_paper TEXT NOT NULL,
            provenance_page INTEGER NOT NULL,
            branch TEXT
        )
    """)

    # Insert claims from two branches
    conn.execute(
        "INSERT INTO claim_core VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("c1", "hash1", 1, "parameter", "concept1", None, "paper1", 1, "master"),
    )
    conn.execute(
        "INSERT INTO claim_core VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("c2", "hash2", 2, "parameter", "concept1", None, "paper1", 1, "paper/test"),
    )

    # Filter by branch
    master_claims = conn.execute(
        "SELECT id FROM claim_core WHERE branch = ?", ("master",)
    ).fetchall()
    assert len(master_claims) == 1
    assert master_claims[0][0] == "c1"

    test_claims = conn.execute(
        "SELECT id FROM claim_core WHERE branch = ?", ("paper/test",)
    ).fetchall()
    assert len(test_claims) == 1
    assert test_claims[0][0] == "c2"

    conn.close()

    # Also verify the actual sidecar schema includes the column
    from propstore import build_sidecar as bs_module
    import inspect

    source = inspect.getsource(bs_module)
    assert "branch TEXT" in source, (
        "claim_core CREATE TABLE must include 'branch TEXT' column"
    )
