from __future__ import annotations

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.claims import claim_file_payload
from propstore.repository import Repository
from tests.git_store_helpers import init_store
from propstore.merge.merge_commit import create_merge_commit
from propstore.storage.snapshot import RepositorySnapshot
from tests.family_helpers import load_claim_files
from tests.ws_l_merge_helpers import claim_payloads


def _obs_claim(claim_id: str, statement: str) -> dict:
    return {
        "id": claim_id,
        "type": "observation",
        "statement": statement,
        "concepts": ["concept_x"],
        "provenance": {"paper": "test_paper", "page": 1},
    }


def _snapshot(root: Path) -> RepositorySnapshot:
    return RepositorySnapshot(Repository(root))


_PRINTABLE = st.characters(min_codepoint=32, max_codepoint=126)
