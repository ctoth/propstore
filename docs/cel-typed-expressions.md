# Typed CEL Expressions

Propstore treats CEL expressions as a domain language, not generic text.

The production lifecycle is:

1. Authored YAML, CLI input, JSON, and SQLite rows carry textual CEL.
2. Decode boundaries brand that text as `CelExpr`.
3. Registry-aware validation constructs `CheckedCelExpr`.
4. Condition-set validation constructs `CheckedCelConditionSet`.
5. The Z3 backend translates checked expressions and caches by source plus
   registry fingerprint.

## Raw CEL

`CelExpr` is a `NewType` over `str`.

It means only that a string is intended to be CEL source. It does not mean the
expression parsed, type-checked, or references concepts that exist in a given
registry.

Use `CelExpr` for:

- decoded claim, concept, and source-local `conditions`
- queryable assumptions
- environment assumptions
- binding-derived CEL source
- storage values immediately after decode

Serialization still emits normal strings.

## Checked CEL

`CheckedCelExpr` is a frozen object created by the CEL checker.

It carries:

- the raw `CelExpr`
- the parsed AST
- a registry fingerprint
- checker warnings

It cannot be constructed accidentally as a string alias. Hard parse or type
errors prevent construction.

CEL validity is registry-relative. An expression such as `valid_from >= 100`
is checked only with respect to a registry where `valid_from` exists and has
numeric or timepoint semantics.

## Checked Condition Sets

`CheckedCelConditionSet` represents a normalized conjunction of checked CEL
expressions.

It deduplicates by source text, sorts deterministically, and requires all
members to share one registry fingerprint.

## Runtime Contract

The Z3 solver accepts `CelExpr`, `CheckedCelExpr`, and
`CheckedCelConditionSet`. Callers that already have a registry should prefer
checked values. The solver validates any raw `CelExpr` before translation and
caches checked expressions so repeated reasoning does not reparse or recheck
the same source repeatedly.

Storage and display layers may still expose plain strings. Core semantic paths
should carry `CelExpr` or checked CEL carriers.

