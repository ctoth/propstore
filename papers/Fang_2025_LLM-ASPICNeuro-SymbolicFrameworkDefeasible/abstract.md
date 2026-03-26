# Abstract

## Original Text (Verbatim)

Large language models (LLMs) excel at complex reasoning and achieve human-like performance in many natural language processing tasks. However, they still struggle to reason effectively when faced with inconsistent or contradictory information. This is particularly challenging in defeasible reasoning scenarios, where reliable decision-making depends on reconciling conflicting evidence, such as legal analysis, medical diagnosis, and common sense reasoning. In this paper, we focus on defeasible reasoning in natural language, a task that challenges LLMs to handle and resolve conflicting information. To enhance the defeasible reasoning capability of LLMs, we propose LLM-ASPIC+, a framework combining neural and formal argumentation-based formal reasoning. Our framework harnesses LLMs' capacity for grounding and contextual reasoning while integrating formal argumentation frameworks to establish systematic conflict resolution mechanisms lacking in LLMs. We also create MineQA, a newly synthesized dataset designed to evaluate the performance of LLMs in defeasible reasoning at controllable scales. LLM-ASPIC+ achieves state of the art results on multi-step defeasible reasoning, with 67.1% accuracy on BoardGameQA, and 63.0% on RuletakerQA-D. These results show that integrating neural language models with formal argumentation effectively supports defeasible reasoning in natural language.

---

## Our Interpretation

This paper addresses the fundamental problem that LLMs cannot handle contradictory information during reasoning — they lack a retraction mechanism and struggle to determine when new evidence should override prior conclusions. The key contribution is a clean architectural split: LLMs handle all natural language understanding and belief formation, while ASPIC+ handles all conflict resolution through formal argumentation with grounded extensions. This is directly relevant to propstore because it validates our needed architecture of LLM extraction front-end feeding into ASPIC+ resolution back-end, replacing our current bare-float NLI approach with structured argumentation.
