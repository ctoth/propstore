"""Quire projection models for claim row views."""

from __future__ import annotations

from typing import Any

from quire.projection_mapping import ProjectionCodec, ProjectionModel, RepeatedPath, ScalarPath

from propstore.core.id_types import to_claim_id, to_concept_id
from propstore.core.relations import coerce_claim_concept_link_role
from propstore.families.claims.declaration import ClaimConceptLinkRow


def _nullable_text(value: Any) -> str | None:
    return None if value is None else str(value)


def _claim_id(value: Any) -> object:
    return None if value is None else to_claim_id(value)


def _concept_id(value: Any) -> object:
    return None if value is None else to_concept_id(value)


def _role_value(value: Any) -> str | None:
    role = coerce_claim_concept_link_role(value)
    return None if role is None else role.value


def _ordinal(value: Any) -> int:
    return 0 if value is None else int(value)


TEXT_CODEC = ProjectionCodec("text", "TEXT", encoder=_nullable_text, decoder=_nullable_text)
CLAIM_ID_CODEC = ProjectionCodec("claim_id", "TEXT", encoder=_nullable_text, decoder=_claim_id)
CONCEPT_ID_CODEC = ProjectionCodec("concept_id", "TEXT", encoder=_nullable_text, decoder=_concept_id)
CLAIM_CONCEPT_LINK_ROLE_CODEC = ProjectionCodec(
    "claim_concept_link_role",
    "TEXT",
    encoder=_role_value,
    decoder=coerce_claim_concept_link_role,
)
ORDINAL_CODEC = ProjectionCodec("integer", "INTEGER", encoder=_ordinal, decoder=_ordinal)


CLAIM_CONCEPT_LINK_ROW_MODEL: ProjectionModel[ClaimConceptLinkRow] = ProjectionModel(
    name="claim_concept_link_row",
    table="claim_concept_link",
    result_type=ClaimConceptLinkRow,
    fields=(
        ScalarPath(("claim_id",), "claim_id", codec=CLAIM_ID_CODEC, nullable=False, missing="raise"),
        ScalarPath(("concept_id",), "concept_id", codec=CONCEPT_ID_CODEC, nullable=False, missing="raise"),
        ScalarPath(("role",), "role", codec=CLAIM_CONCEPT_LINK_ROLE_CODEC, nullable=False, missing="raise"),
        ScalarPath(("ordinal",), "ordinal", codec=ORDINAL_CODEC, nullable=False),
        ScalarPath(("binding_name",), "binding_name", codec=TEXT_CODEC),
    ),
)


CLAIM_CONCEPT_LINKS_PATH = RepeatedPath(
    path=("concept_links",),
    table="claim_concept_link",
    parent_fk="claim_id",
    parent_path=("claim_id",),
    item_parent_path=("claim_id",),
    item_type=ClaimConceptLinkRow,
    fields=(
        ScalarPath(("concept_id",), "concept_id", codec=CONCEPT_ID_CODEC, nullable=False, missing="raise"),
        ScalarPath(("role",), "role", codec=CLAIM_CONCEPT_LINK_ROLE_CODEC, nullable=False, missing="raise"),
        ScalarPath(("ordinal",), "ordinal", codec=ORDINAL_CODEC, nullable=False),
        ScalarPath(("binding_name",), "binding_name", codec=TEXT_CODEC),
    ),
)
