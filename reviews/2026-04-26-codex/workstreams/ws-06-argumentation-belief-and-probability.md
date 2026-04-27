# WS-06: Argumentation, belief revision, and probabilistic semantics

## Review findings covered

- ASPIC grounded can accept attack-conflicting arguments.
- ASPIC incomplete/direct semantics are advertised but not routed.
- `praf-paper-td-complete` is advertised but wired as a normal acceptance query.
- Missing PrAF calibration deletes arguments/relations rather than representing ignorance or failing.
- Raw confidence becomes dogmatic/fabricated evidence.
- DF-QuAD probabilistic support/attack treatment is asymmetric.
- Cyclic DF-QuAD returns last-iteration values without convergence semantics.
- `dfquad_quad` is exposed without required base scores.
- IC merge drops infinite distances.
- Complete semantics is missing from propstore surfaces even though the dependency supports it.
- Asymmetric stance intent is encoded through symmetric contradiction.
- Live worldline revision does not populate merge-parent evidence.
- AF revision conflates no stable extension with empty extension.
- AGM contraction collapses Spohn epistemic state.
- Formal IC merge tests omit IC4 fairness.
- Sensitivity is local derivative/OAT-only despite cited interaction-sensitive literature.

## Dependencies

- Depends on `ws-02-schema-and-test-infrastructure.md`.
- Depends on `ws-04-formal-expressions-units-equations.md` for correct condition/equation behavior.
- Depends on `ws-05-contexts-publications-and-atms.md` where context-aware support affects reasoning.

## First failing tests

1. ASPIC grounded conflict-free:
   - Build two arguments that mutually attack but do not defeat under current preference handling.
   - Expected: grounded ASPIC result must not justify both if ASPIC+/selected semantics require conflict-free extensions.
   - The existing test that expects both justified should be replaced by the paper-correct assertion.

2. Advertised ASPIC semantics:
   - For each advertised ASPIC semantics in `WorldSemantics`, assert either:
     - policy validation rejects it as unsupported, or
     - structured/backend resolution executes it and returns typed results.
   - Add cases for `aspic-direct-grounded`, `aspic-incomplete-grounded`, `complete`.

3. ASPIC contrariness modeling:
   - Author directional stance such as `supersedes`/`undermines`.
   - Expected: represented through asymmetric contraries or a typed directional attack relation, not symmetric contradictory pairs patched later.
   - Verify claim-graph and ASPIC semantics agree on unconditional vs preference-sensitive relations.

4. PrAF calibration boundary:
   - Graph with uncalibrated attacker/relation.
   - Expected: hard boundary error or explicit vacuous/ignorance opinion, not deletion from graph.
   - Public metadata must report any omission if omission remains deliberately supported.

5. Raw confidence to evidence:
   - `confidence=1.0` from raw input must not become dogmatic evidence.
   - Add tests for calibrated finite evidence counts versus uncalibrated score fields.

6. `praf-paper-td-complete` routing:
   - Select the advertised policy.
   - Expected: call dependency with `strategy="paper_td"`, `semantics="complete"`, and extension-probability query shape, or reject at validation.

7. DF-QuAD probability semantics:
   - Defeat edge with probability 0 should not attack at full strength if probability means existence.
   - Support and attack probabilities should be treated symmetrically under the selected semantics, or the policy should state structural-weight semantics explicitly.
   - Cyclic graph should fail or report non-convergence, not return arbitrary last iteration as final semantics.

8. `dfquad_quad` base scores:
   - Select `dfquad_quad` through propstore resolution.
   - Expected: requires/provides `tau` base scores or rejects policy before analysis.

9. IC infinite distances and IC4:
   - Profile formula with no model in candidate space should not be silently ignored.
   - Add IC4 fairness test against `merge_belief_profile`, not scalar assignment merge.

10. Worldline merge-parent detection:
    - Create a real merged worldline/branch history.
    - Project belief base through normal `BoundWorld` path.
    - Expected: merge-parent evidence reaches `RevisionScope` and Bonanno guard fires.

11. AF no-stable-extension:
    - Dependency AF with no stable extensions.
    - Expected: no successful empty-extension substitute.

12. AGM/DP epistemic state preservation:
    - Construct a ranked Spohn state with nontrivial conditional ranking.
    - Contract/revise and then revise again.
    - Expected: ranking-sensitive behavior is preserved where the operator claims epistemic-state semantics.

13. Sensitivity interactions:
    - Function with interaction term where local derivative/OAT ranks low but total Sobol effect ranks high.
    - Expected: either expose local-only method name honestly or add global/Sobol option and tests.

## Production change sequence

1. Semantics validation inventory:
   - Enumerate every advertised world/argumentation/probabilistic semantic.
   - For each, choose exactly one target:
     - implemented and routed
     - rejected during policy validation
     - deleted from public enum
   - Do not leave accepted-but-runtime-raises semantics.

2. ASPIC correctness:
   - Fix attack/defeat construction so grounded/complete/preferred/stable semantics satisfy paper-required conflict-free/admissibility properties.
   - Model directional conflicts as asymmetric contraries or typed attacks, not contradictory-pair hacks.
   - Route direct and incomplete ASPIC through dependency support or delete advertised support.

3. PrAF/probability boundary:
   - Separate raw confidence, calibrated probability, and evidence/opinion.
   - Unknown calibration should be vacuous/ignorance or hard failure.
   - Do not delete graph elements silently.
   - Route paper TD complete to the dependency's paper strategy or remove it.

4. DF-QuAD/QBAF:
   - Decide whether probabilities mean edge existence, structural weight, or opinion expectation.
   - Apply that interpretation symmetrically to attack/support or split policies.
   - Reject cyclic graphs for DAG-only semantics unless a convergent cyclic semantics is implemented and tested.
   - Require `tau` for QuAD mode.

5. IC/AGM/AF revision:
   - Preserve infinite distances or reject inconsistent profile formulas at the boundary.
   - Add Max if the paper taxonomy is claimed, or document supported operators precisely.
   - Stop substituting empty extension for no stable extension.
   - Preserve epistemic-state rankings where DP/Spohn semantics are claimed.

6. Worldline revision:
   - Thread merge-parent commits from repository/worldline history into `RevisionScope`.
   - Guard live revision on real DAG merge evidence, not only manually injected test data.

7. Sensitivity:
   - Rename local derivative/OAT surfaces clearly, or add global interaction-aware sensitivity.
   - Do not cite interaction-aware literature for a purely local metric without exposing the limitation.

## Acceptance gates

- Targeted logged pytest:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label reasoning-semantics tests/test_aspic_bridge.py tests/test_structured_projection.py tests/test_praf*.py tests/test_belief_set*.py tests/test_af_revision_postulates.py tests/test_worldline_revision.py tests/test_sensitivity.py`
  - Add dependency tests in sibling repos where the bug lives, then update propstore integration tests.
- `uv run pyright propstore`
- `uv run lint-imports`

## Done means

- Every advertised semantic either runs correctly or is rejected before execution.
- Paper-backed operators have tests for the postulates/properties that distinguish them from weaker approximations.
- Unknown probability/calibration is not silently deleted or converted to certainty.
- Revision and merge semantics preserve the structures their papers require.
