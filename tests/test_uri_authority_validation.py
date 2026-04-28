from __future__ import annotations

from pathlib import Path

import pytest

from propstore.repository import Repository
from propstore.uri import DEFAULT_URI_AUTHORITY, tag_uri
from propstore.uri_authority import (
    MalformedTaggingAuthority,
    TaggingAuthority,
    parse_tagging_authority,
)


@pytest.mark.parametrize(
    "authority",
    [
        "",
        "no_comma_no_date",
        "local@propstore",
        "local@,2026",
        "local@propstore,not-a-date",
        "contains spaces,2026",
        "contains:colon,2026",
        "contains/slash,2026",
        "x" * 1024,
    ],
)
def test_malformed_tagging_authorities_are_rejected(authority: str) -> None:
    with pytest.raises(MalformedTaggingAuthority):
        parse_tagging_authority(authority)

    with pytest.raises(MalformedTaggingAuthority):
        tag_uri(authority, "source", "example")


@pytest.mark.parametrize(
    "authority",
    [
        "local@propstore,2026",
        "q.example,2026-04-27",
        "example.com,2000",
    ],
)
def test_valid_tagging_authorities_parse(authority: str) -> None:
    parsed = parse_tagging_authority(authority)

    assert isinstance(parsed, TaggingAuthority)
    assert str(parsed) == authority
    assert tag_uri(parsed, "source", "example").startswith(f"tag:{authority}:")


def test_default_uri_authority_is_typed() -> None:
    assert isinstance(DEFAULT_URI_AUTHORITY, TaggingAuthority)


def test_repository_config_validates_uri_authority_at_load(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {"propstore.yaml": b"uri_authority: contains spaces,2026\n"},
        "Set malformed repository config",
    )

    with pytest.raises(MalformedTaggingAuthority):
        _ = repo.config
