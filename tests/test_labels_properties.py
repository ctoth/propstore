"""Property tests for the ATMS label kernel (de Kleer 1986).

The label kernel (core/labels.py, world/labelled.py) is the foundation
of the ATMS engine. These tests verify the formal invariants that
de Kleer 1986 §3 requires of label propagation:

- Label minimality: no environment in a label subsumes another
- combine_labels (cross-product union) is commutative and associative
- merge_labels (alternative supports) is commutative and idempotent
- NogoodSet exclusion is sound: excluded environments are supersets of nogoods
- normalize_environments is idempotent
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.core.labels import (
    EnvironmentKey,
    Label,
    NogoodSet,
    normalize_environments,
)
from propstore.core.labels import combine_labels, merge_labels


# ── Hypothesis strategies ─────────────────────────────────────────


_ASSUMPTION_IDS = st.text(alphabet="abcdef", min_size=1, max_size=3)


@st.composite
def environment_keys(draw, max_assumptions: int = 4):
    """Generate an EnvironmentKey with 0..max_assumptions assumptions."""
    ids = draw(
        st.frozensets(_ASSUMPTION_IDS, min_size=0, max_size=max_assumptions)
    )
    return EnvironmentKey(tuple(ids))


@st.composite
def labels(draw, max_envs: int = 4, max_assumptions: int = 3):
    """Generate a Label (auto-normalized to minimal antichain)."""
    envs = draw(
        st.lists(
            environment_keys(max_assumptions=max_assumptions),
            min_size=0,
            max_size=max_envs,
        )
    )
    return Label(tuple(envs))


@st.composite
def nogood_sets(draw, max_nogoods: int = 3, max_assumptions: int = 3):
    """Generate a NogoodSet."""
    envs = draw(
        st.lists(
            environment_keys(max_assumptions=max_assumptions),
            min_size=0,
            max_size=max_nogoods,
        )
    )
    return NogoodSet(tuple(envs))


_PROP_SETTINGS = settings(deadline=None)


# ── 1. Label minimality (de Kleer 1986 §3, invariant 1) ──────────


class TestLabelMinimality:
    """Every Label must be a minimal antichain: no environment subsumes another.

    de Kleer 1986 §3: "The label of each node is a minimal set of environments."
    """

    @given(labels())
    @_PROP_SETTINGS
    def test_no_environment_subsumes_another(self, label):
        """No environment in a label is a subset of another."""
        envs = label.environments
        for i, env_a in enumerate(envs):
            for j, env_b in enumerate(envs):
                if i != j:
                    assert not env_a.subsumes(env_b), (
                        f"Environment {env_a} subsumes {env_b} in label — "
                        f"violates minimality"
                    )

    @given(labels())
    @_PROP_SETTINGS
    def test_no_duplicate_environments(self, label):
        """No two environments in a label are identical."""
        seen = set()
        for env in label.environments:
            assert env.assumption_ids not in seen, (
                f"Duplicate environment {env} in label"
            )
            seen.add(env.assumption_ids)


# ── 2. normalize_environments properties ──────────────────────────


class TestNormalizeEnvironments:
    """normalize_environments must be idempotent and produce minimal antichains."""

    @given(st.lists(environment_keys(), min_size=0, max_size=6))
    @_PROP_SETTINGS
    def test_idempotent(self, envs):
        """Normalizing twice gives the same result as once."""
        once = normalize_environments(envs)
        twice = normalize_environments(once)
        assert once == twice

    @given(st.lists(environment_keys(), min_size=0, max_size=6), nogood_sets())
    @_PROP_SETTINGS
    def test_idempotent_with_nogoods(self, envs, nogoods):
        """Normalizing with nogoods is idempotent."""
        once = normalize_environments(envs, nogoods=nogoods)
        twice = normalize_environments(once, nogoods=nogoods)
        assert once == twice

    @given(st.lists(environment_keys(), min_size=0, max_size=6), nogood_sets())
    @_PROP_SETTINGS
    def test_nogoods_exclude_supersets(self, envs, nogoods):
        """Every surviving environment must not be excluded by the NogoodSet."""
        result = normalize_environments(envs, nogoods=nogoods)
        for env in result:
            assert not nogoods.excludes(env), (
                f"Environment {env} survived normalization but is excluded "
                f"by nogood set {nogoods}"
            )

    @given(st.lists(environment_keys(), min_size=0, max_size=6))
    @_PROP_SETTINGS
    def test_result_is_antichain(self, envs):
        """Normalized result is a minimal antichain."""
        result = normalize_environments(envs)
        for i, env_a in enumerate(result):
            for j, env_b in enumerate(result):
                if i != j:
                    assert not env_a.subsumes(env_b)


# ── 3. combine_labels (cross-product union) properties ────────────


class TestCombineLabels:
    """combine_labels is the ATMS "and" operation: cross-product of environments.

    de Kleer 1986 §3: when a datum depends on antecedents A1 AND A2,
    its label is the cross-product of A1's and A2's labels.
    """

    @given(labels(), labels())
    @_PROP_SETTINGS
    def test_commutative(self, label_a, label_b):
        """combine(A, B) == combine(B, A)."""
        ab = combine_labels(label_a, label_b)
        ba = combine_labels(label_b, label_a)
        assert set(ab.environments) == set(ba.environments), (
            f"combine_labels not commutative:\n"
            f"  A⊗B = {ab.environments}\n"
            f"  B⊗A = {ba.environments}"
        )

    @given(labels(max_envs=3), labels(max_envs=3), labels(max_envs=3))
    @_PROP_SETTINGS
    def test_associative(self, a, b, c):
        """combine(combine(A, B), C) == combine(A, combine(B, C))."""
        ab_c = combine_labels(combine_labels(a, b), c)
        a_bc = combine_labels(a, combine_labels(b, c))
        assert set(ab_c.environments) == set(a_bc.environments), (
            f"combine_labels not associative:\n"
            f"  (A⊗B)⊗C = {ab_c.environments}\n"
            f"  A⊗(B⊗C) = {a_bc.environments}"
        )

    @given(labels())
    @_PROP_SETTINGS
    def test_empty_is_identity(self, label):
        """combine(L, Label.empty()) == L."""
        result = combine_labels(label, Label.empty())
        assert set(result.environments) == set(label.environments), (
            f"Label.empty() is not identity:\n"
            f"  input = {label.environments}\n"
            f"  result = {result.environments}"
        )

    @given(labels(), labels())
    @_PROP_SETTINGS
    def test_result_is_minimal(self, label_a, label_b):
        """Combined label is always a minimal antichain."""
        result = combine_labels(label_a, label_b)
        for i, env_a in enumerate(result.environments):
            for j, env_b in enumerate(result.environments):
                if i != j:
                    assert not env_a.subsumes(env_b)

    @given(labels(), labels(), nogood_sets())
    @_PROP_SETTINGS
    def test_nogoods_respected(self, label_a, label_b, nogoods):
        """Combined label with nogoods excludes all nogood environments."""
        result = combine_labels(label_a, label_b, nogoods=nogoods)
        for env in result.environments:
            assert not nogoods.excludes(env)


# ── 4. merge_labels (alternative supports) properties ─────────────


class TestMergeLabels:
    """merge_labels is the ATMS "or" operation: union of alternative supports.

    de Kleer 1986 §3: when a datum has multiple justifications,
    its label is the merge (union + minimize) of all justification labels.
    """

    @given(labels(), labels())
    @_PROP_SETTINGS
    def test_commutative(self, label_a, label_b):
        """merge([A, B]) == merge([B, A])."""
        ab = merge_labels([label_a, label_b])
        ba = merge_labels([label_b, label_a])
        assert set(ab.environments) == set(ba.environments)

    @given(labels())
    @_PROP_SETTINGS
    def test_idempotent(self, label):
        """merge([L, L]) == L."""
        result = merge_labels([label, label])
        assert set(result.environments) == set(label.environments)

    @given(labels(), labels())
    @_PROP_SETTINGS
    def test_result_is_minimal(self, label_a, label_b):
        """Merged label is always a minimal antichain."""
        result = merge_labels([label_a, label_b])
        for i, env_a in enumerate(result.environments):
            for j, env_b in enumerate(result.environments):
                if i != j:
                    assert not env_a.subsumes(env_b)

    @given(labels())
    @_PROP_SETTINGS
    def test_superset_of_inputs(self, label):
        """Merging with empty label preserves all environments of input."""
        result = merge_labels([label, Label(())])
        # Every env in the input should be represented
        # (either directly or subsumed by a more general env in result)
        for env in label.environments:
            assert any(
                existing.subsumes(env) for existing in result.environments
            ), f"Lost environment {env} after merge"

    @given(labels(), labels(), nogood_sets())
    @_PROP_SETTINGS
    def test_nogoods_respected(self, label_a, label_b, nogoods):
        """Merged label with nogoods excludes all nogood environments."""
        result = merge_labels([label_a, label_b], nogoods=nogoods)
        for env in result.environments:
            assert not nogoods.excludes(env)


# ── 5. EnvironmentKey properties ──────────────────────────────────


class TestEnvironmentKey:
    """EnvironmentKey invariants."""

    @given(environment_keys(), environment_keys())
    @_PROP_SETTINGS
    def test_union_commutative(self, a, b):
        """Union of environment keys is commutative."""
        ab = a.union(b)
        ba = b.union(a)
        assert ab.assumption_ids == ba.assumption_ids

    @given(environment_keys())
    @_PROP_SETTINGS
    def test_self_subsumes(self, env):
        """Every environment subsumes itself."""
        assert env.subsumes(env)

    @given(environment_keys(), environment_keys())
    @_PROP_SETTINGS
    def test_subsumes_is_subset_relation(self, a, b):
        """subsumes(a, b) iff a's assumptions are a subset of b's."""
        expected = set(a.assumption_ids).issubset(set(b.assumption_ids))
        assert a.subsumes(b) == expected

    @given(environment_keys())
    @_PROP_SETTINGS
    def test_assumptions_sorted_and_deduplicated(self, env):
        """EnvironmentKey always stores sorted, deduplicated assumption IDs."""
        ids = env.assumption_ids
        assert ids == tuple(sorted(ids))
        assert len(ids) == len(set(ids))
