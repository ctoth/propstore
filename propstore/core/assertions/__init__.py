"""Core situated assertion reference types."""

from __future__ import annotations

from propstore.core.assertions.codec import AssertionCanonicalRecord
from propstore.core.assertions.conversion import (
    AssertionSourceRecord,
    assertion_source_record_from_payload,
)
from propstore.core.assertions.refs import (
    UNCONDITIONAL_CONDITION_REF,
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion, derive_assertion_id

__all__ = [
    "AssertionCanonicalRecord",
    "AssertionSourceRecord",
    "UNCONDITIONAL_CONDITION_REF",
    "ConditionRef",
    "ContextReference",
    "ProvenanceGraphRef",
    "SituatedAssertion",
    "assertion_source_record_from_payload",
    "derive_assertion_id",
]
