from __future__ import annotations

import re
from pathlib import Path


DOCS = (
    Path("algorithms.md"),
    Path("aspic.md"),
    Path("docs/integration.md"),
    Path("docs/structured-argumentation.md"),
    Path("docs/epistemic-operating-system.md"),
    Path("docs/argumentation-package-boundary.md"),
)


PATH_RE = re.compile(r"propstore/[A-Za-z0-9_./-]+(?:\.py)?")


def test_referenced_propstore_paths_exist_or_docs_are_historical() -> None:
    offenders: list[str] = []
    for path in DOCS:
        if not path.exists() or "historical" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for match in PATH_RE.finditer(text):
            ref = match.group(0).rstrip(".,:;)")
            candidate = Path(ref)
            if not candidate.exists():
                offenders.append(f"{path}:{ref}")

    assert offenders == []


def test_integration_doc_has_one_review_policy() -> None:
    text = Path("docs/integration.md").read_text(encoding="utf-8")

    assert not (
        "automated — no human review required" in text
        and "must be manually reviewed and moved" in text
    )


def test_structured_argumentation_doc_does_not_claim_silent_drop() -> None:
    text = Path("docs/structured-argumentation.md").read_text(encoding="utf-8")

    assert "silently dropped" not in text
