# Abstract

## Original Text (Verbatim)

The abstract nature of Dung's seminal theory of argumentation accounts for its widespread application as a general framework for various types of non-monotonic reasoning, and more generally, reasoning in the presence of conflict. A Dung argumentation framework is instantiated by arguments and a binary conflict based attack relation, defined by some underlying logical theory. The justified arguments under different extensional semantics are then evaluated, and the aims of these arguments define the interests of the underlying theory. To determine a unique set of justified arguments often requires a preference relation on arguments to determine the success of attacks between arguments. However, preference information is often itself defeasible, conflicting and so subject to argumentation. Hence, in this paper we extend Dung's theory to accommodate arguments that claim preferences between other arguments, thus incorporating meta-level argumentation based reasoning about preferences in the object level. We then define and study application of the full range of Dung's extensional semantics to the extended framework, and study special classes of the extended framework. The extended theory preserves the abstract nature of Dung's approach, thus aiming at a general framework for non-monotonic formalisms that accommodate defeasible reasoning about as well as with preference information. We illustrate by formalising argument based logic programming with defeasible priorities in the extended theory.

---

## Our Interpretation

The paper solves a key gap in abstract argumentation: preferences should not be treated as a fixed external ranking, because claims about preference are themselves defeasible and arguable. Modgil's solution is to extend Dung's framework with arguments that attack attacks, then recover Dung-style semantics for that richer object. For propstore, this is the core abstract design for making provenance or policy preferences first-class argumentative content instead of hard-coded tie-breakers.
