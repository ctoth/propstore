"""CLI adapter tests for ``pks claim/concept embed`` and ``... similar``.

Skip-gated on the ``sqlite-vec`` extra; ``litellm`` is replaced by a deterministic
fake embedder so the commands run end-to-end through the root ``cli`` registry
against the shared demo repo. Covers the embed write path, the similarity read
path, and the honest-empty similar result when no index exists.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner, Result

pytest.importorskip("sqlite_vec")

from tests.app_render_helpers import build_demo_repo  # noqa: E402
from propstore.cli import cli  # noqa: E402
from propstore.repository import Repository  # noqa: E402


def _fake_litellm() -> MagicMock:
    litellm = MagicMock()

    def embedding(model: str, input: Sequence[str]) -> MagicMock:
        response = MagicMock()
        response.data = [
            {"embedding": [float(len(text)), float(sum(map(ord, text)) % 97)]}
            for text in input
        ]
        return response

    litellm.embedding.side_effect = embedding
    return litellm


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), *args])


def test_claim_embed_then_similar(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with patch("propstore.heuristic.embed.require_litellm", return_value=_fake_litellm()):
        embed = _invoke(repo, ["claim", "embed", "--model", "fake/model"])
    assert embed.exit_code == 0, embed.output
    assert "Embedded" in embed.output

    similar = _invoke(repo, ["claim", "similar", "p_speed", "--model", "fake/model"])
    assert similar.exit_code == 0, similar.output
    # The other claims appear as neighbours (self excluded).
    assert "o_speed" in similar.output or "mech1" in similar.output


def test_claim_similar_without_index_is_honest(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["claim", "similar", "p_speed"])
    assert result.exit_code == 0, result.output
    assert "No similar claims" in result.output


def test_concept_embed_then_similar(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with patch("propstore.heuristic.embed.require_litellm", return_value=_fake_litellm()):
        embed = _invoke(repo, ["concept", "embed", "--model", "fake/model"])
    assert embed.exit_code == 0, embed.output
    assert "Embedded" in embed.output

    similar = _invoke(repo, ["concept", "similar", "speed", "--model", "fake/model"])
    assert similar.exit_code == 0, similar.output
    assert "distance" in similar.output.lower() or "distance" in similar.output
