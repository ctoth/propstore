---
tags: [compilers, intermediate-representation, migration-framework, dsl, scheme]
---
Defines the nanopass methodology and its supporting Scheme-embedded DSL (`define-language`, `define-pass`, language inheritance via `extends`+/`-`, and a pass expander) for building compilers as long sequences of tiny, single-discipline passes whose intermediate-language grammars are formally specified and statically enforced as strongly-typed AST records.
The framework auto-generates parsers, unparsers, partial parsers, and structural-recursion boilerplate from each language definition, validates output via per-pass grammar enforcement plus reference-implementation comparison, and is demonstrated on a 50-pass Scheme→Sparc compiler delivered in a 15-week course with per-pass code reductions of roughly 3-4x versus the authors' previous micropass tools.
For propstore, this paper is the architectural template for a storage-schema migration framework: typed schema versions as ILs, single-discipline migrations as passes, automatic boilerplate, and a sequenced/named pass log that doubles as the migration history.
