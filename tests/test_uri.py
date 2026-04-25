from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.repository import Repository
from propstore.uri import ni_uri_for_bytes, tag_uri


_AUTHORITY_CHARS = st.characters(
    whitelist_categories=("Ll", "Lu", "Nd"),
    whitelist_characters=(".", ",", "-"),
)
_TOKEN_CHARS = st.characters(
    whitelist_categories=("Ll", "Lu", "Nd"),
    whitelist_characters=("_", "-", "."),
)
_URI_AUTHORITIES = st.text(_AUTHORITY_CHARS, min_size=1, max_size=32).filter(
    lambda value: value.strip(".,-") != ""
)
_URI_TOKENS = st.text(_TOKEN_CHARS, min_size=1, max_size=32).filter(
    lambda value: value.strip("._-") != ""
)


def test_repository_uri_authority_reads_repo_config(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {"propstore.yaml": b"uri_authority: example.com,2026\n"},
        "Set repository config",
    )

    assert repo.uri_authority == "example.com,2026"


@pytest.mark.property
@given(authority=_URI_AUTHORITIES, kind=_URI_TOKENS, name=st.text(min_size=1, max_size=64))
@settings(deadline=None)
def test_tag_uri_is_deterministic_prefixed_and_normalizes_spaces(
    authority: str,
    kind: str,
    name: str,
) -> None:
    uri = tag_uri(authority, kind, name)

    assert uri == tag_uri(authority, kind, name)
    assert uri.startswith(f"tag:{authority}:")
    assert " " not in uri.rsplit("/", 1)[-1]


@pytest.mark.property
@given(
    authority=_URI_AUTHORITIES,
    kind=_URI_TOKENS,
    left=_URI_TOKENS,
    right=_URI_TOKENS,
    first_ws=st.sampled_from([" ", "\t", "\n", "\r"]),
    second_ws=st.sampled_from([" ", "\t", "\n", "\r"]),
)
@settings(deadline=None)
def test_tag_uri_equivalent_single_whitespace_normalizes_consistently(
    authority: str,
    kind: str,
    left: str,
    right: str,
    first_ws: str,
    second_ws: str,
) -> None:
    assert tag_uri(authority, kind, f"{left}{first_ws}{right}") == tag_uri(
        authority,
        kind,
        f"{left}{second_ws}{right}",
    )


@pytest.mark.property
@given(
    authority=_URI_AUTHORITIES,
    kind=_URI_TOKENS,
    left=_URI_TOKENS,
    right=_URI_TOKENS,
    separator=st.sampled_from(["/", "\\"]),
)
@settings(deadline=None)
def test_tag_uri_path_separators_are_normalized(
    authority: str,
    kind: str,
    left: str,
    right: str,
    separator: str,
) -> None:
    assert tag_uri(authority, kind, f"{left}{separator}{right}") == tag_uri(
        authority,
        kind,
        f"{left}_{right}",
    )


@pytest.mark.property
@given(payload=st.binary(max_size=256))
@settings(deadline=None)
def test_ni_uri_for_bytes_is_deterministic(payload: bytes) -> None:
    assert ni_uri_for_bytes(payload) == ni_uri_for_bytes(payload)


@pytest.mark.property
@given(left=st.binary(max_size=256), right=st.binary(max_size=256))
@settings(deadline=None)
def test_ni_uri_for_bytes_changes_when_payload_changes(left: bytes, right: bytes) -> None:
    assume(left != right)

    assert ni_uri_for_bytes(left) != ni_uri_for_bytes(right)
