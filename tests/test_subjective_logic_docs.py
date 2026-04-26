from __future__ import annotations

from pathlib import Path


def test_subjective_logic_docs_do_not_reintroduce_half_prior_defaults() -> None:
    text = (
        Path(__file__).resolve().parents[1] / "docs" / "subjective-logic.md"
    ).read_text(encoding="utf-8")

    forbidden = [
        "defaults to 0.5",
        "total ignorance defaults",
        "vacuous opinions are the honest default",
        "without calibration data: returns a vacuous opinion",
        "category-derived base rate",
        "backward compatibility with pre-opinion data",
    ]
    normalized = text.lower()

    for phrase in forbidden:
        assert phrase not in normalized
