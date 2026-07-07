"""Core situated assertion reference types.

This package carries two cooperating surfaces:

* the situated-assertion subsystem proper — :class:`SituatedAssertion` and its
  reference types (:class:`ContextReference`, :class:`ConditionRef`,
  :class:`ProvenanceGraphRef`), the canonical serialization record
  (:class:`AssertionCanonicalRecord`), and the structural source boundary
  (:class:`AssertionSourceRecord`);
* the claim-node assertion-identity helpers (:func:`claim_node_assertion_id` and
  friends) that the ATMS engine uses to collapse identical claim content to one
  node. These pre-date the package conversion and are re-exported unchanged so
  existing importers (``propstore.world.atms``) keep working.
"""

from __future__ import annotations

from propstore.core.assertions.claim_nodes import (
    claim_node_assertion_id,
    claim_node_content,
    claim_node_context_id,
    content_digest,
    semantic_content,
)
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
    "UNCONDITIONAL_CONDITION_REF",
    "AssertionCanonicalRecord",
    "AssertionSourceRecord",
    "ConditionRef",
    "ContextReference",
    "ProvenanceGraphRef",
    "SituatedAssertion",
    "assertion_source_record_from_payload",
    "claim_node_assertion_id",
    "claim_node_content",
    "claim_node_context_id",
    "content_digest",
    "derive_assertion_id",
    "semantic_content",
]
