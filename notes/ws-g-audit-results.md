# WS-G Audit Results

## AGM And Iterated Coverage Gates

- `K-6`, `K-7`, `K-8`, and Harper — unasserted-but-correct. First full audit:
  `logs/test-runs/WS-G-audit-first-20260429-020058.log`. The final audit
  matrix passed in `logs/test-runs/WS-G-audit-20260429-020445.log`.
- Darwiche-Pearl `C1`-`C4` and `CR1`-`CR4` for bullet, lexicographic, and
  restrained revision — unasserted-but-correct in the deterministic audit
  matrix. Final audit log: `logs/test-runs/WS-G-audit-20260429-020445.log`.
- `EE1`-`EE5` — unasserted-but-correct in the audit matrix over the finite
  representative formula set. Final audit log:
  `logs/test-runs/WS-G-audit-20260429-020445.log`.

## IC Merge Coverage Gates

- `IC4` — unasserted-but-correct. First run:
  `logs/test-runs/WS-G-ic-coverage-first-20260429-015120.log`.
  Both SIGMA and GMAX passed the concrete fairness gate from
  Konieczny and Pino Perez 2002, Definition 3.1, p.778.
- `Maj` — unasserted-but-correct. First run:
  `logs/test-runs/WS-G-ic-coverage-first-20260429-015120.log`.
  SIGMA passed the majority gate from Theorem 4.2, p.786.
- `Arb` — first run exposed a bad expected fixture, not a production
  violation. The page image for Konieczny and Pino Perez 2002, Example 4.15
  on p.791 states
  `mod(Delta_mu^GMax(Psi)) = {(0,0,1,0), (0,1,0,0)}`. With variables ordered
  as `S,T,P,I`, that is `{P}` or `{T}`. The original test expected `{S,P}` or
  `{T,P}` and was corrected before classification. The corrected gate records
  GMAX as unasserted-but-correct for the paper's block-of-flats example.
