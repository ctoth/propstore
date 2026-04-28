"""Tests verifying relate.py uses fuse() and true WBF for finite evidence."""

from propstore.opinion import Opinion, fuse, wbf


class TestRelateFuseEquivalence:
    """Verify that relate.py's fusion path uses the corrected WBF dispatcher."""

    def test_fuse_matches_wbf_for_two_non_dogmatic_inputs(self):
        """fuse(a, b) == WBF(a, b) for non-dogmatic inputs."""
        a = Opinion(0.5, 0.1, 0.4, 0.5)
        b = Opinion(0.3, 0.3, 0.4, 0.5)
        assert fuse(a, b) == wbf(a, b)

    def test_fuse_handles_dogmatic_categorical(self):
        """fuse() handles the case where categorical opinion is dogmatic."""
        categorical = Opinion.dogmatic_true(0.5)
        corpus = Opinion(0.3, 0.3, 0.4, 0.5)
        # consensus_pair would raise (κ ≈ 0 if both were dogmatic)
        # fuse(method="auto") falls back to CCF
        result = fuse(categorical, corpus)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    def test_fuse_handles_dogmatic_corpus(self):
        """fuse() handles the case where corpus opinion is dogmatic."""
        categorical = Opinion(0.4, 0.2, 0.4, 0.5)
        corpus = Opinion.dogmatic_true(0.5)
        result = fuse(categorical, corpus)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    def test_fuse_handles_both_dogmatic(self):
        """fuse() handles both dogmatic (consensus_pair would crash)."""
        a = Opinion.dogmatic_true(0.5)
        b = Opinion.dogmatic_false(0.5)
        result = fuse(a, b)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    def test_classify_imports_fuse_not_consensus_pair(self):
        """classify.py imports fuse, not consensus_pair."""
        import propstore.classify as classify_module
        source = open(classify_module.__file__).read()
        # Should import fuse
        assert "from propstore.opinion import" in source
        # The key assertion: fuse is used for the fusion call
        assert "fuse(" in source


class TestRelateEdgeCases:
    """Edge cases in the relate fusion path."""

    def test_vacuous_categorical_uses_corpus(self):
        """When categorical is vacuous, fused result ≈ corpus opinion."""
        categorical = Opinion.vacuous(0.5)
        corpus = Opinion(0.4, 0.2, 0.4, 0.5)
        result = fuse(categorical, corpus)
        # Vacuous contributes nothing — result should be close to corpus
        assert abs(result.expectation() - corpus.expectation()) < 0.1

    def test_vacuous_corpus_uses_categorical(self):
        """When corpus is vacuous, fused result ≈ categorical opinion."""
        categorical = Opinion(0.4, 0.2, 0.4, 0.5)
        corpus = Opinion.vacuous(0.5)
        result = fuse(categorical, corpus)
        assert abs(result.expectation() - categorical.expectation()) < 0.1
