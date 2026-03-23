"""BoundWorld — condition-bound view over a WorldModel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from propstore.world.value_resolver import ActiveClaimResolver
from propstore.world.types import (
    BeliefSpace,
    DerivedResult,
    Environment,
    RenderPolicy,
    ResolvedResult,
    ValueResult,
)

if TYPE_CHECKING:
    from propstore.validate_contexts import ContextHierarchy
    from propstore.world.model import WorldModel


def _concept_registry_for_store(world) -> dict[str, dict]:
    registry: dict[str, dict] = {}
    for concept in world.all_concepts():
        cdata = dict(concept)
        cid = cdata["id"]
        form_parameters = cdata.get("form_parameters")
        if isinstance(form_parameters, str):
            try:
                cdata["form_parameters"] = json.loads(form_parameters)
            except json.JSONDecodeError:
                cdata["form_parameters"] = {}
        params = world.parameterizations_for(cid)
        if params:
            cdata["parameterization_relationships"] = []
            for param in params:
                cdata["parameterization_relationships"].append({
                    "inputs": json.loads(param["concept_ids"]),
                    "sympy": param.get("sympy"),
                    "exactness": param.get("exactness"),
                    "conditions": json.loads(param["conditions_cel"]) if param.get("conditions_cel") else [],
                })
        registry[cid] = cdata
    return registry


def _claim_row_to_source_claim(claim: dict) -> dict:
    source = dict(claim)
    if claim.get("conditions_cel"):
        source["conditions"] = json.loads(claim["conditions_cel"])
    else:
        source["conditions"] = []

    claim_type = claim.get("type")
    if claim_type == "parameter" and claim.get("concept_id"):
        source["concept"] = claim["concept_id"]
    if claim_type == "measurement" and claim.get("concept_id") and not claim.get("target_concept"):
        source["target_concept"] = claim["concept_id"]
    if claim_type == "algorithm" and claim.get("concept_id"):
        source["concept"] = claim["concept_id"]
    if claim_type == "algorithm" and claim.get("variables_json"):
        source["variables"] = json.loads(claim["variables_json"])
    return source


def _recomputed_conflicts(world, claims: list[dict]) -> list[dict]:
    from propstore.conflict_detector import detect_conflicts
    from propstore.validate_claims import LoadedClaimFile

    if len(claims) < 2:
        return []

    synthetic = LoadedClaimFile(
        filename="<render>",
        filepath=Path("<render>"),
        data={"claims": [_claim_row_to_source_claim(claim) for claim in claims]},
    )
    concept_registry = _concept_registry_for_store(world)
    hierarchy_loader = getattr(world, "_load_context_hierarchy", None)
    context_hierarchy: ContextHierarchy | None = hierarchy_loader() if callable(hierarchy_loader) else None
    records = detect_conflicts(
        [synthetic],
        concept_registry,
        context_hierarchy=context_hierarchy,
    )
    return [
        {
            "concept_id": record.concept_id,
            "claim_a_id": record.claim_a_id,
            "claim_b_id": record.claim_b_id,
            "warning_class": record.warning_class.value,
            "conditions_a": record.conditions_a,
            "conditions_b": record.conditions_b,
            "value_a": record.value_a,
            "value_b": record.value_b,
            "derivation_chain": record.derivation_chain,
        }
        for record in records
    ]


class BoundWorld(BeliefSpace):
    """The world under specific condition bindings, optionally scoped to a context."""

    def __init__(
        self,
        world: WorldModel,
        bindings: dict[str, Any] | None = None,
        context_id: str | None = None,
        context_hierarchy: ContextHierarchy | None = None,
        *,
        environment: Environment | None = None,
        policy: RenderPolicy | None = None,
    ) -> None:
        self._store = world
        if environment is None:
            environment = Environment(bindings=bindings or {}, context_id=context_id)
        self._environment = environment
        self._policy = policy
        self._bindings = dict(environment.bindings)
        self._binding_conds = self._bindings_to_cel(self._bindings)
        for assumption in environment.effective_assumptions:
            if assumption not in self._binding_conds:
                self._binding_conds.append(assumption)
        self._context_id = environment.context_id
        self._context_hierarchy = context_hierarchy
        # Pre-compute ancestor set for fast lookups
        if self._context_id and context_hierarchy is not None:
            self._context_visible: set[str] | None = {self._context_id}
            for ancestor in context_hierarchy.ancestors(self._context_id):
                self._context_visible.add(ancestor)
        else:
            self._context_visible = None  # no context filtering
        self._conflicts_cache: dict[str | None, list[dict]] = {}
        self._resolver = ActiveClaimResolver(
            parameterizations_for=getattr(self._store, "parameterizations_for", lambda _cid: []),
            is_param_compatible=self.is_param_compatible,
            value_of=self.value_of,
            extract_variable_concepts=self.extract_variable_concepts,
            collect_known_values=self.collect_known_values,
            extract_bindings=self.extract_bindings,
        )

    @staticmethod
    def _bindings_to_cel(bindings: dict[str, Any]) -> list[str]:
        """Convert keyword bindings to CEL condition strings."""
        conds: list[str] = []
        for key, value in bindings.items():
            if isinstance(value, str):
                conds.append(f"{key} == '{value}'")
            elif isinstance(value, bool):
                conds.append(f"{key} == {'true' if value else 'false'}")
            else:
                conds.append(f"{key} == {value}")
        return conds

    def is_active(self, claim: dict) -> bool:
        """Check if a claim is active under the current bindings and context."""
        # Step 1: Context membership check
        if self._context_visible is not None:
            claim_ctx = claim.get("context_id")
            if claim_ctx is not None:
                if claim_ctx not in self._context_visible:
                    return False
            # Claims with no context (NULL) are always visible

        # Step 2: Existing CEL condition check
        conds_json = claim.get("conditions_cel")
        if not conds_json:
            return True  # unconditional → always active
        claim_conds = json.loads(conds_json)
        if not claim_conds:
            return True  # empty conditions → always active
        if not self._binding_conds:
            return True  # no bindings → everything active

        solver = self._store.condition_solver()
        return not solver.are_disjoint(self._binding_conds, claim_conds)

    def is_param_compatible(self, conditions_cel: str | None) -> bool:
        """Check if parameterization conditions are compatible with bindings."""
        if not conditions_cel:
            return True
        conds = json.loads(conditions_cel)
        if not conds:
            return True
        if not self._binding_conds:
            return True
        solver = self._store.condition_solver()
        return not solver.are_disjoint(self._binding_conds, conds)

    def active_claims(self, concept_id: str | None = None) -> list[dict]:
        all_claims = self._store.claims_for(concept_id)
        return [c for c in all_claims if self.is_active(c)]

    def inactive_claims(self, concept_id: str | None = None) -> list[dict]:
        all_claims = self._store.claims_for(concept_id)
        return [c for c in all_claims if not self.is_active(c)]

    def algorithm_for(self, concept_id: str) -> list[dict]:
        """Return all active algorithm claims relevant to the given concept."""
        active = self.active_claims(concept_id)
        return [c for c in active if c.get("type") == "algorithm"]

    def collect_known_values(self, variable_concepts: list[str]) -> dict[str, Any]:
        """Resolve numeric values for a list of concept IDs."""
        known: dict[str, Any] = {}
        for cid in variable_concepts:
            vr = self.value_of(cid)
            if vr.status == "determined" and vr.claims:
                val = vr.claims[0].get("value")
                if val is not None:
                    try:
                        known[cid] = float(val)
                    except (TypeError, ValueError):
                        pass
        return known

    def extract_variable_concepts(self, claim: dict) -> list[str]:
        """Extract concept IDs referenced by an algorithm claim's variables."""
        variables_json = claim.get("variables_json")
        if not variables_json:
            return []
        variables = json.loads(variables_json)
        concepts: list[str] = []
        if isinstance(variables, list):
            for var in variables:
                if isinstance(var, dict):
                    concept = var.get("concept")
                    if concept:
                        concepts.append(concept)
        elif isinstance(variables, dict):
            concepts.extend(variables.values())
        return concepts

    def extract_bindings(self, claim: dict) -> dict[str, str]:
        """Extract variable name -> concept mapping from an algorithm claim."""
        variables_json = claim.get("variables_json")
        if not variables_json:
            return {}
        variables = json.loads(variables_json)
        bindings: dict[str, str] = {}
        if isinstance(variables, list):
            for var in variables:
                if isinstance(var, dict):
                    name = var.get("name") or var.get("symbol")
                    concept = var.get("concept")
                    if name and concept:
                        bindings[name] = concept
        elif isinstance(variables, dict):
            bindings = dict(variables)
        return bindings

    def value_of(self, concept_id: str) -> ValueResult:
        active = self.active_claims(concept_id)
        return self._resolver.value_of_from_active(active, concept_id)

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: dict[str, float | str | None] | None = None,
    ) -> DerivedResult:
        """Derive a value for concept_id via parameterization relationships."""
        return self._resolver.derived_value(
            concept_id,
            override_values=override_values,
        )

    def resolved_value(self, concept_id: str) -> ResolvedResult:
        from propstore.world.resolution import resolve

        return resolve(self, concept_id, policy=self._policy, world=self._store)

    def is_determined(self, concept_id: str) -> bool:
        return self.value_of(concept_id).status == "determined"

    def conflicts(self, concept_id: str | None = None) -> list[dict]:
        """Return active conflicts, revalidated against the current belief space."""
        if concept_id in self._conflicts_cache:
            return self._conflicts_cache[concept_id]
        active_claims = self.active_claims(concept_id)
        active_ids = {c["id"] for c in active_claims}

        result = []
        all_conflicts = self._store.conflicts()
        for conflict in all_conflicts:
            if conflict["claim_a_id"] in active_ids and conflict["claim_b_id"] in active_ids:
                if concept_id is None or conflict.get("concept_id") == concept_id:
                    result.append(conflict)
        seen = {(c["claim_a_id"], c["claim_b_id"], c.get("concept_id")) for c in result}
        for conflict in _recomputed_conflicts(self._store, active_claims):
            key = (conflict["claim_a_id"], conflict["claim_b_id"], conflict.get("concept_id"))
            reverse_key = (conflict["claim_b_id"], conflict["claim_a_id"], conflict.get("concept_id"))
            if key not in seen and reverse_key not in seen:
                result.append(conflict)
                seen.add(key)
        self._conflicts_cache[concept_id] = result
        return result

    def explain(self, claim_id: str) -> list[dict]:
        """Stance walk filtered to active claims."""
        claim = self._store.get_claim(claim_id)
        if claim is None or not self.is_active(claim):
            return []

        active_ids = {c["id"] for c in self.active_claims()}
        full_chain = self._store.explain(claim_id)
        return [s for s in full_chain if s["target_claim_id"] in active_ids]
