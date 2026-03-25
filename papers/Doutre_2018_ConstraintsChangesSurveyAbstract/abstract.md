# Abstract

## Original Text (Verbatim)

This paper addresses the issue of the dynamic enforcement of a constraint in an argumentation system. The system consists in (1) an argumentation framework, made up, notably, of a set of arguments and of an attack relation, (2) an evaluation semantics, and (3) the evaluation result, computed from (1) and (2). An agent may want another agent to consider a new attack, or to have a given argument accepted, or even to relax the definition of the semantics. A constraint on any of the three components is thus defined, and it has to be enforced in the system. The enforcement may result in changes on components of the system. The paper surveys existing approaches for the dynamic enforcement of a constraint and its consequences, and reveals challenging enforcement cases that remain to be investigated.

---

## Our Interpretation

The paper tackles the problem of how to modify an argumentation system when an external requirement (constraint) must be satisfied --- for example, ensuring a particular argument is accepted, or changing which semantics is used. It provides a typology classifying constraint types, change types, and quality criteria, then maps 20+ existing approaches onto this grid. The key finding is that most work focuses on structural constraints with structural changes, while semantic constraints, semantic changes, and quality criteria beyond structural minimality remain largely underexplored. This is relevant to propstore because it provides the theoretical framework for understanding how to enforce render-time policy constraints on AFs.
