# Code Review — 2026-04-16

Deep-dive review of propstore. Scope per Q: code in `./propstore/`, tests in `./tests/`, papers in `./papers/` (notes + PDFs/PNGs).

## Axis files

| # | File | Agent | Concern |
|---|---|---|---|
| 1 | `axis-1-principle-adherence.md` | adversary | Violations of non-commitment, honest ignorance, no-gates-before-render, proposals-not-mutations |
| 2 | `axis-2-layer-discipline.md` | scout | Six-layer one-way dependency audit; strict-typed island integrity |
| 3a | `axis-3a-argumentation.md` | scout | Dung / ASPIC+ / bipolar / weighted / ranking fidelity |
| 3b | `axis-3b-uncertainty.md` | scout | Jøsang / DFQuAD / Denoeux / calibration fidelity |
| 3c | `axis-3c-revision.md` | scout | AGM / Darwiche-Pearl / IC merge / AF revision fidelity |
| 3d | `axis-3d-semantic.md` | scout | McCarthy / Fillmore / Pustejovsky / lemon / micropubs fidelity |
| 3e | `axis-3e-reasoning-infra.md` | scout | ATMS / Z3+CEL / treedecomp fidelity |
| 4 | `axis-4-test-adequacy.md` | analyst | Property vs. example coverage; formal-property-to-@given mapping; blind spots |
| 5 | `axis-5-silent-failures.md` | silent-failure-hunter | Fabricated priors, swallowed unknowns, manufactured confidence |
| 6 | `axis-6-limitation-honesty.md` | primary | Do declared gaps in CLAUDE.md cover the real gaps, or screen worse ones? |
| 7 | `axis-7-defeasible-datalog.md` | scout | Antoniou / Bozzato / Brewka / Diller 2025 / Fang / ABA fidelity; defeasible-on-datalog story |
| 8 | `axis-8-real-potential.md` | primary | What can this actually do today; where could it go with a little help — be real and precise |
| 9 | `axis-9-doc-drift.md` | comment-analyzer | CLAUDE.md / docstrings / paper citations / Known Limitations vs. actual code |
| — | `SYNTHESIS.md` | primary | Cross-axis findings, severity-ordered |
| — | `paper-manifest.md` | scout (pre-work) | Paper→cluster mapping so axis agents don't re-classify |

## Reporting discipline (binding on every agent)

Every finding carries:

- **Evidence** — exact `file:line` for code claims; `paper:section/page` for literature claims; paper PNG filename if read visually.
- **Severity** — `crit` (principle violation or correctness bug), `high` (design drift from paper), `med` (code smell / under-tested invariant), `low` (style/minor), `note` (observation, no action).
- **Recommendation** — optional. Omit rather than fabricate.
- **Explicit unknowns** — every report ends with an `## Open questions` section. "I didn't verify X" is required; silence about X is forbidden.

No manufactured confidence. "I don't know yet" is a first-class finding. Runtime evidence preferred over source inspection for causal claims.

## Layout

```
reviews/2026-04-16-code-review/
  README.md               # this file
  paper-manifest.md       # scout output (pre-work)
  axis-1-principle-adherence.md
  axis-2-layer-discipline.md
  axis-3a-argumentation.md
  axis-3b-uncertainty.md
  axis-3c-revision.md
  axis-3d-semantic.md
  axis-3e-reasoning-infra.md
  axis-4-test-adequacy.md
  axis-5-silent-failures.md
  axis-6-limitation-honesty.md
  axis-7-defeasible-datalog.md
  axis-8-real-potential.md
  axis-9-doc-drift.md
  SYNTHESIS.md
```
