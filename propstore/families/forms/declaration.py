"""Form world-store family charters."""

from __future__ import annotations

from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, CharterIndex, FamilyCharter
from quire.families import FamilyDefinition

from propstore.families.forms.stages import Form, FormAlgebra
from propstore.families.meta.declaration import _WORLD_CONTRACT_VERSION


FORMS_CHARTERS: tuple[FamilyCharter, FamilyCharter] = (
        FamilyCharter(
            family=FamilyDefinition(
                key="form",
                name="form",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-form",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=Form,
                    placement=FlatYamlPlacement(".derived/form", str),
                ),
                identity_field="name",
            ),
            model=Form,
            fields=(
                CharterField("name", str, primary_key=True, nullable=False),
                CharterField("kind", str, nullable=False),
                CharterField("unit_symbol", str),
                CharterField("is_dimensionless", int, nullable=False, default_sql="0"),
                CharterField("dimensions", str),
            ),
            semantic_metadata={"semantic": "propstore.world"},
        ),
        FamilyCharter(
            family=FamilyDefinition(
                key="form_algebra",
                name="form_algebra",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-form_algebra",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=FormAlgebra,
                    placement=FlatYamlPlacement(".derived/form_algebra", str),
                ),
                identity_field="id",
            ),
            model=FormAlgebra,
            fields=(
                CharterField("id", int, primary_key=True, nullable=False),
                CharterField("output_form", str, nullable=False),
                CharterField("input_forms", str, nullable=False),
                CharterField("operation", str, nullable=False),
                CharterField("source_concept_id", str),
                CharterField("source_formula", str),
                CharterField("dim_verified", int, nullable=False, default_sql="1"),
            ),
            indexes=(CharterIndex("idx_form_algebra_output", ("output_form",)),),
            semantic_metadata={"semantic": "propstore.world"},
        ),
    )
