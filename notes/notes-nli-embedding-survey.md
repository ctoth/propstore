# NLI, Embedding, and Confidence/Probability Survey

Survey date: 2026-03-24

## 1. NLI (Natural Language Inference) -- Stance Classification

### Primary Module: `propstore/relate.py`

This is the only NLI module. It uses LLM-based classification (via litellm), not a dedicated NLI model. The module classifies epistemic relationships between claims using two-pass prompting.

**Stance types** (defined at `propstore/stances.py:5-7`):
`rebuts`, `undercuts`, `undermines`, `supports`, `explains`, `supersedes`, `none`

**Classification prompt** (`relate.py:29-49`): Asks an LLM to return JSON with `type`, `strength`, `note`, `conditions_differ`. Strength is a categorical string: `"strong"`, `"moderate"`, or `"weak"`.

**Two-pass architecture** (`relate.py:52-73`): When first pass returns `"none"` but embedding distance is below `second_pass_threshold` (default 0.75, see `relate.py:239`), a second pass re-prompts with the embedding distance value and shared concept info baked into the prompt.

**Confidence mapping** (`relate.py:76-83`):
```python
_CONFIDENCE_MAP: dict[tuple[int, str], float] = {
    (1, "strong"): 0.95, (1, "moderate"): 0.80, (1, "weak"): 0.60,
    (2, "strong"): 0.70, (2, "moderate"): 0.50, (2, "weak"): 0.30,
}
```
- Representation: bare `float` in range [0.0, 1.0]
- Pass number (1 or 2) x strength category -> float
- Default fallback is 0.5 (`relate.py:83`)
- "none" verdicts get confidence 0.0 (`relate.py:200-201`)

**Output structure** (`relate.py:202-219`): Each stance result is a `dict` with:
- `target`: claim ID
- `type`: stance type string
- `strength`: categorical string
- `note`: freetext
- `conditions_differ`: freetext or None
- `resolution`: nested dict with `method`, `model`, `embedding_model`, `embedding_distance`, `pass_number`, `confidence`

**File output** (`relate.py:464-485`): Written to `knowledge/stances/<claim_id>.yaml` via `write_stance_file`.


## 2. Embedding Similarity

### Primary Module: `propstore/embed.py`

**Embedding generation** (`embed.py:159-260`): Uses `litellm.embedding()` to get vectors. Stores as float32 blobs in sqlite-vec virtual tables. Supports claims and concepts as separate entity types.

**Distance metric**: sqlite-vec's built-in distance (cosine distance by default). The `find_similar` query (`embed.py:341-348`) uses `v.embedding MATCH ? AND k = ?` with `ORDER BY v.distance`. The distance value is a bare `float` returned as `v.distance` in result dicts.

**Representation**: The distance is a bare `float` carried in result dicts under key `"distance"`. No wrapper type, no explicit semantics annotation. Lower = more similar.

**Multi-model consensus** (`embed.py:372-446`):
- `find_similar_agree`: intersection of top-k across ALL stored models
- `find_similar_disagree`: entities in top-k of some models but not others
- These operate on set membership, not distance values

**Downstream consumption of distance**:
1. `relate.py:265` -- distance stored as `candidate_distances[c["id"]] = c.get("distance", 1.0)`
2. `relate.py:284-285` -- compared against `second_pass_threshold` to trigger second NLI pass
3. `relate.py:52` -- distance value interpolated directly into second-pass LLM prompt string: `"HIGHLY SIMILAR by embedding distance ({distance:.4f})"`
4. Stored into stance YAML files as `resolution.embedding_distance`


## 3. Probability/Confidence Floats in the System

### 3a. NLI Confidence (`relate.py:76-83`)
- Bare float [0.0, 1.0]
- Computed from (pass_number, strength_category) lookup table
- Stored in stance YAML files and loaded into `claim_stance.confidence` column

### 3b. Embedding Distance (`embed.py:341`)
- Bare float, range depends on sqlite-vec distance metric
- Used as-is for threshold comparison and prompt interpolation
- Stored in `claim_stance.embedding_distance` column

### 3c. Claim Strength (`propstore/preference.py:56-87`)
- Bare float, unbounded (not [0,1])
- Computed from claim metadata: `log1p(sample_size)`, `1/uncertainty`, `confidence`
- Average of available components; missing data is neutral (returns 1.0)
- The `confidence` component here (`preference.py:79`) reads from claim dict, which could be the NLI confidence or any other confidence field on the claim

### 3d. Algorithm AST Similarity (`propstore/conflict_detector/algorithms.py:56`)
- Bare float from `ast_equiv.compare()` result: `result.similarity`
- Stored only in `derivation_chain` string: `f"similarity:{result.similarity:.3f} tier:{result.tier}"`
- Not consumed numerically downstream -- purely diagnostic string

### 3e. MaxSAT Weights (`propstore/maxsat_resolver.py:38-39`)
- `claim_strength` floats passed as z3.Optimize soft constraint weights
- `optimizer.add_soft(keep_vars[cid], weight=str(strength))` -- converted to string for z3


## 4. Flow into Argumentation Layer

### 4a. claim_stance Table (Storage)
Schema at `build_sidecar.py:826-841`:
```sql
CREATE TABLE claim_stance (
    claim_id TEXT NOT NULL,
    target_claim_id TEXT NOT NULL,
    stance_type TEXT NOT NULL,
    strength TEXT,              -- categorical: "strong"/"moderate"/"weak"
    conditions_differ TEXT,
    note TEXT,
    resolution_method TEXT,     -- "nli_first_pass" or "nli_second_pass"
    resolution_model TEXT,
    embedding_model TEXT,
    embedding_distance REAL,    -- bare float from sqlite-vec
    pass_number INTEGER,        -- 1 or 2
    confidence REAL,            -- bare float [0.0, 1.0] from _CONFIDENCE_MAP
    ...
)
```

### 4b. Confidence Threshold Gate (`argumentation.py:106-107, 131-133`)
`build_argumentation_framework` takes `confidence_threshold: float = 0.5`. Stances with `confidence < confidence_threshold` are skipped entirely (`argumentation.py:133`). This is the primary point where the NLI confidence float enters the argumentation layer.

Same pattern in `structured_argument.py:60-61, 147-148`.

### 4c. Claim Strength -> Preference Ordering (`argumentation.py:156-161`)
For `rebuts`/`undermines` stances, `claim_strength()` is called on both attacker and target. These floats are passed to `defeat_holds()` -> `strictly_weaker()` (`preference.py:16-34`).

- Elitist comparison: EXISTS x in set_a s.t. FORALL y in set_b, x < y
- Democratic comparison: FORALL x in set_a EXISTS y in set_b, x < y
- Currently always single-element lists: `[claim_strength(claim)]`

The defeat decision: undercuts/supersedes always succeed. Rebuts/undermines succeed iff attacker is NOT strictly weaker than target (`preference.py:48-53`).

### 4d. Stance Type -> Attack Classification (`argumentation.py:22-26`)
```python
_ATTACK_TYPES = frozenset({"rebuts", "undercuts", "undermines", "supersedes"})
_UNCONDITIONAL_TYPES = frozenset({"undercuts", "supersedes"})
_PREFERENCE_TYPES = frozenset({"rebuts", "undermines"})
_SUPPORT_TYPES = frozenset({"supports", "explains"})
```
These directly map NLI output types to argumentation roles.

### 4e. Support -> Cayrol Derived Defeats (`argumentation.py:46-98`)
Support relations (`supports`, `explains`) feed into bipolar AF construction (Cayrol 2005). Transitive support chains create derived defeats:
- Supported defeat: A supports* B, B defeats C -> (A,C) is a defeat
- Indirect defeat: A defeats B, B supports* C -> (A,C) is a defeat

### 4f. Resolution Strategy Dispatch (`world/resolution.py:210-342`)
The full pipeline: `resolve()` dispatches to one of:
- `RECENCY` -- uses provenance dates, no floats from NLI/embedding
- `SAMPLE_SIZE` -- uses claim metadata, no floats from NLI/embedding
- `ARGUMENTATION` with backend:
  - `CLAIM_GRAPH` -> `argumentation.build_argumentation_framework` -> `dung.grounded_extension`
  - `STRUCTURED_PROJECTION` -> `structured_argument.build_structured_projection` -> same Dung machinery
  - `ATMS` -> ATMS engine label propagation (separate path)

### 4g. RenderPolicy Defaults (`world/types.py:181-196`)
```python
class RenderPolicy:
    reasoning_backend: ReasoningBackend = ReasoningBackend.CLAIM_GRAPH
    strategy: ResolutionStrategy | None = None
    semantics: str = "grounded"
    comparison: str = "elitist"
    confidence_threshold: float = 0.5
```


## 5. Key Observations

### 5a. No dedicated NLI model -- LLM prompt-based classification
The system uses general-purpose LLMs via litellm, not specialized NLI models (like cross-encoders or MNLI-trained models). The "NLI" label is aspirational -- it is really LLM stance classification.

### 5b. Confidence is a hardcoded lookup table, not model-derived
The confidence float does not come from the LLM's output or calibrated probabilities. It is a fixed mapping from (pass_number, strength_category) to a float. The LLM's actual confidence in its classification is not captured. See `relate.py:76-83`.

### 5c. Embedding distance used raw in LLM prompt
At `relate.py:52`, the raw embedding distance float is interpolated into the second-pass prompt. The LLM sees "HIGHLY SIMILAR by embedding distance (0.3421)" -- the meaning of this number depends on the embedding model and distance metric, but no normalization or interpretation is provided to the LLM.

### 5d. strength (categorical) vs confidence (float) vs claim_strength (float) -- three different things
- `strength`: LLM output, categorical string ("strong"/"moderate"/"weak"), stored in claim_stance.strength
- `confidence`: derived float [0,1] from lookup table, stored in claim_stance.confidence, used as threshold gate
- `claim_strength`: computed float from claim metadata (sample_size, uncertainty, confidence), used for preference ordering

The `confidence` field on a claim dict (used by `preference.py:79`) could be the NLI-derived confidence or any other float on the claim -- there is no type distinction.

### 5e. Single-element strength lists
`argumentation.py:158-159` always creates single-element lists `[claim_strength(claim)]` for the preference comparison. The `strictly_weaker` function supports set comparison (Modgil & Prakken Def 19), but the current projection never produces multi-element strength sets. This is noted in `argumentation.py:1-7` -- the module self-documents that it is a "claim-graph backend inspired by Dung and ASPIC+ ideas", not full ASPIC+.

### 5f. Embedding distance default is 1.0 when missing
At `relate.py:265`: `candidate_distances[c["id"]] = c.get("distance", 1.0)`. This means if distance is missing, the claim will NOT trigger second-pass NLI (since 1.0 > 0.75 threshold). This is a safe default.

### 5g. MaxSAT path is independent of NLI/embedding
`argumentation.py:249-302` (`compute_consistent_beliefs`) uses `conflict_detector` + `maxsat_resolver`, which operate on structural conflicts (same concept, incompatible values), not on NLI stances. Claim strengths are used as z3 soft constraint weights.


## 6. Complete Data Flow Diagram

```
[litellm embedding API]
    |
    v
embed.py: vectors stored in sqlite-vec
    |
    v
embed.py:find_similar -> list[dict] with "distance" float
    |
    v
relate.py: for each similar pair, LLM classifies stance
    |  (pass 1: all pairs)
    |  (pass 2: "none" verdicts with distance < 0.75)
    |
    v
relate.py:_CONFIDENCE_MAP -> float confidence from (pass, strength)
    |
    v
write_stance_file -> knowledge/stances/*.yaml
    |
    v
build_sidecar.py -> claim_stance table (confidence REAL, embedding_distance REAL)
    |
    v
argumentation.py:build_argumentation_framework
    |  - gate: confidence >= threshold (default 0.5)
    |  - classify: stance_type -> attack or support
    |  - preference: claim_strength() -> defeat_holds()
    |  - Cayrol derived defeats from support chains
    |
    v
dung.py: AF = (Args, Defeats) -> grounded/preferred/stable extensions
    |
    v
world/resolution.py:resolve -> ResolvedResult (winner or conflicted)
```
