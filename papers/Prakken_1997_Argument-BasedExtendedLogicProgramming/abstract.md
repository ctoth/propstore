# Abstract

## Original Text (Verbatim)

Inspired by legal reasoning, this paper presents a semantics and proof theory of a system for defeasible argumentation. Arguments are expressed in a logic-programming language with both weak and strong negation. Conflicts between arguments are decided with the help of priorities on the rules. An important feature of the system is that these priorities are not fixed, but are themselves defeasibly derived as conclusions within the system. Thus debates on the choice between conflicting arguments can also be modelled. The semantics of the system is given with a fixpoint definition, while its proof theory is stated in dialectical style, where a proof takes the form of a dialogue between a proponent and an opponent of an argument: an argument is shown to be justified if the proponent can make the opponent run out of moves in whatever way the opponent attacks.

KEYWORDS: Argumentation, Nonmonotonic reasoning, Extended logic programming, Legal reasoning, Defeasible priorities

(Transcribed from page 1 of the authors' PDF.)

---

## Our Interpretation

The paper handles domains where conflicts are unavoidable and the criteria for settling them are themselves disputed. Its key result is a grounded, sceptical argumentation semantics with a matching dialogue proof procedure in which rule priorities are conclusions of arguments and can be attacked. For propstore it is a formal basis for keeping disagreement in storage and resolving it only at render time under argued, not hard-coded, preference orderings.
