# Propstore follow-up audit

## Scope

Read-only follow-up audit answering which Propstore surfaces remain unwired,
architecturally misplaced, or worth beautifying after the `cel_registry` work.
No production changes are authorized in this audit.

## Live findings so far

- Canonical scalar representation is still inconsistent: claim/source owners
  narrow values to `float | None`, while active/world paths accept or coerce
  broader scalar values. This is the foundational next convergence candidate.
- Grounding already reports `complete` versus `budget_exceeded`, but the
  production bundle-building owner does not expose or forward `max_arguments`.
  The low-level capability exists and is not fully wired through.
- Predicate and rule extraction have typed proposal/admission machinery, but
  their real LLM call boundaries still raise and their paper-note lookup is
  process-CWD-relative.
- Relation classification still crosses loose-dict boundaries, uses a protocol
  wrapper around world capabilities, does not preserve reverse-direction
  distance through classification, and does not yet complete the
  relation-to-proposal path.
- Context, micropublication, rule, and superiority list/show commands exist,
  but several CLI modules read families directly instead of calling typed app
  owners. This is an ownership cleanup, not missing user functionality.
- Claim neighborhoods are wired, while other focus kinds and some provenance,
  assumption, and policy-alternative projections remain explicit placeholders.
- ATMS and ASPIC basic wiring are already present; do not treat old missingness
  reports as authority for rebuilding them.
- The ASPIC projection kernel is implemented and tested, but production
  `WorldQuery` does not implement `grounding_bundle()`. The only production
  declaration found is the `GroundingBundleStore` protocol; runtime ASPIC
  resolution and worldline argumentation require that capability, while tests
  use explicit bundles or a store double. This is a concrete production wiring
  gap, not a request to rebuild ASPIC.
- No production consumer currently reads `GroundedRulesBundle.status` or
  `budget_reason`. The bundle-building owner also omits `max_arguments`, so both
  budget control and incomplete-result propagation stop below the owner layer.
- `_claim_to_payload` is not confined to serialization. Source claim identity
  normalization and authored-form restoration mutate a decoded semantic dict
  and convert it back to `SourceClaimDocument`. Under the repo's typed-domain
  rule, this is a real representation-cleanup candidate, best handled as part
  of canonical scalar/source-claim convergence rather than as an isolated
  helper rename.
- Claim and concept views explicitly know provenance lives in git notes but
  always report it missing. A typed provenance index/view owner is therefore a
  concrete missing connection, not merely optional richer presentation.
- Rule extraction has a CLI fixture path; predicate extraction has proposal
  lifecycle code and tests but no equivalent extraction command. Both real LLM
  owner boundaries remain unwired.

## Evidence still to inspect

- Classify `_claim_to_payload` in `propstore/source/claims.py` as a legitimate
  IO-boundary carrier or a loose semantic payload leaking into core code.
- Trace production grounding callers to identify exactly where completeness
  status and budget controls disappear.
- Verify the current predicate/rule CLI surfaces and the provenance/view
  placeholders before ranking the recommendations.

## Current ordering hypothesis

1. Execute canonical scalar convergence first.
2. Decide incomplete-reasoning policy, then give production `WorldQuery` its
   grounded-bundle owner path and propagate grounding completeness.
3. Decide durable LLM evidence, then wire predicate/rule extraction.
4. Converge relation classification onto typed owner/proposal surfaces.
5. Build provenance/view owners and replace known placeholders.
6. Treat CLI list/show owner separation as a bounded later beauty slice.

## Blockers

None for the read-only audit. Several implementation slices intentionally
depend on unresolved decisions already recorded in
`plans/unwired-and-missing-code-convergence.md`.

## Next action

Verify `WorldQuery` construction and runtime tests, confirm exact memory citation
lines, then give the user a live-verified ranked recommendation without changing
production state.
