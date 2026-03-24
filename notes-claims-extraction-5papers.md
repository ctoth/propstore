# Claims Extraction Session - 5 TMS Papers
Date: 2026-03-22

## Goal
Extract claims from 5 papers with full concept registration and validation:
1. Doyle_1979_TruthMaintenanceSystem
2. McAllester_1978_ThreeValuedTMS
3. deKleer_1984_QualitativePhysicsConfluences
4. deKleer_1986_AssumptionBasedTMS
5. deKleer_1986_ProblemSolvingATMS

## Observations
- No existing concept files were present in knowledge/concepts/
- No existing claims.yaml files on disk (git has some in working tree changes)
- Claim IDs must match regex: `^([A-Za-z0-9][A-Za-z0-9_'\-]*:)?[A-Za-z][A-Za-z0-9_]*$` - so claim1, claim2 etc work
- Validator checks concepts exist in registry by ID or canonical_name or alias
- Form "structural" is correct for argumentation concepts (dimensionless, structural kind)
- `pks concept add` auto-assigns IDs starting from concept163

## Concepts Registered (Paper 1 - Doyle 1979)
- truth_maintenance_system (concept163)
- support_list_justification (concept164)
- conditional_proof_justification (concept165)
- support_status (concept166)
- well_founded_justification (concept167)
- dependency_directed_backtracking (concept168)
- nogood (concept169)
- non_monotonic_reasoning (concept170)
- default_assumption (concept171)
- belief_revision (concept172)

## Still needed for Paper 1
- More concepts: dialectical_argumentation, summarizing_argument, belief_model, contradiction_node
- Write claims.yaml
- Validate

## Paper 1 - Doyle 1979: DONE
- 18 claims written, all observation type
- Validated clean (0 warnings)

## Paper 2 - McAllester 1978: DONE
- 14 claims written, all observation type
- Validated clean (0 warnings)
- Additional concepts: three_valued_logic (concept238), disjunctive_clause (concept242), clause_validity (concept246), contradiction_resolution (concept249), unit_propagation (concept250)

## Paper 3 - deKleer 1984 Confluences: IN PROGRESS
- Notes read, concepts registered:
  - confluence (concept290), qualitative_state (concept291), qualitative_value (concept292)
  - no_function_in_structure (concept293), mythical_causality (concept294), device_topology (concept296)
  - qualitative_ambiguity (concept300), constraint_propagation (concept302)
- Next: write claims.yaml and validate

## Paper 3 - deKleer 1984 Confluences: DONE
- 14 claims written, all observation type
- Validated clean (0 warnings)
- Concepts: confluence, qualitative_state, qualitative_value, no_function_in_structure, mythical_causality, device_topology, qualitative_ambiguity, constraint_propagation

## Paper 4 - deKleer 1986 ATMS: DONE
- 15 claims written, all observation type
- Validated clean (0 warnings)
- New concepts: label_soundness (333), label_completeness (334), label_minimality (335), label_consistency (336), context_switching (337)

## Paper 5 - deKleer 1986 Problem Solving ATMS: DONE
- 15 claims written, all observation type
- Validated clean (0 warnings)
- New concepts: consumer_architecture (349), control_disjunction (350), constraint_language (351), kernel_environment (352)

## Summary
All 5 papers complete. Total: 76 claims across 5 files, all validated clean (0 errors, 0 warnings).
- Paper 1 (Doyle 1979): 18 claims
- Paper 2 (McAllester 1978): 14 claims
- Paper 3 (deKleer 1984): 14 claims
- Paper 4 (deKleer 1986 ATMS): 15 claims
- Paper 5 (deKleer 1986 PS-ATMS): 15 claims
