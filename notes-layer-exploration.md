# Layer Exploration: Theory/Typing + Heuristic Analysis

## GOAL
Map all files in theory/typing layer and heuristic analysis layer, identify maturity level (mature/WIP/stub) for each category.

## PROJECT STRUCTURE
- `/propstore/propstore/` — main source
- Tests in `/propstore/tests/`
- Forms in `/propstore/forms/`
- Knowledge in `/propstore/knowledge/`

## FILES FOUND (RAW LIST)
Core Python modules in propstore/:
- __init__.py
- argumentation.py (9.9K)
- build_sidecar.py (30.4K)
- cel_checker.py (21.8K)
- condition_classifier.py (11.1K)
- conflict_detector.py (18.2K)
- description_generator.py (5.5K)
- dung.py (6.3K)
- dung_z3.py (8.0K)
- embed.py (22.4K)
- equation_comparison.py (3.3K)
- form_utils.py (8.5K)
- graph_export.py (7.7K)
- maxsat_resolver.py (1.4K)
- param_conflicts.py (14.5K)
- parameterization_groups.py (2.3K)
- preference.py (2.6K)
- propagation.py (2.3K)
- relate.py (16.5K)
- resources.py (1.8K)
- sensitivity.py (4.9K)
- sympy_generator.py (3.0K)
- unit_dimensions.py (3.5K)
- validate.py (16.1K)
- validate_claims.py (21.6K)
- validate_contexts.py (5.1K)
- value_comparison.py (5.1K)
- world_model.py (134B)
- z3_conditions.py (12.2K)

Subdirectories:
- cli/
- world/ (bound.py, hypothetical.py, model.py, resolution.py, types.py)

## LAYER MAPPING (IN PROGRESS)
- [ ] CEL type-checking — cel_checker.py
- [ ] Z3 condition reasoning — z3_conditions.py, dung_z3.py
- [ ] Forms/dimensions/parameterization — form_utils.py, param_conflicts.py, parameterization_groups.py, unit_dimensions.py
- [ ] Embedding similarity, LLM classification — embed.py, condition_classifier.py
- [ ] Argumentation (Dung, ASPIC+, extensions, attacks, defeats) — argumentation.py, dung.py, dung_z3.py
- [ ] Derivation chains — validate_claims.py, relate.py, propagation.py
- [ ] Sensitivity analysis — sensitivity.py
- [ ] Graph export — graph_export.py

## DONE
1. Located all Python files
2. Identified major modules

## STUCK
None yet — proceeding to read each file for maturity assessment.

## NEXT
1. Read each identified file to assess maturity and implementation status
2. Organize by layer and category
3. Identify stubs, WIP, and mature implementations
4. Note interdependencies
