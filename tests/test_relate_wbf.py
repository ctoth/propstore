"""classify.py fuses categorical and corpus opinions via doxa's WBF dispatcher."""

from __future__ import annotations

from pathlib import Path

from doxa import Opinion


class TestRelateFuseEquivalence:
    def test_fuse_matches_wbf_for_two_non_dogmatic_inputs(self) -> None:
        a = Opinion(0.5, 0.1, 0.4, 0.5)
        b = Opinion(0.3, 0.3, 0.4, 0.5)
        assert a.fuse(b) == a.wbf(b)

    def test_fuse_handles_dogmatic_categorical(self) -> None:
        categorical = Opinion.dogmatic_true(0.5)
        corpus = Opinion(0.3, 0.3, 0.4, 0.5)
        result = categorical.fuse(corpus)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    def test_fuse_handles_both_dogmatic(self) -> None:
        a = Opinion.dogmatic_true(0.5)
        b = Opinion.dogmatic_false(0.5)
        result = a.fuse(b)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    def test_classify_uses_doxa_fuse(self) -> None:
        import propstore.heuristic.classify as classify_module

        source = Path(classify_module.__file__).read_text(encoding="utf-8")
        assert "from doxa import Opinion" in source
        assert ".fuse(" in source
