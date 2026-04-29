# WS-G Audit Results

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
