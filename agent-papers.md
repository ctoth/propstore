# agent-papers.md

Retrieval manifest for BDI-on-propstore. Read-and-iterate targets.
Organized by what gap in the stack each paper fills.

Format: citation — venue/arxiv/DOI — one-line relevance — stack role.

---

## 0 · Foundations (read first, calibrate vocabulary)

- **Bratman, M. (1987).** *Intention, Plans, and Practical Reason.* Harvard University Press. — Not a paper, the book. Reconsideration filter, future-directed intention, the philosophical core of BDI. — Stack role: motivates the entire `revision/` + `fragility.py` + `sensitivity.py` loop; gives the language for intention stability.
- **Rao, A. S. & Georgeff, M. P. (1991).** "Modeling Rational Agents within a BDI-Architecture." *KR'91*, pp. 473-484. — Modal operators for B/D/I, commitment strategies (blind, single-minded, open-minded). — Stack role: the commitment strategies map 1:1 onto `revision/operators.py` operator choice.
- **Rao, A. S. & Georgeff, M. P. (1995).** "BDI Agents: From Theory to Practice." *ICMAS'95*. — The bridge from modal logic to implementable plan-library architectures. — Stack role: gives the reasoning-cycle skeleton the top-level BDI driver will follow.
- **Rao, A. S. (1996).** "AgentSpeak(L): BDI Agents Speak Out in a Logical Computable Language." *MAAMAW'96*. — AgentSpeak as executable BDI. Plan triggering events, context, body. — Stack role: syntactic reference for how plans should look as `rule_documents.py` entries.
- **Wooldridge, M. (2000).** *Reasoning About Rational Agents.* MIT Press. — Formal semantics, LORA logic. — Stack role: reference for how to talk about the deliberative cycle precisely.
- **Bordini, R. H., Hübner, J. F. & Wooldridge, M. (2007).** *Programming Multi-Agent Systems in AgentSpeak Using Jason.* Wiley. — The working reference implementation. Operational baseline to benchmark against. — Stack role: read to understand what a naive BDI does so you can see where propstore's substrate changes the answer.

## 1 · Argumentation-based practical reasoning (the critical bridge)

- **Parsons, S., Sierra, C. & Jennings, N. R. (1998).** "Agents that reason and negotiate by arguing." *J. Logic and Computation* 8(3):261-292. — Foundational: agents whose deliberation is argument construction, not rule-firing. — Stack role: establishes the pattern `aspic_bridge.py` already implements. Read to understand what you already built.
- **Rahwan, I. & Amgoud, L. (2006).** "An argumentation-based approach for practical reasoning." *AAMAS'06*, pp. 347-354. — **Highest priority.** Maps desires / plans / actions directly onto argument schemes. The closest living match to what propstore already has. — Stack role: this paper is almost a specification for how to wire the existing argumentation stack to a BDI loop. Start here.
- **Amgoud, L. & Prade, H. (2009).** "Using arguments for making and explaining decisions." *AI* 173(3-4):413-436. — Argumentation as decision theory. Connects preference ordering to argument strength. — Stack role: informs how `preference.py` should feed the render-time resolution strategies.
- **Hulstijn, J. & van der Torre, L. (2004).** "Combining goal generation and planning in an argumentation framework." *NMR'04*. — Goals *and* plans as arguments in one AF. — Stack role: tells you how to treat desires and plans as arguments with attack relations under one Dung semantics.
- **Atkinson, K. & Bench-Capon, T. (2007).** "Practical reasoning as presumptive argumentation using action based alternating transition systems." *AI* 171(10-15):855-874. — Value-based argumentation for action selection. — Stack role: ties ASPIC+ preferences to moral/social values — feeds the "LLM judgement as last-mile veto" story later.
- **Modgil, S. & Prakken, H. (2018).** "A general account of argumentation with preferences." *AI* 248:51-104. — Already cited in `aspic.py`. — Stack role: you are already here; re-read when fixing the rule-ordering gap.

## 2 · Goal types, goal interaction, plan failure

- **van Riemsdijk, M. B., Dastani, M. & Meyer, J.-J. Ch. (2008).** "Goals in conceptual agent programming frameworks." *AGS'08*. — Typed goals: achievement, maintenance, perform, test, query. — Stack role: your desire set should not be flat; goal types become different context/condition signatures on desire claims.
- **Thangarajah, J., Padgham, L. & Winikoff, M. (2003).** "Detecting and avoiding interference between goals in intelligent agents." *IJCAI'03*. — Resource, precondition, effect interaction between plans. — Stack role: directly an AF construction problem — interference = attack relation.
- **Thangarajah, J., Harland, J., Morley, D. & Yorke-Smith, N. (2010).** "Operational behaviour for executing, suspending and aborting goals in BDI agent systems." *DALT'10*. — Goal lifecycle states. — Stack role: tells you what states an intention-as-ATMS-node needs to carry.
- **Padgham, L. & Lambrix, P. (2005).** "Formalisations of capabilities for BDI-agents." *AAMAS J.* 10(3):249-271. — Capabilities as the link between plans and actions. — Stack role: capabilities are where material-db/recipe-db plug in as grounded affordances.
- **Schut, M., Wooldridge, M. & Parsons, S. (2004).** "The theory and practice of intention reconsideration." *JETAI* 16(4):261-293. — When should an agent reconsider intentions? Empirical + theoretical. — Stack role: calibration targets for `fragility.py` / `sensitivity.py` thresholds.

## 3 · HTN planning in BDI (first-principles fallback)

- **Sardina, S., de Silva, L. & Padgham, L. (2006).** "Hierarchical planning in BDI agent programming languages: a formal approach." *AAMAS'06*. — HTN decomposition integrated with BDI plan libraries; first-principles synthesis when library is insufficient. — Stack role: the "read more papers when stuck" impasse-recovery loop is a realization of this paper's first-principles branch, with the research-papers-plugin pipeline as the synthesis mechanism.
- **de Silva, L., Sardina, S. & Padgham, L. (2009).** "First principles planning in BDI systems." *AAMAS'09*. — Explicit planner-in-the-loop. — Stack role: reference for the shape of an impasse handler.
- **Meneguzzi, F. & Luck, M. (2013).** "Composing high-level plans for declarative agent programming." *AAMAS'13*. — Automated plan synthesis in BDI. — Stack role: the authors wanted a knowledge pipeline they did not have; you built it as the plugin.

## 4 · Commitment, multi-agent, social layer

- **Singh, M. P. (1999).** "An ontology for commitments in multiagent systems." *Artif. Intell. Law* 7:97-113. — Social commitments as first-class objects. — Stack role: commitments become context-qualified claims under the same discipline as beliefs.
- **Singh, M. P. (2008).** "Semantical considerations on dialectical and practical commitments." *AAAI'08*. — Commitment protocol semantics. — Stack role: the multi-agent branch-merge story — each agent's commitments live on their branch, merge via IC operators.
- **Fornara, N. & Colombetti, M. (2004).** "A commitment-based approach to agent communication." *Applied AI* 18(9-10):853-866. — ACL based on commitments, not FIPA speech acts. — Stack role: how agents talk to each other in a way the argumentation layer can ingest.
- **Broersen, J., Dastani, M., Hulstijn, J. & van der Torre, L. (2002).** "Goal generation in the BOID architecture." *Cognitive Science Quarterly* 2(3-4):428-447. — Beliefs/Obligations/Intentions/Desires with prioritized rules to resolve conflicts. — Stack role: BOID is a special case of what you have — obligations are just high-entrenchment context-qualified desires.

## 5 · Uncertainty in BDI (sparse literature, pick carefully)

- **Casali, A., Godo, L. & Sierra, C. (2011).** "A graded BDI agent model to represent and reason about preferences." *Artif. Intell.* 175(7-8):1468-1478. — Possibility-theoretic BDI with graded mental attitudes. — Stack role: translation target into the Jøsang opinion algebra.
- **Chen, Y., Hong, J., Liu, W., Godo, L., Sierra, C. & Loughlin, M. (2013).** "Incorporating PGMs into a BDI architecture." *PRIMA'13*. — Probabilistic graphical models for belief. — Stack role: existing attempts to do what propstore does more principally; read for what they got wrong.
- **Kwiatkowska, M., Norman, G. & Parker, D. (2011).** "PRISM 4.0: verification of probabilistic real-time systems." *CAV'11*. — PRISM for probabilistic BDI plan verification. — Stack role: benchmark baseline.

## 6 · Calibration, honest uncertainty, opinion algebra

- **Jøsang, A. (2001).** "A logic for uncertain probabilities." *Int. J. Uncertainty, Fuzziness* 9(3):279-311. — Already cited in `opinion.py`. The foundation. — Stack role: you are here.
- **Jøsang, A. (2016).** *Subjective Logic: A Formalism for Reasoning under Uncertainty.* Springer. — The book. Fusion, trust transitivity, base rates, extended operators (deduction/abduction/comultiplication — the ones CLAUDE.md notes as missing). — Stack role: the reference for filling in the extended-operator gap.
- **Guo, C., Pleiss, G., Sun, Y. & Weinberger, K. Q. (2017).** "On calibration of modern neural networks." *ICML'17*. — Temperature scaling, ECE, reliability diagrams. — Stack role: calibration bridge from LLM logits to Jøsang opinions — the ADC-side transducer function.
- **Kuleshov, V., Fenner, N. & Ermon, S. (2018).** "Accurate uncertainties for deep learning using calibrated regression." *ICML'18*. — Calibration for continuous outputs, not just classification. — Stack role: matters when LLM extracts numerical values (quantities with units) from text.
- **Lin, S., Hilton, J. & Evans, O. (2022).** "Teaching models to express their uncertainty in words." *arXiv:2205.14334*. — LLMs saying "I'm 60% confident" in natural language and having it mean something. — Stack role: the ADC boundary — LLM confidence → Jøsang opinion prior.

## 7 · LLM-as-transducer, structured extraction, tool use

- **Schick, T., Dwivedi-Yu, J., Dessì, R., et al. (2023).** "Toolformer: language models can teach themselves to use tools." *NeurIPS'23*. — LLMs invoking external APIs. — Stack role: the DAC-side tool-invocation story; motivates MCP-driven effectors.
- **Yao, S., Zhao, J., Yu, D., et al. (2023).** "ReAct: Synergizing reasoning and acting in language models." *ICLR'23*. — Reasoning traces + action invocation. — Stack role: ReAct is the naive version of what you get for free when deliberation is symbolic and action is LLM-rendered — read to see what you avoid.
- **Wei, J., Wang, X., Schuurmans, D., et al. (2022).** "Chain-of-thought prompting elicits reasoning in large language models." *NeurIPS'22*. — CoT as deliberation-in-prompt. — Stack role: the anti-pattern — CoT is deliberation without provenance; propstore is deliberation *with* provenance.
- **Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K. & Yao, S. (2023).** "Reflexion: language agents with verbal reinforcement learning." *NeurIPS'23*. — Agents that critique their own outputs. — Stack role: reflexion-style critique belongs at the DAC boundary as last-mile veto, *not* in the deliberative core.
- **Hao, S., Gu, Y., Ma, H., Hong, J., Wang, Z., Wang, D. Z. & Hu, Z. (2023).** "Reasoning with language model is planning with world model." *EMNLP'23*. — LLMs as world models for planning. — Stack role: exactly the role you do *not* give the LLM — the world model is propstore + material-db + recipe-db with calibration, not the LLM.

## 8 · Alignment / paperclip avoidance at the boundary

- **Omohundro, S. M. (2008).** "The basic AI drives." *AGI'08*. — Instrumental convergence, the paperclip argument's skeleton. — Stack role: read to know what you are defending against.
- **Soares, N., Fallenstein, B., Armstrong, S. & Yudkowsky, E. (2015).** "Corrigibility." *AAAI Workshops*. — What "correctable" means formally. — Stack role: propstore's non-commitment discipline is a form of structural corrigibility — no locked-in utility function.
- **Hadfield-Menell, D., Russell, S. J., Abbeel, P. & Dragan, A. (2016).** "Cooperative inverse reinforcement learning." *NeurIPS'16*. — Agents that treat their utility function as uncertain and learn it from the human. — Stack role: aligns naturally with vacuous-prior opinions on desire claims — the agent is *literally* uncertain about what it wants and must accumulate evidence.
- **Shah, R., Gundotra, N., Abbeel, P. & Dragan, A. (2019).** "On the feasibility of learning, rather than assuming, human biases for reward inference." *ICML'19*. — Don't assume human rationality when inferring preferences. — Stack role: informs how LLM-ADC extracts goals from human text without collapsing disagreement.
- **Leike, J., Krueger, D., Everitt, T., Martic, M., Maini, V. & Legg, S. (2018).** "Scalable agent alignment via reward modeling." *arXiv:1811.07871*. — Reward modeling with uncertainty. — Stack role: reward models are claims too; should live on a propstore branch with their own provenance.

## 9 · Adjacent: normative / deontic layers (optional but cheap wins)

- **Dignum, F. (1999).** "Autonomous agents with norms." *Artif. Intell. Law* 7:69-79. — Norms as constraints on deliberation. — Stack role: norms become context-qualified attack relations.
- **Boella, G., van der Torre, L. & Verhagen, H. (2008).** "Introduction to the special issue on normative multiagent systems." *JAAMAS* 17(1):1-10. — Survey of normative multi-agent systems. — Stack role: orientation.

---

## Reading order recommendation

**Week 1 (core):** Rahwan & Amgoud 2006 → Parsons/Sierra/Jennings 1998 → van Riemsdijk/Dastani/Meyer 2008 → Thangarajah/Padgham/Winikoff 2003.
**Week 2 (plans + impasse):** Sardina/de Silva/Padgham 2006 → Meneguzzi/Luck 2013 → Schut/Wooldridge/Parsons 2004.
**Week 3 (commitment + multi-agent):** Singh 1999 + 2008 → Broersen et al. 2002 (BOID) → Atkinson/Bench-Capon 2007.
**Week 4 (transduction + alignment):** Lin/Hilton/Evans 2022 → Guo et al. 2017 → Hadfield-Menell et al. 2016 (CIRL) → Soares et al. 2015 (corrigibility) → Omohundro 2008 (know thy enemy).
**Gap-fill later:** Jøsang 2016 for extended operators, Modgil/Prakken 2018 re-read for rule-ordering fix.

Each week ends by running the full research-papers-plugin pipeline on that week's papers and letting the extracted claims land in a propstore branch. Iterate until the architecture diagram has no hand-waves left.
