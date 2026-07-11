"""Core situated assertion reference types.

This package carries two cooperating surfaces:

* the situated-assertion subsystem proper — :class:`SituatedAssertion` and its
  reference types (:class:`ContextReference`, :class:`ConditionRef`,
  :class:`ProvenanceGraphRef`);
* claim-charter assertion identity used by the ATMS engine to collapse
  identical claim content to one node.
"""

from __future__ import annotations

from propstore.core.assertions.claim_identity import (
    claim_assertion_id,
    content_digest,
    semantic_content,
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
    "ConditionRef",
    "ContextReference",
    "ProvenanceGraphRef",
    "SituatedAssertion",
    "claim_assertion_id",
    "content_digest",
    "derive_assertion_id",
    "semantic_content",
]
