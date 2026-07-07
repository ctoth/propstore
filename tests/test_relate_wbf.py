"""classify.py fuses categorical and corpus opinions via doxa's WBF dispatcher.

``Opinion.fuse`` is a classmethod taking ``*opinions``; calling it through an
instance silently drops the receiver (``a.fuse(b)`` fuses only ``b``). These
tests pin the classmethod call shape and, behaviorally, that the category
opinion actually contributes to the resolved stance opinion.
"""

from __future__ import annotations

from pathlib import Path

from doxa import Opinion

from propstore.heuristic.calibrate import (
    CalibrationSource,
    CategoryPrior,
    CategoryPriorRegistry,
    CorpusCalibrator,
    categorical_to_opinion,
)
from propstore.provenance import Provenance, ProvenanceStatus


def _category_prior_registry() -> CategoryPriorRegistry:
    provenance = Provenance(
        status=ProvenanceStatus.VACUOUS,
        witnesses=(),
        operations=("test_category_prior",),
    )
    return CategoryPriorRegistry(
        {
            category: CategoryPrior(
                category=category,
                value=value,
                source=CalibrationSource.USER_DEFAULT,
                provenance=provenance,
            )
            for category, value in {
                "strong": 0.7,
                "moderate": 0.5,
                "weak": 0.3,
                "none": 0.1,
            }.items()
        }
    )


class TestRelateFuseEquivalence:
    def test_fuse_matches_wbf_for_two_non_dogmatic_inputs(self) -> None:
        a = Opinion(0.5, 0.1, 0.4, 0.5)
        b = Opinion(0.3, 0.3, 0.4, 0.5)
        assert Opinion.fuse(a, b) == Opinion.wbf(a, b)

    def test_fuse_combines_both_operands(self) -> None:
        a = Opinion(0.5, 0.1, 0.4, 0.5)
        b = Opinion(0.3, 0.3, 0.4, 0.5)
        fused = Opinion.fuse(a, b)
        assert fused != a
        assert fused != b

    def test_fuse_handles_dogmatic_categorical(self) -> None:
        categorical = Opinion.dogmatic_true(0.5)
        corpus = Opinion(0.3, 0.3, 0.4, 0.5)
        result = Opinion.fuse(categorical, corpus)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    def test_fuse_handles_both_dogmatic(self) -> None:
        a = Opinion.dogmatic_true(0.5)
        b = Opinion.dogmatic_false(0.5)
        result = Opinion.fuse(a, b)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6


class TestResolvedOpinionFusesCategoryEvidence:
    def test_category_opinion_contributes_to_corpus_fusion(self) -> None:
        from propstore.heuristic.classify import _resolved_opinion

        registry = _category_prior_registry()
        counts = {(1, "strong"): (7, 10)}
        reference_distances = [0.1, 0.2, 0.3, 0.4, 0.5]
        embedding_distance = 0.25

        category = categorical_to_opinion(
            "strong", 1, calibration_counts=counts, prior_registry=registry
        )
        assert isinstance(category, Opinion)
        corpus = CorpusCalibrator(
            reference_distances, corpus_base_rate=category.a
        ).to_opinion(embedding_distance)

        resolved, unresolved, _provenance = _resolved_opinion(
            "strong",
            reference_distances=reference_distances,
            embedding_distance=embedding_distance,
            calibration_counts=counts,
            category_prior_registry=registry,
        )

        assert unresolved is None
        assert resolved == Opinion.fuse(category, corpus)
        # The receiver-dropping bug (`opinion.fuse(corpus)`) returned the
        # corpus opinion unchanged, discarding the LLM category evidence.
        assert resolved != corpus

    def test_classify_calls_fuse_as_classmethod(self) -> None:
        import propstore.heuristic.classify as classify_module

        source = Path(classify_module.__file__).read_text(encoding="utf-8")
        assert "from doxa import Opinion" in source
        assert "Opinion.fuse(" in source
        assert "opinion.fuse(" not in source
