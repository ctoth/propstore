# WS-O-arg-vaf-completion: Bench-Capon line-of-argument and fact-uncertainty completion

**Status**: OPEN
**Depends on**: WS-O-arg-vaf-ranking
**Blocks**: none currently
**Owner**: future argumentation-package implementation owner + human reviewer
**Authoritative**: Bench-Capon 2003 pp. 438-447, reread from page images on 2026-04-28

## Why this workstream exists

WS-O-arg-vaf-ranking closed the core Bench-Capon VAF/AVAF kernel: value annotations, audience-specific defeat, preferred extensions, objective acceptance, and subjective acceptance.

The post-compaction image reread found additional Bench-Capon surfaces that are paper-significant but were not part of that workstream:

- Argument chains, Definition 6.3, p. 438.
- Unique preferred extension for AVAFs with no single-valued cycles, Theorem 6.4, p. 438.
- Lines of argument, Definition 6.5, p. 439.
- Parity classification of objective/subjective/indefensible status in one-attacker/no-single-valued-cycle VAFs, Theorem 6.6, pp. 440-441.
- Two-value cycle preferred-extension corollary, Corollary 6.7, pp. 440-441.
- Practical shortcuts for two-valued disputes and repeated-value termination, pp. 441-442.
- Fact-as-highest-value treatment for factual arguments, p. 444.
- Uncertain factual disputes yielding multiple preferred extensions even under value orderings, pp. 445-447.

Those surfaces are not optional if we later claim full Bench-Capon practical persuasion support. They should be implemented deliberately, with tests proving the paper claims before production code.

## Scope

This work lands in `../argumentation` first, then propstore pins the pushed upstream commit. Do not implement this inside propstore.

In scope:

- Typed argument-chain representation over an existing `ValueBasedArgumentationFramework`.
- Typed line-of-argument representation for a target argument.
- A paper-faithful status classifier for the pp. 438-441 no-single-valued-cycle / at-most-one-attacker conditions.
- A two-value cycle helper that proves Corollary 6.7 behavior.
- Explicit fact-as-highest-value modeling for Bench-Capon's Hal/Carla factual-argument examples.
- A propstore pin sentinel proving the new upstream surface under the final pushed dependency.

Out of scope:

- Dialogue protocol modeling from Bench-Capon and Dunne 2001.
- General persuasion strategy synthesis.
- Replacing the existing exhaustive preferred-extension kernel.
- Oikarinen strong/local equivalence kernels; those are a separate gap.

## TDD plan

### Step 0 - Paper example inventory

Create an upstream note that enumerates Bench-Capon pp. 438-447 examples and theorem obligations using actual paper page numbers. Do not use PDF text extraction.

### Step 1 - Argument chains

Write failing tests for Definition 6.3, p. 438:

- All arguments in a chain share one value.
- The first chain argument has no attacker inside the chain.
- Every later chain argument has exactly one sole chain attacker: the previous argument.
- Odd/even parity follows the paper's accepted/defeated alternation under same-value successful attacks.

Implement the minimal typed chain checker and parity helper.

### Step 2 - Lines of argument

Write failing tests for Definition 6.5, p. 439:

- A line comprises chains with distinct values.
- The target argument is the last argument of the first chain.
- Each next chain's last argument attacks the first argument of the previous chain.
- Each next chain starts with a value not already present in the line.
- Repeated values terminate the line rather than creating infinite expansion.

Implement typed line construction without changing existing VAF preferred-extension behavior.

### Step 3 - Theorem 6.6 classifier

Write failing tests from pp. 439-440:

- Objective iff the target is odd-numbered in `C1` and there is no subsequent odd chain.
- Indefensible iff the target is even-numbered in `C1` and there is no subsequent odd chain.
- Subjective iff the line contains an odd chain `Cn` for `n > 1`.

Implement the classifier and hard-fail outside the theorem's stated preconditions.

### Step 4 - Corollary 6.7 two-value cycles

Write failing tests for pp. 440-441:

- Preferred extension includes odd-numbered arguments of all chains preceded by an even chain.
- Preferred extension includes odd-numbered arguments of chains with the preferred value.
- Preferred extension includes even-numbered arguments of all other chains.

Use generated small two-value cycles to assert the helper agrees with ordinary audience-specific preferred extensions.

### Step 5 - Fact as highest value

Write failing tests for pp. 444-447:

- Facts are modeled as a special value that outranks every ordinary value for every reasonable audience.
- Figure 7 blocks the life/property value dispute from defeating the factual argument when the fact is accepted.
- Figure 8 admits multiple preferred extensions under factual uncertainty even with a fixed value ordering.
- Objective persuasion under uncertainty requires the argument in every preferred extension for every value ordering, as stated on p. 447.

Implement an explicit fact-value helper. Do not silently rewrite ordinary values into facts.

### Step 6 - Property gates

Add Hypothesis tests:

- Generated valid chains satisfy same-value parity.
- Generated valid lines terminate when a value repeats.
- Generated two-value cycles match Corollary 6.7 and the existing preferred-extension engine.
- Generated fact values always outrank ordinary values under reasonable audiences.

### Step 7 - Propstore pin and sentinel

Push the upstream argumentation commit. Then update propstore's `formal-argumentation` git pin to that pushed commit and add `tests/architecture/test_argumentation_pin_vaf_completion.py`.

The propstore sentinel must prove at least one line-of-argument classification, one Corollary 6.7 two-value cycle case, and one fact-as-highest-value uncertainty case.

### Step 8 - Close gaps and gate

Update `docs/gaps.md`, `cluster-P-argumentation-pkg.md`, this workstream, and `INDEX.md`.

## Acceptance gates

- [ ] Upstream focused tests for VAF completion pass.
- [ ] Upstream Hypothesis property gates pass.
- [ ] `cd ../argumentation && uv run pyright src/argumentation` passes with `0 errors`.
- [ ] `cd ../argumentation` full suite has no new failures.
- [ ] Propstore pin references a pushed upstream commit, not a local path.
- [ ] Propstore sentinel `tests/architecture/test_argumentation_pin_vaf_completion.py` passes through the logged pytest wrapper.
- [ ] `uv run pyright propstore` passes with `0 errors`.
- [ ] Propstore full suite passes through the logged pytest wrapper.
- [ ] `docs/gaps.md` closes the Bench-Capon pp. 438-447 residual gap.
- [ ] This workstream status is `CLOSED <propstore-sha>`.

## Done means done

- Bench-Capon pp. 438-447 are implemented as a named, typed public surface in `argumentation`.
- Tests cite actual paper page numbers, not PNG artifact indexes.
- The implementation hard-fails outside theorem preconditions rather than returning speculative classifications.
- Existing VAF/AVAF defeat and acceptance behavior remains unchanged.
- Propstore observes the behavior only through the pushed dependency pin and sentinel tests.
