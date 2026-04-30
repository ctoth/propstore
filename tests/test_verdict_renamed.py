from __future__ import annotations

from pathlib import Path


TARGETS = (
    Path("propstore/grounding/grounder.py"),
    Path("propstore/grounding/bundle.py"),
    Path("propstore/sidecar/rules.py"),
    Path("propstore/world/atms.py"),
)


def test_grounding_domain_terms_do_not_use_verdict() -> None:
    offenders = [
        f"{path}:verdict"
        for path in TARGETS
        if "verdict" in path.read_text(encoding="utf-8").casefold()
    ]

    assert offenders == []
