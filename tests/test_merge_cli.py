"""CLI tests for formal merge inspection and execution."""

from __future__ import annotations

from copy import deepcopy

import yaml
import pytest
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from propstore.merge.merge_classifier import build_merge_framework
from propstore.merge.merge_report import summarize_merge_framework
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import normalize_claims_payload


def _param_claim(
    cid: str,
    concept: str,
    value: float,
    *,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "parameter",
        "concept": concept,
        "value": value,
        "unit": "K",
        "concepts": [concept],
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def _snapshot(repo: Repository) -> RepositorySnapshot:
    return repo.snapshot
