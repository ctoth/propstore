"""HypotheticalWorld — in-memory overlay on a BoundWorld."""

from __future__ import annotations

import json

from propstore.world.bound import (
    BoundWorld,
    _recomputed_conflicts,
)
from propstore.world.value_resolver import ActiveClaimResolver, collect_known_values
from propstore.world.types import BeliefSpace, DerivedResult, ResolvedResult, SyntheticClaim, ValueResult


class HypotheticalWorld(BeliefSpace):
    """In-memory overlay on a BoundWorld — removes/adds claims without mutation."""

    def __init__(
        self,
        base: BoundWorld,
        remove: list[str] | None = None,
        add: list[SyntheticClaim] | None = None,
    ) -> None:
        self._base = base
        self._removed_ids = set(remove or [])
        self._synthetics = list(add or [])
        self._resolver = ActiveClaimResolver(
            parameterizations_for=getattr(self._base._store, "parameterizations_for", lambda _cid: []),
            is_param_compatible=self._base.is_param_compatible,
            value_of=self.value_of,
            extract_variable_concepts=self._base.extract_variable_concepts,
            collect_known_values=self.collect_known_values,
            extract_bindings=self._base.extract_bindings,
        )

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
            if self._base.is_active(sc_dict):
                filtered.append(sc_dict)
        return filtered

    def inactive_claims(self, concept_id: str | None = None) -> list[dict]:
        base_inactive = self._base.inactive_claims(concept_id)
        filtered = [c for c in base_inactive if c["id"] not in self._removed_ids]
        for sc in self._synthetics:
            if concept_id is not None and sc.concept_id != concept_id:
                continue
            sc_dict = self._synthetic_to_dict(sc)
            if not self._base.is_active(sc_dict):
                filtered.append(sc_dict)
        return filtered

    def collect_known_values(self, variable_concepts: list[str]) -> dict:
        """Resolve numeric values for a list of concept IDs via hypothetical claims."""
        return collect_known_values(variable_concepts, self.value_of)

    def value_of(self, concept_id: str) -> ValueResult:
        active = self.active_claims(concept_id)
        return self._resolver.value_of_from_active(active, concept_id)

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: dict[str, float | str | None] | None = None,
    ) -> DerivedResult:
        """Derive using this hypothetical world's active claims."""
        return self._resolver.derived_value(
            concept_id,
            override_values=override_values,
        )

    def resolved_value(self, concept_id: str) -> ResolvedResult:
        from propstore.world.resolution import resolve

        return resolve(self, concept_id, policy=self._base._policy, world=self._base._store)

    def is_determined(self, concept_id: str) -> bool:
        return self.value_of(concept_id).status == "determined"

    def conflicts(self, concept_id: str | None = None) -> list[dict]:
        filtered = [
            c for c in self._base.conflicts(concept_id)
            if c.get("claim_a_id") not in self._removed_ids
            and c.get("claim_b_id") not in self._removed_ids
        ]
        recomputed = _recomputed_conflicts(self._base._store, self.active_claims(concept_id))
        seen = {(c["claim_a_id"], c["claim_b_id"], c.get("concept_id")) for c in filtered}
        for conflict in recomputed:
            key = (conflict["claim_a_id"], conflict["claim_b_id"], conflict.get("concept_id"))
            reverse_key = (conflict["claim_b_id"], conflict["claim_a_id"], conflict.get("concept_id"))
            if key not in seen and reverse_key not in seen:
                filtered.append(conflict)
                seen.add(key)
        return filtered

    def explain(self, claim_id: str) -> list[dict]:
        claim = next((c for c in self.active_claims() if c["id"] == claim_id), None)
        if claim is None:
            return []
        active_ids = {c["id"] for c in self.active_claims()}
        return [s for s in self._base.explain(claim_id) if s["target_claim_id"] in active_ids]

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
            claim = self._base._store.get_claim(cid)
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
