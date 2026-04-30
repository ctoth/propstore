from __future__ import annotations

from pathlib import Path
from typing import get_type_hints


def test_workstream_k_done_contract() -> None:
    for name in ("embed", "classify", "relate", "calibrate"):
        assert not Path("propstore", f"{name}.py").exists()
        assert Path("propstore", "heuristic", f"{name}.py").exists()

    propstore_sources = "\n".join(
        path.read_text()
        for path in Path("propstore").rglob("*.py")
        if "__pycache__" not in path.parts
    )
    assert "derive_source_document_trust" not in propstore_sources
    assert "_sanitize_model_key" not in propstore_sources

    from propstore.families.documents.sources import SourceTrustDocument
    from propstore.opinion import Opinion
    from propstore.source_trust_argumentation import calibrate_source_trust

    assert get_type_hints(SourceTrustDocument)["prior_base_rate"] == Opinion | None
    assert callable(calibrate_source_trust)


def test_workstream_k_docs_have_no_open_closed_findings() -> None:
    gaps = Path("docs/gaps.md").read_text()
    open_gaps = gaps.split("## Closed gaps", 1)[0]

    assert "dedup_pairs" not in open_gaps
    assert "heuristic logic outside `heuristic/`" not in open_gaps
    assert "trust calibration breaks proposal gate" not in open_gaps
    assert "embedding-key-collision" not in open_gaps
