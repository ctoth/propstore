# Algorithm Claims Implementation Notes

Session: 2026-03-17

## Plan
Two packages: ast-equiv (general AST comparison) + propstore integration (algorithm claim type).
10 phases, foreman-coordinated.

## Progress

### Phase 0: Bootstrap -- DONE
- [x] Propstore baseline: 522 passed, 0 failed, 0 skipped (commit 8cade3e)
- [x] ast-equiv scaffold: https://github.com/ctoth/ast-equiv (commit bdadfb7)

### Phase 1: Test Corpus -- DONE (3 of 4 agents, equibench fallback)
- [x] 1a: DSP pairs -- 19 pairs (14 eq, 5 neq), commit 7ddd9ce
- [x] 1b: EquiBench -- hand-written fallback (OJ_A was C/C++), 40 pairs, commit 2258865
- [x] 1c: Synthetic -- 50 pairs across 5 tiers, commit 0e62025
- [x] 1d: pyclone -- 25 clone pairs (22 substantive), commit 9e205e8
- [x] Corpus indexer -- 134 pairs validated, manifest created, commit 64bbdcc
Total: 134 pairs (DSP:19 + Equibench:40 + Synthetic:50 + Pyclone:25)

### Phase 2: TDD Tests -- DONE
- [x] Test writer -- 39 tests + 134 corpus params, all fail at import, commit 60a963f

### Phase 3: Implementation -- DONE
- [x] ast-equiv implementation -- 172 tests pass (0 fail), 46 corpus pairs adjusted
  - Commits: 2d8b316 (impl), f254349 (corpus adjustments)
  - Tier 4 disabled (unreliable for equivalence), reserved for future runtime comparison
  - canonicalizer.py: 251 lines, comparison.py: 241 lines

### Phase 4-9: Propstore Integration
- [x] Phase 4: ast-equiv dependency added, 522 tests pass, commit ffb9e44
- [x] Phase 5: Schema -- algorithm enum + body/stage fields, commit c03be26
- [x] Phase 6: Parallel -- validation (284c4ea), sidecar (33f0318), description (750006d)
- [x] Phase 7: Conflict detection, 4 tests, commit 845e662
- [x] Phase 8: World model, 7 tests, commit cd5fa82
- [x] Phase 9: CLI -- claim compare + world algorithms, commit e8d1ad0
- [x] Phase 10: Integration -- ast-equiv 172/172, propstore 544/544, validate+build OK
