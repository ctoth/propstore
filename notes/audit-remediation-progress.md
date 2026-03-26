# Audit Remediation — COMPLETE

## 2026-03-25

### Final Verdict: MERGE

**1317 pass, 1 pre-existing fail, 34 commits, 67 new tests.**

### Summary by Iteration

| Iter | Focus | Findings | New Tests | Gate |
|------|-------|----------|-----------|------|
| 1 | Quick wins | F1-F8 (8) | +17 | PASS |
| 2 | Isolated refactors | F9-F12, F16 (5) | +16 | PASS |
| 3 | Semantic/argumentation | F13-F15, F27-F29 (5+3) | +19 | PASS |
| 4 | Architecture | F17-F19, F30-F31 (5) | +10 | PASS |
| 5 | Calibrator redesign | F26, M8 (2) | +5 | PASS |
| 6 | Documentation | F20-F25 (6) | 0 | PASS |
| 7 | Final verification | — | — | MERGE |

### Key Achievements

1. **Security:** Patched real code execution via `parse_expr` (equation_comparison.py)
2. **Architecture:** Removed vacuous-opinion build-time gate → render-time only
3. **Architecture:** relate.py now writes to `proposals/`, not source storage; `pks promote` command added
4. **Architecture:** `data_utils.py` extracted; WorldModel accepts `sidecar_path` directly
5. **Calibration:** Evidence model redesigned — local CDF density, not raw corpus size
6. **Correctness:** mc_confidence parametric, float tolerance comparisons, PrAF deterministic defeats
7. **Safety:** z3 `is_true()`, embed.py exception narrowing, CEL type validation, cache clearing
8. **Coverage:** Property tests for Dung AF, PrAF P_A bound, opinion algebra invariants
9. **Documentation:** Literature table with implementation status, known limitations documented

### Deferred (future work)
- ASPIC+ real argument construction (rules, sub-arguments)
- Tree decomposition asymptotic improvement
- P_A vs DF-QuAD base score principled separation
- Grounded extension post-hoc pruning formal analysis
- Denoeux 2019 decision layer
- Dixon 1993 AGM operations
- Hunter & Thimm COH constraint enforcement
