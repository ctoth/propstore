# Abstract

## Original Text (Verbatim)

This paper addresses the problem of revising a Dung-style argumentation framework by adding finitely many new arguments which may interact with old ones. We study the behavior of the extensions of the augmented argumentation frameworks, taking also into account possible changes of the underlying semantics (which may be interpreted as corresponding changes of proof standards). We show both possibility and impossibility results related to the problem of enforcing a desired set of arguments. Furthermore, we prove some monotonicity results for a special class of expansions with respect to the cardinality of the set of extensions and the justification state.

---

## Our Interpretation

The paper formalizes what happens when you add new arguments to an existing Dung argumentation framework. It defines three expansion types (normal, strong, weak) based on attack direction constraints and two enforcement modes (conservative = same semantics, liberal = different semantics). The key positive result is that any conflict-free set can be enforced as an extension by adding just one new argument with carefully chosen attacks. For weak expansions (new arguments only receive attacks), monotonicity holds: extension counts and justification states are preserved. This is directly relevant to incremental knowledge base updates in propstore's argumentation layer.
