# Bridgman Integration Notes — 2026-03-23

## GOAL
Wire bridgman into propstore: replace form-name heuristic with real dimensional arithmetic, delegate dims_equal.

## OBSERVATIONS
- pyproject.toml: dependencies on line 6-15, uv.sources on line 37-38 (has ast-equiv)
- validate.py: Form compatibility heuristics at lines 292-319, does name-matching
- unit_dimensions.py: dimensions_compatible() at lines 92-102, manual key comparison
- bridgman exports: mul_dims, div_dims, dims_equal, pow_dims, verify_equation, format_dims, Dimensions
- FormDefinition has `dimensions: dict[str, int] | None` field (form_utils.py line 26)
- bridgman exists locally at C:/Users/Q/code/bridgman/

## DONE
1. Added bridgman to pyproject.toml dependencies + uv.sources — DONE
2. uv sync — DONE, bridgman 0.1.0 installed from git
3. validate.py — DONE: replaced name-matching heuristic (lines 294-321) with real dimensional
   verification using mul_dims/div_dims/dims_equal. Falls back to old heuristic when any form
   lacks dimensions. Added imports: itertools.product, bridgman.{mul_dims,div_dims,dims_equal,format_dims}
4. unit_dimensions.py — DONE: dimensions_compatible now delegates to bridgman.dims_equal

## NEXT
- Run tests
- Commit

## FILES
- C:/Users/Q/code/propstore/pyproject.toml — added bridgman dep
- C:/Users/Q/code/propstore/propstore/validate.py — replaced heuristic with bridgman
- C:/Users/Q/code/propstore/propstore/unit_dimensions.py — delegate to bridgman
