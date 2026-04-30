from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st


@given(st.binary(min_size=0, max_size=512))
def test_trusty_uri_sha256_round_trips(payload: bytes) -> None:
    from propstore.provenance.trusty import compute_ni_uri, verify_ni_uri

    uri = compute_ni_uri(payload)

    assert uri.startswith("ni:///sha-256;")
    assert verify_ni_uri(uri, payload) is True
    assert verify_ni_uri(uri, payload + b"\0") is False


def test_trusty_uri_rejects_sha1_emission() -> None:
    from propstore.provenance.trusty import compute_ni_uri

    with pytest.raises(ValueError):
        compute_ni_uri(b"abc", algorithm="sha-1")


def test_provenance_module_no_longer_templates_sha1_ni_uris() -> None:
    provenance = importlib.import_module("propstore.provenance")
    source = Path(provenance.__file__).read_text(encoding="utf-8")

    assert "_sha_text" not in source
    assert "ni:///sha-1;" not in source
