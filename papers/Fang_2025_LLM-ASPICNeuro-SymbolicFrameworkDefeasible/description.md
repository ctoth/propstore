---
tags: [aspic-plus, neuro-symbolic, defeasible-reasoning, llm-integration, argumentation]
---
Presents LLM-ASPIC+, a neuro-symbolic framework that uses LLMs for knowledge extraction and belief formation from natural language, then feeds contradiction pairs into an ASPIC+ solver for formal defeasible reasoning and conflict resolution via grounded extensions. Achieves 67.1% accuracy on BoardGameQA, significantly outperforming pure LLM approaches (CoT: 51.3%). Directly relevant to propstore's architecture: validates the pattern of LLM extraction front-end with ASPIC+ resolution back-end, and provides a concrete error taxonomy for LLM-based knowledge extraction failures.
