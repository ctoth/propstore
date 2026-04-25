# Citations

## Reference List

[1] G. Aigner, A. Diwan, D. Heine, M. Lam, D. Moore, B. Murphy, and C. Sapuntzakis. An overview of the SUIF2 compiler infrastructure. Technical report, Stanford University, 2000.

[2] G. Aigner, A. Diwan, D. Heine, M. Lam, D. Moore, B. Murphy, and C. Sapuntzakis. The SUIF2 compiler infrastructure. Technical report, Stanford University, 2000.

[3] J. R. Allen and K. Kennedy. Pfc: A program to convert fortran to parallel form. Technical Report MASC-TR82-6, Rice University, Houston, TX, 1982.

[4] Cliff Click and Keith D. Cooper. Combining analyses, combining optimizations. *ACM Transactions on Programming Languages and Systems*, 17(2), 1995.

[5] R. Kent Dybvig. *The Scheme Programming Language*. MIT Press, third edition, 2002.

[6] R. Kent Dybvig, Robert Hieb, and Carl Bruggeman. Syntactic abstraction in Scheme. *Lisp and Symbolic Computation*, 5(4):295-326, 1993.

[7] Wilf R. LaLonde and Jim des Rivieres. A flexible compiler structure that allows dynamic phase ordering. In *Proceedings of the ACM SIGPLAN Symposium on Compiler Construction*, pages 134-139, 1982.

[8] Sorin Lerner, David Grove, and Craig Chambers. Composing dataflow analyses and transformations. In *Proceedings of the 29th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages*, pages 270-282, 2002.

[9] N. Nystrom, M. Clarkson, and A. Myers. Polyglot: An extensible compiler framework for Java. In *Proceedings of the 12th International Conference on Compiler Construction*, volume 2622 of *Lecture Notes in Computer Science*, pages 138-152. Springer-Verlag, 2003.

[10] Anthony Pioli and Michael Hind. Combining interprocedural pointer analysis and conditional constant propagation. Research Report 21532, IBM T. J. Watson Center, 1999.

[11] D. Tarditi, G. Morrisett, P. Cheng, C. Stone, R. Harper, and P. Lee. TIL: a type-directed optimizing compiler for ML. In *Proceedings of the ACM SIGPLAN 1996 conference on Programming language design and implementation*, pages 181-192, 1996.

[12] C. van Reeuwijk. Tm: a code generator for recursive data structures. *Software Practice and Experience*, 22(10):899-908, 1992.

[13] C. van Reeuwijk. Rapid and robust compiler construction using template-based metacompilation. In *Proceedings of the 12th International Conference on Compiler Construction*, volume 2622 of *Lecture Notes in Computer Science*, pages 247-261. Springer-Verlag, 2003.

[14] Oscar Waddell and R. Kent Dybvig. Fast and effective procedure inlining. In Pascal Van Hentenryck, editor, *Fourth International Symposium on Static Analysis*, volume 1302 of *Lecture Notes in Computer Science*, pages 35-52. Springer-Verlag, 1997.

[15] P. Wadler. Deforestation: Transforming programs to eliminate trees. In *ESOP '88: European Symposium on Programming*, volume 300 of *Lecture Notes in Computer Science*, pages 344-358. Springer-Verlag, 1988.

[16] D. C. Wang, A. W. Appel, J. L. Korn, and C. S. Serra. The zephyr abstract syntax description language. In *Proceedings of the USENIX Conference on Domain-Specific Languages*, pages 213-228, 1997.

[17] M. N. Wegman and F. K. Zadeck. Constant propagation with conditional branches. *ACM Transactions on Programming Languages and Systems*, 3(2):181-210, 1991.

[18] D. Whitfield and M. L. Soffa. An approach to ordering optimizing transformations. In *Proceedings of the Second ACM SIGPLAN Symposium on Principles & Practice of Parallel Programming*, pages 137-146, 1990.

## Key Citations for Follow-up

- **[16] Wang et al. 1997 — Zephyr ASDL**: The direct ancestor of `define-language`; ASDL gave language-specific data-structure declarations and parsers/unparsers but did not integrate pass definitions. For propstore: this is what the schema-definition half of a migration framework looks like in isolation. Worth reading to understand what nanopass adds *on top of* a typed IR description.
- **[11] Tarditi et al. 1996 — TIL**: Per-pass IL type-checking as a debugging tool. Empirical confirmation that "type-check the output of every pass" catches bugs. Closest precedent for the validation discipline propstore needs at every storage migration boundary.
- **[6] Dybvig, Hieb, Bruggeman 1993 — `syntax-case`**: The host-language macro system that makes `define-language`/`define-pass` implementable. Background reading for anyone proposing to implement a similar framework in a different host (e.g., Python decorators or a Pydantic plugin for propstore).
- **[15] Wadler 1988 — Deforestation**: The technique nanopass authors propose for fusing many independently developed improvement passes back into one efficient pass. If propstore migrations ever need fast bulk replay, deforestation-style fusion is the technique to investigate.
- **[9] Nystrom et al. 2003 — Polyglot**: Alternative answer to "how do you make pass-and-IL extension scale?" via OOP rather than language inheritance. Useful contrast for a propstore design discussion of which extensibility model fits Python better.
