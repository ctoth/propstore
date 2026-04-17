"""OntoLex-Lemon core objects for concept lexicalization."""

from propstore.core.lemon.description_kinds import (
    CausalAccount,
    CausalConnectionAssertion,
    CoreferenceQuery,
    DescriptionClaim,
    DescriptionKind,
    MergeArgument,
    ParticipantSlot,
    SlotBinding,
    causal_transitivity_allowed,
    coreference_query,
    coreference_argument,
    validate_slot_bindings,
)
from propstore.core.lemon.forms import LexicalForm
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
    DescriptionTemporalAnchor,
    description_temporal_relation,
)
from propstore.core.lemon.types import (
    LexicalEntry,
    LexicalSense,
    lexical_entry_identity_key,
    lexical_form_identity_key,
)

__all__ = [
    "CausalAccount",
    "CausalConnectionAssertion",
    "CoercedReference",
    "CoreferenceQuery",
    "DescriptionClaim",
    "DescriptionKind",
    "DescriptionTemporalAnchor",
    "GradedEntailment",
    "LexicalEntry",
    "LexicalForm",
    "LexicalSense",
    "MergeArgument",
    "OntologyReference",
    "ParticipantSlot",
    "ProtoAgentProperty",
    "ProtoPatientProperty",
    "ProtoRoleBundle",
    "QualiaReference",
    "QualiaRole",
    "QualiaStructure",
    "SlotBinding",
    "TypeConstraint",
    "AllenRelation",
    "causal_transitivity_allowed",
    "coerce_via_qualia",
    "coreference_query",
    "coreference_argument",
    "description_temporal_relation",
    "lexical_entry_identity_key",
    "lexical_form_identity_key",
    "predicted_subject_role",
    "proto_agent_weight",
    "proto_patient_weight",
    "purposive_chain",
    "qualia_references",
    "validate_slot_bindings",
]
