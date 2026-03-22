# Abstract

## Original Text (Verbatim)

This paper generalizes the encoding of argumentation frameworks beyond the classical 2-valued propositional logic system (PL2) to 3-valued propositional logic systems (PL3s) and fuzzy propositional logic systems (PL[0,1]s), employing two key encodings: normal encoding (ec1) and regular encoding (ec2). Specifically, via ec1 and ec2, we establish model relationships between Dung's classical semantics (stable and complete semantics) and the encoded semantics associated with Kleene's PL3 and Lukasiewicz's PL3. Through ec1, we also explore connections between Gabbay's real equational semantics and the encoded semantics of PL[0,1]s, including showing that Gabbay's Eq_max^R and Eq_inverse^R correspond to the fuzzy encoded semantics of PL[0,1]^G and PL[0,1]^P respectively. Additionally, we propose a new fuzzy encoded semantics (Eq^L) associated with Lukasiewicz's PL[0,1] and investigate interactions between complete semantics and fuzzy encoded semantics. This work strengthens the links between argumentation frameworks and propositional logic systems, providing a framework for constructing new argumentation semantics.

---

## Our Interpretation

The paper addresses the gap between argumentation framework semantics and propositional logic by showing that different logic systems (classical, 3-valued, fuzzy) yield different AF semantics when the same encoding formula is evaluated. The key finding is that simply switching the logic system used to evaluate a fixed formula produces a systematic correspondence: Kleene gives stable semantics, Lukasiewicz gives complete semantics, and various fuzzy t-norms give known equational semantics plus a new Lukasiewicz-based one. This is relevant because it provides a unified computational framework for AF semantics via propositional logic model checking and opens the door to constructing novel semantics by choosing new logic systems.
