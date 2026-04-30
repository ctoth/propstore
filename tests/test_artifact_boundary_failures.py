from types import SimpleNamespace

import pytest

from quire.documents import decode_yaml_mapping
from propstore.artifact_verification import _verify_origin


def test_decode_yaml_mapping_rejects_yaml_null():
    with pytest.raises(ValueError, match="expected a YAML mapping"):
        decode_yaml_mapping(b"null\n", source="artifact.yaml")


def test_decode_yaml_mapping_rejects_false_scalar():
    with pytest.raises(ValueError, match="expected a YAML mapping"):
        decode_yaml_mapping(b"false\n", source="artifact.yaml")


def test_origin_verification_rejects_malformed_origin(tmp_path):
    repo = SimpleNamespace(root=tmp_path / "knowledge")

    with pytest.raises(ValueError, match="origin"):
        _verify_origin(repo, "source", {"origin": []})
