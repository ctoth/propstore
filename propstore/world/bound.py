"""BoundWorld — condition-bound view over a WorldModel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ast_equiv import compare as ast_compare
from propstore.world.types import DerivedResult, Environment, RenderPolicy, ResolvedResult, ValueResult

if TYPE_CHECKING:
    from propstore.world.model import WorldModel


def _derived_value_impl(
    concept_id: str,
    world,
    is_param_compatible,
    value_of_fn,
    override_values: dict[str, float | str | None] | None = None,
) -> DerivedResult:
    """Shared implementation for derived_value() — used by BoundWorld and HypotheticalWorld."""
    from propstore.propagation import evaluate_parameterization

    params = world.parameterizations_for(concept_id)
    if not params:
        return DerivedResult(concept_id=concept_id, status="no_relationship")

    for param in params:
        if not is_param_compatible(param.get("conditions_cel")):
            continue

        sympy_expr = param.get("sympy")
        if not sympy_expr:
            continue

        input_ids = json.loads(param["concept_ids"])
        effective_inputs = [iid for iid in input_ids if iid != concept_id]

        input_values: dict[str, float] = {}
        all_determined = True
        any_conflicted = False

        for iid in effective_inputs:
            if override_values and iid in override_values:
                ov = override_values[iid]
                if ov is not None:
                    try:
                        input_values[iid] = float(ov)
                        continue
                    except (TypeError, ValueError):
                        pass

            vr = value_of_fn(iid)
            if vr.status == "determined":
                val = vr.claims[0].get("value") if vr.claims else None
                if val is not None:
                    input_values[iid] = float(val)
                else:
                    all_determined = False
            elif vr.status == "conflicted":
                any_conflicted = True
                all_determined = False
            else:
                all_determined = False

        if any_conflicted:
            return DerivedResult(concept_id=concept_id, status="conflicted")

        if not all_determined or len(input_values) != len(effective_inputs):
            continue

        result = evaluate_parameterization(sympy_expr, input_values, concept_id)
        if result is not None:
            return DerivedResult(
                concept_id=concept_id,
                status="derived",
                value=result,
                formula=param.get("formula"),
                input_values=input_values,
                exactness=param.get("exactness"),
            )

    # No parameterization succeeded
    if any(not is_param_compatible(p.get("conditions_cel")) for p in params):
        return DerivedResult(concept_id=concept_id, status="no_relationship")

    return DerivedResult(concept_id=concept_id, status="underspecified")


def _value_of_from_active(
    active: list[dict], concept_id: str, helpers: BoundWorld,
) -> ValueResult:
    """Shared implementation for value_of() — used by BoundWorld and HypotheticalWorld.

    ``helpers`` is always a BoundWorld instance (HypotheticalWorld passes self._base).
    It provides _extract_variable_concepts, _collect_known_values, _extract_bindings.
    """
    if not active:
        return ValueResult(concept_id=concept_id, status="no_claims")

    # Separate algorithm claims from value-bearing claims
    algo_claims = [c for c in active if c.get("type") == "algorithm"]
    value_claims = [c for c in active if c.get("type") != "algorithm"]

    # Mixed: algorithms are separate channel, resolve value claims only
    if value_claims and algo_claims:
        values = set()
        for c in value_claims:
            v = c.get("value")
            if v is not None:
                values.add(v)
        if not values:
            return ValueResult(concept_id=concept_id, status="no_claims", claims=active)
        if len(values) == 1:
            return ValueResult(concept_id=concept_id, status="determined", claims=active)
        return ValueResult(concept_id=concept_id, status="conflicted", claims=active)

    # Algorithm-only claims
    if algo_claims and not value_claims:
        if len(algo_claims) == 1:
            return ValueResult(concept_id=concept_id, status="determined", claims=algo_claims)

        # Multiple algorithms — compare pairwise using ast_compare
        all_var_concepts: set[str] = set()
        for ac in algo_claims:
            all_var_concepts.update(helpers._extract_variable_concepts(ac))
        all_var_concepts.discard(concept_id)

        known_values = helpers._collect_known_values(list(all_var_concepts))

        all_equivalent = True
        for i in range(len(algo_claims)):
            for j in range(i + 1, len(algo_claims)):
                body_a = algo_claims[i].get("body", "")
                body_b = algo_claims[j].get("body", "")
                if not body_a or not body_b:
                    all_equivalent = False
                    break
                bindings_a = helpers._extract_bindings(algo_claims[i])
                bindings_b = helpers._extract_bindings(algo_claims[j])
                try:
                    result = ast_compare(
                        body_a, bindings_a, body_b, bindings_b,
                        known_values=known_values if known_values else None,
                    )
                except Exception:
                    all_equivalent = False
                    break
                if not result.equivalent:
                    all_equivalent = False
                    break
            if not all_equivalent:
                break

        if all_equivalent:
            return ValueResult(concept_id=concept_id, status="determined", claims=algo_claims)
        return ValueResult(concept_id=concept_id, status="conflicted", claims=algo_claims)

    # Standard value-based resolution
    values = set()
    for c in active:
        v = c.get("value")
        if v is not None:
            values.add(v)

    if not values:
        return ValueResult(concept_id=concept_id, status="no_claims", claims=active)

    if len(values) == 1:
        return ValueResult(concept_id=concept_id, status="determined", claims=active)

    return ValueResult(concept_id=concept_id, status="conflicted", claims=active)


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
    records = detect_conflicts([synthetic], concept_registry)
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


class BoundWorld:
    """The world under specific condition bindings, optionally scoped to a context."""

    def __init__(
        self,
        world: WorldModel,
        bindings: dict[str, Any] | None = None,
        context_id: str | None = None,
        context_hierarchy: object | None = None,
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
        self._context_id = environment.context_id
        self._context_hierarchy = context_hierarchy
        # Pre-compute ancestor set for fast lookups
        if self._context_id and context_hierarchy is not None:
            self._context_visible: set[str] | None = {self._context_id}
            for ancestor in context_hierarchy.ancestors(self._context_id):  # type: ignore[union-attr]
                self._context_visible.add(ancestor)
        else:
            self._context_visible = None  # no context filtering

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

    def _is_active(self, claim: dict) -> bool:
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

    def _is_param_compatible(self, conditions_cel: str | None) -> bool:
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
        return [c for c in all_claims if self._is_active(c)]

    def inactive_claims(self, concept_id: str | None = None) -> list[dict]:
        all_claims = self._store.claims_for(concept_id)
        return [c for c in all_claims if not self._is_active(c)]

    def algorithm_for(self, concept_id: str) -> list[dict]:
        """Return all active algorithm claims relevant to the given concept."""
        active = self.active_claims(concept_id)
        return [c for c in active if c.get("type") == "algorithm"]

    def _collect_known_values(self, variable_concepts: list[str]) -> dict[str, Any]:
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

    def _extract_variable_concepts(self, claim: dict) -> list[str]:
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

    def _extract_bindings(self, claim: dict) -> dict[str, str]:
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
        return _value_of_from_active(active, concept_id, self)

    def derived_value(
        self,
        concept_id: str,
        *,
        override_values: dict[str, float | str | None] | None = None,
    ) -> DerivedResult:
        """Derive a value for concept_id via parameterization relationships."""
        return _derived_value_impl(
            concept_id,
            self._store,
            self._is_param_compatible,
            self.value_of,
            override_values=override_values,
        )

    def resolved_value(self, concept_id: str) -> ResolvedResult:
        from propstore.world.resolution import resolve

        return resolve(self, concept_id, policy=self._policy, world=self._store)

    def is_determined(self, concept_id: str) -> bool:
        return self.value_of(concept_id).status == "determined"

    def conflicts(self, concept_id: str | None = None) -> list[dict]:
        """Return active conflicts, revalidated against the current belief space."""
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
        return result

    def explain(self, claim_id: str) -> list[dict]:
        """Stance walk filtered to active claims."""
        claim = self._store.get_claim(claim_id)
        if claim is None or not self._is_active(claim):
            return []

        active_ids = {c["id"] for c in self.active_claims()}
        full_chain = self._store.explain(claim_id)
        return [s for s in full_chain if s["target_claim_id"] in active_ids]
