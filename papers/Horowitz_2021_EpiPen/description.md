---
tags: [epistemic-logic, dynamic-epistemic-logic, smt-solver, knowledge-representation, modal-logic]
---
Presents EpiPEn, a Python DSL for epistemic logic puzzles that encodes agent knowledge and public announcements as first-order constraints and delegates solving to Z3. The system adds simultaneous-action blocks, actual-world simulation, and solver-verified simplification hints to handle puzzles that would otherwise produce explosive formulas. It works on several classic examples, but runs into limits on self-referential surprise puzzles and non-linear arithmetic-heavy reasoning.

