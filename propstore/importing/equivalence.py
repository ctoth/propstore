"""Explicit equivalence witnesses with no sameAs-style identity closure.

When an import finds two candidates that *might* be the same thing, the system
records an explicit witness for that belief and stops. It never merges the
candidates, never rewrites one id to the other, and never computes a transitive
closure that would make the merge irreversible (CLAUDE.md non-commitment;
[[feedback_imports_are_opinions]]). :meth:`EquivalenceWitnessStore.compose` will
derive a witness across a shared candidate, but marks it ``derived_unresolved``
so a render policy can tell a derived guess from an asserted one, and
:meth:`identity_for` deliberately returns the candidate unchanged: there is no
canonical representative to collapse onto.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

EquivalenceWitnessStatus = Literal["asserted", "derived_unresolved"]

_URI_PREFIXES = ("urn:", "ni://", "http://", "https://")


@dataclass(frozen=True, order=True)
class EquivalenceWitness:
    witness_id: str
    candidate_ids: tuple[str, str]
    mapping_policy_id: str
    evidence_statement_ids: tuple[str, ...]
    status: EquivalenceWitnessStatus
    source_witness_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "witness_id", _require_uri(self.witness_id, "witness_id")
        )
        candidates = _canonical_candidate_pair(
            self.candidate_ids[0], self.candidate_ids[1]
        )
        object.__setattr__(self, "candidate_ids", candidates)
        object.__setattr__(
            self,
            "mapping_policy_id",
            _require_uri(self.mapping_policy_id, "mapping_policy_id"),
        )
        object.__setattr__(
            self,
            "evidence_statement_ids",
            _canonical_uri_tuple(self.evidence_statement_ids, "evidence statement"),
        )
        object.__setattr__(
            self,
            "source_witness_ids",
            _canonical_uri_tuple(self.source_witness_ids, "source witness")
            if self.source_witness_ids
            else (),
        )
        if self.status not in ("asserted", "derived_unresolved"):
            raise ValueError("unsupported equivalence witness status")


class EquivalenceWitnessStore:
    """Explicit witness index with no sameAs-style identity closure."""

    def __init__(self) -> None:
        self._witnesses: dict[str, EquivalenceWitness] = {}

    def record_witness(
        self,
        first_candidate_id: str,
        second_candidate_id: str,
        *,
        mapping_policy_id: str,
        evidence_statement_ids: tuple[str, ...],
    ) -> EquivalenceWitness:
        return self._record(
            first_candidate_id,
            second_candidate_id,
            mapping_policy_id=mapping_policy_id,
            evidence_statement_ids=evidence_statement_ids,
            status="asserted",
            source_witness_ids=(),
        )

    def compose(
        self,
        first_witness_id: str,
        second_witness_id: str,
    ) -> EquivalenceWitness | None:
        first = self._witnesses[first_witness_id]
        second = self._witnesses[second_witness_id]
        if first.mapping_policy_id != second.mapping_policy_id:
            return None
        shared = set(first.candidate_ids).intersection(second.candidate_ids)
        if len(shared) != 1:
            return None
        endpoints = (
            set(first.candidate_ids).union(second.candidate_ids).difference(shared)
        )
        if len(endpoints) != 2:
            return None
        left, right = tuple(sorted(endpoints))
        return self._record(
            left,
            right,
            mapping_policy_id=first.mapping_policy_id,
            evidence_statement_ids=first.evidence_statement_ids
            + second.evidence_statement_ids,
            status="derived_unresolved",
            source_witness_ids=(first.witness_id, second.witness_id),
        )

    def witnesses_for(self, candidate_id: str) -> tuple[EquivalenceWitness, ...]:
        candidate = _require_uri(candidate_id, "candidate_id")
        return tuple(
            witness
            for witness in self._witnesses.values()
            if candidate in witness.candidate_ids
        )

    def identity_for(self, candidate_id: str) -> str:
        return _require_uri(candidate_id, "candidate_id")

    def _record(
        self,
        first_candidate_id: str,
        second_candidate_id: str,
        *,
        mapping_policy_id: str,
        evidence_statement_ids: tuple[str, ...],
        status: EquivalenceWitnessStatus,
        source_witness_ids: tuple[str, ...],
    ) -> EquivalenceWitness:
        candidate_ids = _canonical_candidate_pair(
            first_candidate_id, second_candidate_id
        )
        payload = (
            candidate_ids,
            mapping_policy_id,
            tuple(sorted(evidence_statement_ids)),
            status,
            tuple(sorted(source_witness_ids)),
        )
        witness = EquivalenceWitness(
            witness_id=f"urn:propstore:equivalence-witness:{_digest(payload)}",
            candidate_ids=candidate_ids,
            mapping_policy_id=mapping_policy_id,
            evidence_statement_ids=evidence_statement_ids,
            status=status,
            source_witness_ids=source_witness_ids,
        )
        self._witnesses[witness.witness_id] = witness
        return witness


def _canonical_candidate_pair(left: str, right: str) -> tuple[str, str]:
    left_id = _require_uri(left, "candidate_id")
    right_id = _require_uri(right, "candidate_id")
    if left_id == right_id:
        raise ValueError("equivalence witness requires distinct candidates")
    first, second = sorted((left_id, right_id))
    return (first, second)


def _canonical_uri_tuple(values: tuple[str, ...], label: str) -> tuple[str, ...]:
    result = tuple(sorted({_require_uri(value, label) for value in values}))
    if not result:
        raise ValueError(f"{label} set must be non-empty")
    return result


def _require_non_empty(value: str, label: str) -> str:
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{label} must be non-empty")
    return text


def _require_uri(value: str, label: str) -> str:
    text = _require_non_empty(value, label)
    if not text.startswith(_URI_PREFIXES):
        raise ValueError(f"{label} must be a URI")
    return text


def _digest(value: object) -> str:
    rendered = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()
