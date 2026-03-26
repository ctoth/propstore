# Sympy verification wiring

## GOAL
Wire bridgman's verify_expr into propstore's validate.py for dimensional checking via sympy expression trees.

## OBSERVATIONS
- validate.py lines 294-347: brute-force mul/div dimensional check
- sympy field exists directly on parameterization_relationships in concept YAML files
- Example: `sympy: Eq(concept7, 0.5 * concept1 * concept4**2)` on kinetic_energy
- Need to check bridgman for verify_expr/dims_of_expr/DimensionalError exports
- Ward blocks bare python — must use `uv run` or write .py files

## DONE
- Read validate.py structure
- Found sympy field locations in concept files
- Understood parameterization structure

## MORE OBSERVATIONS
- bridgman updated to c6401fa1 — verify_expr, dims_of_expr, DimensionalError all import fine
- FormDefinition.dimensions is `dict[str, int] | None` — same as bridgman's Dimensions type
- sympy field is directly on parameterization_relationships in concept YAML (e.g. `sympy: Eq(concept7, 0.5 * concept1 * concept4**2)`)
- The concept IDs (concept1, concept2, etc.) are the symbol names in the expression
- dim_map needs: for each concept ID in the expression, look up its form, get form.dimensions
- The brute-force check is at validate.py lines 309-329
- Need to insert sympy check BEFORE line 309 ("# Real dimensional verification: try all mul/div")
- The output concept's ID is `cid`, its dims are `output_dims`
- Input concepts are looked up via `id_to_concept` and their forms via `load_form`
- All the pieces are already available in scope at that point

## NEXT
1. Edit validate.py — add sympy check before brute-force
2. Delete _check_imports.py
3. Run tests
4. Commit and push
