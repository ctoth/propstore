---
tags: [defeasible-logic, contextual-reasoning, multi-agent, deliberation, bdi]
---
Extends Defeasible Logic with modal operators (BEL, INT, DES, OBL), an ⊗-preference connective lifted from literals to rules, and a layer of meta-rules whose consequents are themselves rules so a cognitive agent can defeasibly derive *which rules for goals are in force in the current context* before applying them.
The proof theory introduces rule-level proof tags (±Δ_C, ±∂_C) alongside the standard literal tags (±Δ, ±∂), with conversions c ⊆ MOD × MOD letting one modality's rule act as another's; the framework is illustrated on a "Frodo" agent and an office-assistant context-detection example.
Supplies the agent-side complement to propstore's contextualised defeasible storage — meta-rules and rule-incompatibility map cleanly onto `propstore.aspic_bridge` rule priorities and `propstore.defeasibility` exception-injection.
