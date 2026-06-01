from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def test_trusty_uri_rejects_sha1_emission() -> None:
    from propstore.provenance.trusty import compute_ni_uri

    with pytest.raises(ValueError):
        compute_ni_uri(b"abc", algorithm="sha-1")


def test_provenance_module_no_longer_templates_sha1_ni_uris() -> None:
    provenance = importlib.import_module("propstore.provenance")
    source = Path(provenance.__file__).read_text(encoding="utf-8")

    assert "_sha_text" not in source
    assert "ni:///sha-1;" not in source
