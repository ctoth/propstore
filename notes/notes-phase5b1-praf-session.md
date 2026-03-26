# Phase 5B-1: PrAF Core + MC Sampler Session Notes

## GOAL
Implement ProbabilisticAF dataclass and Monte Carlo sampler in propstore/praf.py, plus build_praf() in argumentation.py.

## DONE
- Read all 7 required files (Li 2012, Hunter 2017, Josang 2001, dung.py, opinion.py, argumentation.py, phase5b plan)
- Wrote tests/test_praf.py with all 12 tests per prompt spec

## KEY OBSERVATIONS
- dung.py: ArgumentationFramework(arguments, defeats, attacks), grounded_extension(), complete/preferred/stable_extensions()
- opinion.py: Opinion(b,d,u,a), .expectation() = b + a*u, .dogmatic_true(), .vacuous(), from_probability()
- argumentation.py: build_argumentation_framework(store, active_claim_ids) returns AF. Uses stances_between() to get stances, classifies into attacks/defeats/supports, applies Cayrol derived defeats
- Plan says: p_args and p_defeats are dict[..., Opinion], MC uses .expectation() for sampling probability
- Plan says: deterministic fallback when all P_D expectations >= 0.999
- Plan says: connected component decomposition is internal optimization
- Plan says: Agresti-Coull stopping: N > 4*p*(1-p)/epsilon^2 - 4, min 30 samples

## FILES
- tests/test_praf.py — 12 tests, all should fail (module doesn't exist yet)
- propstore/praf.py — TO CREATE: ProbabilisticAF, PrAFResult, compute_praf_acceptance, MC sampler
- propstore/argumentation.py — TO MODIFY: add build_praf()

## STATUS
- All 12 praf tests pass
- Full suite: 1171 passed in 53.18s (>= 1159 requirement met)
- pre-commit not installed as standalone command; ruff not available as standalone
- Need to check if there's a lint step in pyproject.toml or just commit

## NEXT
1. Commit the 3 files
2. Write report to reports/phase5b1-praf-core-mc-report.md
