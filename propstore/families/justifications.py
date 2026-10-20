"""The ``Justification`` entity — an authored argument linking premises to a claim.

A justification records that a conclusion claim is supported by a body of premise
claims under a rule kind/strength. Its ``conclusion`` and ``premises`` are
foreign keys into the claim family, declared as
:class:`~quire.references.ForeignKeySpec` annotations on the fields so the family
registry's foreign-key graph is derived (PLAN.md §12.6). The class IS the
document; there is no ``JustificationDocument`` second spelling.
"""

from __future__ import annotations

from typing import Annotated

import msgspec

from quire.charter_class import CharterDoc, charter, charter_field
from quire.references import ForeignKeySpec

from propstore.families import SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION


def _transport_identity(document: Justification) -> Justification:
    from propstore.families.identity.justifications import derive_justification_artifact_id

    return msgspec.structs.replace(
        document,
        justification_id=derive_justification_artifact_id(
            conclusion=document.conclusion,
            premises=document.premises,
            rule_kind=document.rule_kind,
            rule_strength=document.rule_strength,
        ),
    )


@charter(
    key="justification",
    name="justification",
    contract_version="2026.10.20",
    placement="justification",
    identity_field="justification_id",
    transport_identity=_transport_identity,
)
class Justification(CharterDoc):
    """An authored ``premises ⊢ conclusion`` justification over claims."""

    # A non-reported licence makes its conclusion inferred, rather than an
    # unconditional premise. An independent report requires an explicit
    # reported_claim licence. Withdrawal disables support, not this document.
    justification_id: Annotated[str, charter_field(primary_key=True)]
    conclusion: Annotated[
        str | None,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="justification_conclusion",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="justification",
                source_field="conclusion",
                target_family="claim",
                target_field="claim_id",
                required=False,
            )
        ),
    ] = None
    premises: Annotated[
        tuple[str, ...],
        charter_field(
            json=True,
            foreign_keys=(
                ForeignKeySpec(
                    name="justification_premises",
                    contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                    source_family="justification",
                    source_field="premises[]",
                    target_family="claim",
                    target_field="claim_id",
                    required=False,
                    many=True,
                ),
            ),
        ),
    ] = ()
    rule_kind: str | None = None
    rule_strength: str | None = None
