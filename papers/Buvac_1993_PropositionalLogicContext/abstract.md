# Abstract

## Original Text (Verbatim)

In this paper we investigate the simple logical properties of *contexts*. We describe both the syntax and semantics of a general propositional language of context, and give a Hilbert style proof system for this language. A propositional logic of context extends classical propositional logic in two ways. Firstly, a new modality, ist(κ, φ), is introduced. It is used to express that the sentence, φ, holds in the context κ. Secondly, each context has its own vocabulary, i.e. a set of propositional atoms which are *defined* or *meaningful* in that context. The main results of this paper are the soundness and completeness of this Hilbert style proof system. We also provide soundness and completeness results (i.e. correspondence theory) for various extensions of the general system.

---

## Our Interpretation

Before this paper, contexts in AI (McCarthy, Guha/Cyc) had no formal logic; this gives one at the propositional level, with per-context vocabularies so a proposition can be meaningless rather than false in a context. Its key results are a sound and complete Hilbert system and axioms matching consistent, flat, and single-assignment (truth) contexts. For propstore it fixes the semantics that first-class ist(c, p) contexts and lifting rules build on.
