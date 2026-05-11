# Abstract

## Original Text (Verbatim)

The imperfect nature of context in Ambient Intelligence environments and the special characteristics of the entities that possess and share the available context information render contextual reasoning a very challenging task. The accomplishment of this task requires formal models that handle the involved entities as autonomous logic-based agents and provide methods for handling the imperfect and distributed nature of context. This paper proposes a solution based on the Multi-Context Systems paradigm in which local context knowledge of ambient agents is encoded in rule theories (contexts), and information flow between agents is achieved through mapping rules that associate concepts used by different contexts. To handle imperfect context, we extend Multi-Context Systems with nonmonotonic features: local defeasible theories, defeasible mapping rules, and a preference ordering on the system contexts. On top of this model, we have developed an argumentation framework that exploits context and preference information to resolve potential conflicts caused by the interaction of ambient agents through the mappings, and a distributed algorithm for query evaluation.

**Index Terms:** Ambient Intelligence, contextual reasoning, defeasible reasoning, argumentation systems.

---

## Our Interpretation

Bikakis & Antoniou propose a multi-context system in which each context is a defeasible logic theory, contexts are linked by defeasible mapping rules whose bodies cite foreign-context literals, and a per-context total preference ordering over other contexts breaks ambiguity from cross-context information flow. The semantics is given both model-theoretically and via a Dung-style argumentation framework that uses the context preference to decide attack/defeat, and they present a distributed peer-to-peer algorithm (P2P_DR) that is sound, complete, and terminating against the argumentation semantics on finite MCS. The paper is the canonical statement of distributed defeasible argumentation over MCS for Ambient Intelligence and is the closest precursor to Al-Anbaki et al. 2019, against which propstore needs to compare any future distributed-context implementation.
