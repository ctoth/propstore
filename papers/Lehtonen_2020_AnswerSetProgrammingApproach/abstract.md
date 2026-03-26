# Abstract

## Original Text (Verbatim)

A major research direction in AI argumentation is the study and development of practical computational techniques for reasoning in different argumentation formalisms. Compared to abstract argumentation, developing algorithmic techniques for different structured argumentation formalisms, such as assumption-based argumentation and the general ASPIC+ framework, is more challenging. At present, there is a lack of efficient approaches to reasoning in ASPIC+. We develop a direct declarative approach based on answer set programming (ASP) to reasoning in an instantiation of the ASPIC+ framework. We establish formal foundations for direct declarative encodings for reasoning in ASPIC+ without preferences for several central argumentation semantics, and detail ASP encodings of semantics for which reasoning about acceptance is NP-hard in ASPIC+. Empirically, the ASP approach scales up to frameworks of significant size, thereby answering the current lack of practical computational approaches to reasoning in ASPIC+ and providing a promising base for capturing further generalizations within ASPIC+.

---

## Our Interpretation

This paper addresses the lack of efficient solvers for ASPIC+ by reformulating semantics in terms of "assumptions" (pairs of premises and defeasible rules) rather than exponentially many arguments, then encoding these directly in ASP. The key finding is that this assumption-based reformulation preserves all standard semantics (admissible, complete, stable, preferred) while keeping the search space polynomially bounded, enabling ASP solvers like Clingo to handle instances with thousands of atoms. This is directly relevant to propstore's argumentation layer as it provides a practical computational backend for ASPIC+ reasoning without the exponential blowup of constructing abstract AFs.
