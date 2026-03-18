"""HypotheticalWorld — in-memory overlay on a BoundWorld."""

from __future__ import annotations

import json

from propstore.world.bound import (
    BoundWorld,
    _derived_value_impl,
    _value_of_from_active,
)
from propstore.world.types import DerivedResult, SyntheticClaim, ValueResult


class HypotheticalWorld:
    """In-memory overlay on a BoundWorld — removes/adds claims without mutation.

    Known limitation: conflicts() returns base conflicts filtered by active IDs.
    It does NOT detect new conflicts from synthetic claims. Full conflict
    recomputation is deferred to Feature 7.
    """

    def __init__(
        self,
        base: BoundWorld,
        remove: list[str] | None = None,
        add: list[SyntheticClaim] | None = None,
    ) -> None:
        self._base = base
        self._removed_ids = set(remove or [])
        self._synthetics = list(add or [])

    def _synthetic_to_dict(self, sc: SyntheticClaim) -> dict:
        """Convert a SyntheticClaim to the dict format used by claims."""
        return {
            "id": sc.id,
            "concept_id": sc.concept_id,
            "type": sc.type,
            "value": sc.value,
            "conditions_cel": json.dumps(sc.conditions) if sc.conditions else None,
        }

    def active_claims(self, concept_id: str | None = None) -> list[dict]:
        base_active = self._base.active_claims(concept_id)
        filtered = [c for c in base_active if c["id"] not in self._removed_ids]
        for sc in self._synthetics:
            if concept_id is not None and sc.concept_id != concept_id:
                continue
            sc_dict = self._synthetic_to_dict(sc)
            if self._base._is_active(sc_dict):
                filtered.append(sc_dict)
        return filtered

    def inactive_claims(self, concept_id: str | None = None) -> list[dict]:
        base_inactive = self._base.inactive_claims(concept_id)
        filtered = [c for c in base_inactive if c["id"] not in self._removed_ids]
        for sc in self._synthetics:
            if concept_id is not None and sc.concept_id != concept_id:
                continue
            sc_dict = self._synthetic_to_dict(sc)
            if not self._base._is_active(sc_dict):
                filtered.append(sc_dict)
        return filtered

    def value_of(self, concept_id: str) -> ValueResult:
        active = self.active_claims(concept_id)
        return _value_of_from_active(active, concept_id, self._base)

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: dict[str, float | str | None] | None = None,
    ) -> DerivedResult:
        """Derive using this hypothetical world's active claims."""
        return _derived_value_impl(
            concept_id,
            self._base._world,
            self._base._is_param_compatible,
            self.value_of,
            override_values=override_values,
        )

    def is_determined(self, concept_id: str) -> bool:
        return self.value_of(concept_id).status == "determined"

    def recompute_conflicts(self) -> list[dict]:
        """Check for direct value disagreements among active claims."""
        conflicts: list[dict] = []
        all_active = self.active_claims()

        by_concept: dict[str, list[dict]] = {}
        for claim in all_active:
            cid = claim.get("concept_id")
            if cid is None:
                continue
            if cid not in by_concept:
                by_concept[cid] = []
            by_concept[cid].append(claim)

        for cid, claims in by_concept.items():
            if len(claims) < 2:
                continue
            for i in range(len(claims)):
                for j in range(i + 1, len(claims)):
                    val_a = claims[i].get("value")
                    val_b = claims[j].get("value")
                    if val_a is None or val_b is None:
                        continue
                    if val_a != val_b:
                        conflicts.append({
                            "concept_id": cid,
                            "claim_a_id": claims[i]["id"],
                            "claim_b_id": claims[j]["id"],
                            "warning_class": "CONFLICT",
                            "value_a": val_a,
                            "value_b": val_b,
                        })
        return conflicts

    def diff(self) -> dict[str, tuple[ValueResult, ValueResult]]:
        """Compare base and hypothetical value_of for all affected concepts."""
        affected: set[str] = set()
        for sc in self._synthetics:
            affected.add(sc.concept_id)
        for cid in self._removed_ids:
            claim = self._base._world.get_claim(cid)
            if claim and claim.get("concept_id"):
                affected.add(claim["concept_id"])

        result: dict[str, tuple[ValueResult, ValueResult]] = {}
        for cid in affected:
            base_vr = self._base.value_of(cid)
            hypo_vr = self.value_of(cid)
            if base_vr.status != hypo_vr.status or _value_set(base_vr) != _value_set(hypo_vr):
                result[cid] = (base_vr, hypo_vr)
        return result


def _value_set(vr: ValueResult) -> set:
    """Extract the set of values from a ValueResult for comparison."""
    return {c.get("value") for c in vr.claims if c.get("value") is not None}
