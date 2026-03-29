# Abstract

## Original Text (Verbatim)

A major problem for knowledge representation is how to revise a knowledge system in the light of new information that is inconsistent with what is already in the system. Another related problem is that of contractions, where some of the information in the knowledge system is taken away.

Here, the problems of modelling revisions and contractions are attacked in two ways. First, two sets of rationality postulates or integrity constraints are presented, one for revisions and one for contractions. On the basis of these postulates it is shown that there is a natural correspondence between revisions and contractions.

Second, a more constructive approach is adopted based on the "epistemic entrenchment" of the facts in a knowledge system which determines their priority in revisions and contractions. We introduce a set of computationally tractable constraints for an ordering of epistemic entrenchments.

The key result is a representation theorem which says that a revision method for a knowledge system satisfies the set of rationality postulates, if and only if, there exists an ordering of epistemic entrenchment satisfying the appropriate constraints such that this ordering determines the retraction priority of the facts of the knowledge system. We also prove that the amount of information needed to uniquely determine the required ordering is linear in the number of atomic facts of the knowledge system.

---

## Our Interpretation

This paper solves the problem of principled belief retraction by defining epistemic entrenchment — a total ordering over beliefs that determines which ones to give up first when inconsistency arises. The central representation theorem shows this ordering is equivalent to AGM-rational revision, providing both a theoretical foundation and a computationally tractable approach (linear in atomic facts). For propstore, this is the formal inverse of fragility: low entrenchment equals high fragility, and the bridging conditions (C≤) and (C-) provide algorithms for converting between retraction behavior and entrenchment orderings.
