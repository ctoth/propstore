"""OntoLex-Lemon core objects for concept lexicalization.

The lemon model links linguistic entries (forms, senses) to ontology references
and carries sense-level semantic content (Pustejovsky qualia, Dowty proto-roles,
description kinds). Coreference over description claims is resolved by CONSUMING
the ``argumentation`` package directly for the render-time Dung query; temporal
order is a happens-before partial order (Lamport 1978) with declared-frame
TIMEPOINT projections decided three-valued through ``condition-ir`` — see
:mod:`propstore.core.lemon.coreference` and
:mod:`propstore.core.lemon.temporal`.
"""

from __future__ import annotations

from propstore.core.lemon.coreference import CoreferenceQuery, coreference_query
from propstore.core.lemon.description_kinds import (
    BindingValidation,
    CausalAccount,
    CausalConnectionAssertion,
    CoreferenceMergeArgument,
    DescriptionClaim,
    DescriptionKind,
    DescriptionKindMergeProtocol,
    ParticipantSlot,
    SlotBinding,
    causal_transitivity_allowed,
    coreference_argument,
    validate_slot_bindings,
)
from propstore.core.lemon.forms import LexicalForm, fold_text, require_text
from propstore.core.lemon.proto_roles import (
    GradedEntailment,
    ProtoAgentProperty,
    ProtoPatientProperty,
    ProtoRoleBundle,
    predicted_subject_role,
    proto_agent_weight,
    proto_patient_weight,
)
from propstore.core.lemon.qualia import (
    CoercedReference,
    QualiaReference,
    QualiaRole,
    QualiaStructure,
    TypeConstraint,
    coerce_via_qualia,
    purposive_chain,
    qualia_references,
)
from propstore.core.lemon.references import OntologyReference
from propstore.core.lemon.temporal import (
    AllenRelation,
    AllenVerdict,
    DescriptionTemporalAnchor,
    HappensBeforeAccount,
    HappensBeforeEdge,
    OrderingEvidenceKind,
    OrderingLink,
    TemporalFrame,
    TemporalOrderJudgment,
    TemporalOrderVerdict,
    description_temporal_relation,
    temporal_order,
)
from propstore.core.lemon.types import (
    LexicalEntry,
    LexicalSense,
    lexical_entry_identity_key,
    lexical_form_identity_key,
)

__all__ = [
    "AllenRelation",
    "AllenVerdict",
    "BindingValidation",
    "CausalAccount",
    "CausalConnectionAssertion",
    "CoercedReference",
    "CoreferenceMergeArgument",
    "CoreferenceQuery",
    "DescriptionClaim",
    "DescriptionKind",
    "DescriptionKindMergeProtocol",
    "DescriptionTemporalAnchor",
    "GradedEntailment",
    "HappensBeforeAccount",
    "HappensBeforeEdge",
    "LexicalEntry",
    "LexicalForm",
    "LexicalSense",
    "OntologyReference",
    "OrderingEvidenceKind",
    "OrderingLink",
    "ParticipantSlot",
    "ProtoAgentProperty",
    "ProtoPatientProperty",
    "ProtoRoleBundle",
    "QualiaReference",
    "QualiaRole",
    "QualiaStructure",
    "SlotBinding",
    "TemporalFrame",
    "TemporalOrderJudgment",
    "TemporalOrderVerdict",
    "TypeConstraint",
    "causal_transitivity_allowed",
    "coerce_via_qualia",
    "coreference_argument",
    "coreference_query",
    "description_temporal_relation",
    "fold_text",
    "lexical_entry_identity_key",
    "lexical_form_identity_key",
    "predicted_subject_role",
    "proto_agent_weight",
    "proto_patient_weight",
    "purposive_chain",
    "qualia_references",
    "require_text",
    "temporal_order",
    "validate_slot_bindings",
]
