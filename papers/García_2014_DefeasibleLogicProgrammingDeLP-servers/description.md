---
tags:
  - defeasible-logic-programming
  - delp
  - argumentation
  - contextual-queries
  - explanation
  - dialectical-trees
  - multi-agent-systems
  - structured-argumentation
  - warrant
  - distributed-reasoning
relevance: high
---

# Description

García & Simari (2014) consolidates the Defeasible Logic Programming (DeLP) language, the DeLP-Server execution architecture for serving argumentative queries to multiple client agents, and the *contextual query* mechanism whereby a client ships a private d.l.p. fragment alongside each query so the server can compute warrant under merged (server-public ⋄ client-private) programs without mutating its own knowledge base. The paper formalises three concrete merge operators ⊕, ⊗, ⊖ over (Π, Δ) program pairs (private-wins, public-wins, subtract) and defines δ-Explanations as the triple of marked dialectical trees `(T*_U(Q), T*_U(Q̄), T*_D(Q))` that the server returns alongside its four-valued answer (YES / NO / UNDECIDED / UNKNOWN) so the client can audit every argument and counterargument considered. For propstore this paper is highly relevant: it gives a paper-anchored model for the `query_claim()` / `build_arguments_for()` backward-chaining surface, the contextual-query operators map directly onto how `ist(c, p)` contexts compose with the underlying claim store, and the dialectical-tree explanation format is a usable target representation for what propstore's argumentation render layer should expose to downstream consumers.
