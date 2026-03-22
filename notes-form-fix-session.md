# Form Fix Session Notes - 2026-03-21

## Findings

1. `validate_form_files` ALREADY EXISTS in `propstore/form_utils.py` lines 212-256 — task description was wrong about it being missing
2. All 16 form YAML files are stubs with only `name: <form_name>`
3. Schema at `schema/generated/form.schema.json` requires: `name` (string) and `dimensionless` (boolean)
4. Schema allows optional: `base`, `unit_symbol`, `qudt`, `parameters`, `common_alternatives`, `kind`, `note`, `dimensions`
5. `dimensions` keys must be from: L, M, T, I, Theta, N, J (SI base dimensions)
6. `kind` must be one of: quantity, category, boolean, structural
7. `additionalProperties: false` — no extra fields allowed

## Form Classification

Dimensionless (true): amplitude_ratio, dimensionless_compound, duration_ratio, ratio, count, rate, score
Dimensional (false): frequency, flow, flow_derivative, level, pressure, time
Non-quantity kinds: category, boolean, structural

## Plan

Populate all 16 form files with at minimum `name` + `dimensionless` + `kind` where appropriate.
For physical quantities, add `unit_symbol` and `dimensions`.
