# Abstract

## Original Text (Verbatim)

Compilers structured as a small number of monolithic passes are difficult to understand and difficult to maintain. Adding new optimizations often requires major restructuring of existing passes that cannot be understood in isolation. The steep learning curve is daunting, and even experienced developers find it hard to modify existing passes without introducing subtle and tenacious bugs. These problems are especially frustrating when the developer is a student in a compiler class.

An attractive alternative is to structure a compiler as a collection of many small passes, each of which performs a single task. This "micropass" structure aligns the actual implementation of a compiler with its logical organization, simplifying development, testing, and debugging. Unfortunately, writing many small passes duplicates code for traversing and rewriting abstract syntax trees and can obscure the meaningful transformations performed by individual passes.

To address these problems, we have developed a methodology and associated tools that simplify the task of building compilers composed of many fine-grained passes. We describe these compilers as "nanopass" compilers to indicate both the intended granularity of the passes and the amount of source code required to implement each pass. This paper describes the methodology and tools comprising the nanopass framework.

---

## Our Interpretation

The paper diagnoses two failure modes of existing compiler architectures — monolithic passes that no one can read, and "micropass" piles whose intermediate-language grammars are documented but not enforced — and proposes a framework that generates strongly-typed AST records, parsers, unparsers, and pass-expander boilerplate from formal `define-language` declarations, then lets each `define-pass` write transformer clauses only for the forms that change between input and output IL. The result is a 50-pass Scheme→Sparc compiler delivered in a 15-week course, with per-pass code reductions of roughly 3-4x versus the authors' previous micropass tooling, and bug isolation guaranteed by per-pass grammar enforcement plus reference-implementation comparison. For propstore the relevance is direct: this is the architectural template for a storage-schema migration framework — typed schema versions as ILs, single-discipline migrations as passes, automatic structural-recursion boilerplate, and a sequenced/named pass log that doubles as the migration history.
