from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "propstore"

DISPLAY_ONLY = {
    Path("propstore/web/html.py"),
    Path("propstore/web/render.py"),
}


def _slice_text(source: str, node: ast.AST) -> str:
    return ast.get_source_segment(source, node) or ""


def test_no_truncated_hex_digest_identity_surfaces() -> None:
    """D-20: persisted identity stores full hashes; truncation is render-only."""

    offenders: list[str] = []
    for path in sorted(PRODUCTION.rglob("*.py")):
        relpath = path.relative_to(ROOT)
        if relpath in DISPLAY_ONLY:
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Subscript):
                continue
            text = _slice_text(source, node)
            if "hexdigest()" in text and "[:" in text:
                offenders.append(f"{relpath}:{node.lineno}: {text}")
            if "content_hash" in text and "[:" in text:
                offenders.append(f"{relpath}:{node.lineno}: {text}")

    assert offenders == []
