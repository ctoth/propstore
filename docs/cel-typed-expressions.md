# Typed CEL Expressions

Propstore treats CEL as an authoring frontend. CEL source can appear in YAML,
CLI input, JSON, and SQLite display columns, but semantic code does not reason
over parser ASTs or raw strings.

The production lifecycle is:

1. Authored text is decoded as `CelExpr` at IO boundaries.
2. `propstore.core.conditions.cel_frontend` parses and type-checks the source
   against the condition registry.
3. The frontend lowers the source to `ConditionIR`.
4. `CheckedCondition` records the source text, semantic IR, warnings, encoded
   IR, and registry fingerprint.
5. `CheckedConditionSet` represents the normalized conjunction used by
   compiler, sidecar, graph, activation, conflict detection, and world paths.
6. `ConditionSolver` answers runtime queries over checked conditions; Z3 is an
   internal backend behind `propstore.core.conditions.z3_backend`.

## Raw CEL

`CelExpr` is a `NewType` over `str`.

It means only that a string is intended to be CEL source. It does not mean the
expression parsed, type-checked, or references concepts that exist in a given
registry.

Use `CelExpr` for decoded authored source and display-oriented storage fields.
Do not pass it through core semantic/runtime paths as the condition carrier.

## Checked Conditions

`CheckedCondition` is the checked semantic condition object. It carries:

- the authored source text
- the lowered `ConditionIR`
- a registry fingerprint
- checker warnings
- canonical encoded IR for derived storage

It does not store CEL parser ASTs or Z3 expressions. Hard parse, type, or
unsupported-CEL errors prevent construction.

CEL validity is registry-relative. An expression such as `valid_from >= 100`
is checked only with respect to a registry where `valid_from` exists and has
numeric or timepoint semantics.

## Checked Condition Sets

`CheckedConditionSet` represents a normalized conjunction of
`CheckedCondition` objects.

It deduplicates by source text, sorts deterministically, and requires all
members to share one registry fingerprint.

## Runtime Contract

`ConditionSolver` accepts `CheckedCondition` sequences or
`CheckedConditionSet`. It rejects registry fingerprint mismatches and translates
only semantic `ConditionIR` into backend constraints.

Storage and display layers may retain authored strings. Sidecar and graph
runtime payloads expose checked semantic conditions or versioned encoded
`ConditionIR`; if the derived storage schema changes, rebuild the sidecar
rather than reading old shapes.
