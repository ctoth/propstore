from __future__ import annotations

from pathlib import Path

import yaml
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.cli.repository import Repository
from propstore.uri import ni_uri_for_bytes, tag_uri


def test_repository_uri_authority_reads_repo_config(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.config_path.write_text("uri_authority: example.com,2026\n", encoding="utf-8")

    assert repo.uri_authority == "example.com,2026"


def test_tag_uri_uses_configured_authority() -> None:
    assert tag_uri("example.com,2026", "source", "Demo Source") == (
        "tag:example.com,2026:source/Demo_Source"
    )


@given(payload=st.binary(max_size=256))
@settings(max_examples=50, deadline=None)
def test_ni_uri_for_bytes_is_deterministic(payload: bytes) -> None:
    assert ni_uri_for_bytes(payload) == ni_uri_for_bytes(payload)


@given(left=st.binary(max_size=256), right=st.binary(max_size=256))
@settings(max_examples=50, deadline=None)
def test_ni_uri_for_bytes_changes_when_payload_changes(left: bytes, right: bytes) -> None:
    assume(left != right)

    assert ni_uri_for_bytes(left) != ni_uri_for_bytes(right)
