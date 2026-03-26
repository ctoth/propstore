# Abstract

## Paraphrase

The paper presents a practical way to verify linear-logic inference rules with Z3. It encodes Gentzen-style sequents as solver constraints, uses negated candidate rules to test derivability, and applies the pattern to two fragments of linear logic: MLL+Mix and MILL. The result is a small reusable verification template that proves several derived rules, exposes some non-derivable variants, and shows where Z3 runs into memory limits.

