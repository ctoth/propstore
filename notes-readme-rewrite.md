# README Rewrite Session — 2026-03-25

## GOAL
Rewrite README.md (~850 lines → ~170 lines) and create docs/ folder with reference material.

## STATE
- Plan approved at `~/.claude/plans/temporal-inventing-swan.md`
- Task restated, waiting for Q's confirmation before executing

## DONE
- Read current README (850 lines)
- Explored: no docs/ folder exists, no CHANGELOG.md
- Captured real CLI output for showcase (extensions is the star: 410 claims, 2050 stances, 126 attacks, 252 accepted)
- Found that hypothetical/sensitivity/derive return minimal output with current dataset — not good showcase material
- Planned new README structure and docs/ breakdown
- Plan approved by Q

## FILES
- `README.md` — to be rewritten
- `docs/data-model.md` — to be created (claim types, concepts, forms, conditions, stances, contexts from README lines 72-427)
- `docs/argumentation.md` — to be created (Dung AF, ATMS, semantic axes, run changelog from README lines 438-551)
- `docs/cli-reference.md` — to be created (full CLI reference from README lines 768-819)
- `docs/integration.md` — to be created (research-papers-plugin workflow, reconciliation, algorithm comparison)

## KEY DECISIONS
- Extensions output is the showcase hook (not hypothetical/sensitivity which return empty)
- Run-by-run changelog (Run 2A-7) moves to docs/argumentation.md as appendix
- 9 claim types with YAML examples move to docs/data-model.md
- Stats line ("315 concepts | 410 claims | 26 papers | 2050 stances") goes near top

## NEXT
- Commit all files
- Verify cross-links render on GitHub
