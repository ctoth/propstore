# Scout Notes: Uncertainty Design Proposal Synthesis

## GOAL
Synthesize research findings from code survey + 7 paper notes into a concrete design proposal for replacing bare float probability/confidence representation.

## DONE
- Read gauntlet protocol (scout role: survey and report, do NOT implement)
- Read code survey (notes-nli-embedding-survey.md) - 5 critical findings identified
- Read initial research (notes-probability-representation-research.md)
- Read all 7 paper notes: Guo 2017, Josang 2001, Sensoy 2018, Hunter 2017, Li 2011, Denoeux 2018, Fang 2025
- Verified key code locations: relate.py:76-83, argumentation.py:101-139, preference.py:56-87

## KEY OBSERVATIONS

### 5 Problems from Code Survey
1. Confidence is hardcoded lookup table (relate.py:76-83) - not model-derived
2. Embedding distance used raw in LLM prompt (relate.py:52) - no normalization
3. Three conflated concepts: strength(categorical), confidence(float), claim_strength(float)
4. Confidence threshold gate at argumentation.py:133 - binary gate on continuous value, violates non-commitment
5. Single-element strength lists (argumentation.py:158-159) - preference machinery underused

### Literature Synthesis
- Josang 2001: Opinion tuples (b,d,u,a) with Beta distribution bijection - THE core replacement
- Sensoy 2018: Dirichlet/evidence parameterization - how to get opinions from model outputs
- Guo 2017: Temperature scaling - raw scores are miscalibrated, need post-hoc fix
- Hunter 2017: Epistemic probability on AFs with COH/RAT/FOU constraints
- Li 2011: PrAF constellations approach - probabilities on argument/defeat existence
- Denoeux 2018: Decision rules for belief functions at render time (pignistic, E-admissibility)
- Fang 2025: LLM-ASPIC+ pipeline - validates neuro-symbolic architecture but uses binary beliefs

### Design Direction
- Store Beta(alpha, beta) as canonical representation
- Derive opinions, DS intervals, credal intervals at render time
- Calibrate raw scores before mapping to Beta params
- Replace confidence threshold gate with PrAF existence probabilities
- Use Denoeux decision criteria as render-time policies

## NEXT
Write the design proposal to notes-uncertainty-design-proposal.md
