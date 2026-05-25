"""Derived world-store meta charter."""

from __future__ import annotations

from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, FamilyCharter, FamilyModel
from quire.families import FamilyDefinition
from quire.versions import VersionId


PROPSTORE_WORLD_SCHEMA_VERSION = 6
PROPSTORE_WORLD_META_KEY = "sidecar"
_WORLD_CONTRACT_VERSION = VersionId("2026.05.20", allow_placeholder=False)


class WorldMeta(FamilyModel):
    pass


WORLD_META_CHARTER: FamilyCharter = FamilyCharter(
        family=FamilyDefinition(
            key="meta",
            name="meta",
            contract_version=_WORLD_CONTRACT_VERSION,
            artifact_family=ArtifactFamily(
                name="propstore-world-meta",
                contract_version=_WORLD_CONTRACT_VERSION,
                doc_type=WorldMeta,
                placement=FlatYamlPlacement(".derived/meta", str),
            ),
            identity_field="key",
        ),
        model=WorldMeta,
        fields=(
            CharterField("key", str, primary_key=True, nullable=False),
            CharterField("schema_version", int, nullable=False),
        ),
        semantic_metadata={"semantic": "propstore.world"},
    )
