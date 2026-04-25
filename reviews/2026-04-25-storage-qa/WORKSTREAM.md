# Storage QA Workstream

Date: 2026-04-25
Status: ACTIVE - SQA-1 COMPLETE
Depends on: none
Blocks: none
Review context: measured Quire/Dulwich read-path behavior against propstore usage patterns on 2026-04-25.

## What triggered this

Recent measurement work on `quire` showed that propstore read-heavy workflows
are sensitive to Git object layout, not YAML parsing complexity.

I read the relevant propstore entrypoints before writing this workstream:

- `propstore/cli/compiler_cmds.py`
- `propstore/app/compiler.py`
- `propstore/compiler/workflows.py`
- `propstore/repository.py`
- `propstore/source/finalize.py`
- `propstore/source/promote.py`
- `propstore/app/project_init.py`

The important architectural fact is simple:

- `pks build` is a read-only Git consumer plus sidecar SQLite rebuild.
- `pks build` is **not** the bulk Git-write step.
- Bulk Git writes happen in source finalize, source promote, and initial
  repository seeding.

So "pack after `pks build`" is the wrong intervention point. If we want packed
repos for fast reads, the packing hook belongs after bulk authored-artifact
write phases, not after sidecar rebuild.

## Verified facts

These numbers were measured on 2026-04-25 with dedicated benchmark scripts in
`quire`, not inferred from memory.

### Raw filesystem floor

- Plain filesystem `read_bytes()` of `5000` unique YAML docs:
  `0.4170s`, about `0.0834 ms/doc`
- Plain filesystem `read_bytes() + msgspec.yaml.decode(...)` of `5000` unique
  docs: `0.6256s`, about `0.1251 ms/doc`
- Decode from memory for `5000` unique docs:
  `0.0764s`, about `0.0153 ms/doc`

Conclusion: YAML decode is cheap on these docs. It is not the dominant problem.

### Git layout impact

- Loose Git unique point loads, `5000` docs:
  `1.1432s` median, about `0.2286 ms/doc`
- Packed Git unique point loads, `5000` docs:
  `0.6706s` median, about `0.1341 ms/doc`

Packed Git gets close to the raw filesystem + decode floor. Loose Git is
materially worse, especially on cold first pass.

### Packed-repo speedups

- Repeated point loads: `1.36x`
- Unique point loads: `1.70x`
- `iter_handles()` family scan: `1.82x`
- Pinned `iter()+require()` family scan: `1.83x`

Conclusion: packing helps enough to be worth operationalizing for hot-read
repos.

### What is slow inside Dulwich

The hot loose-object path is dominated by:

- repeated `_io.open`
- `dulwich.objects.ShaFile.from_path(...)`
- `DiskObjectStore._get_loose_object(...)`

What is **not** dominant:

- YAML decode
- Dulwich Rust tree parsing on this workload

Packed-object caches exist inside Dulwich. Equivalent loose-object caches do not
appear to.

## Target discipline

Propstore should treat packed Git state as the normal read-optimized condition
after bulk authored-artifact writes.

Propstore should not:

- pack after `pks build`;
- try to solve loose-object slowness by sidecar-only changes;
- spend time tuning YAML codecs before storage layout and access pattern issues
  are addressed.

Propstore should:

- pin read snapshots once per workflow;
- use iterator-first loaded-artifact scans where Quire already supports them;
- pack after large Git mutation phases that create many loose objects;
- measure the effect in propstore workflows, not just in microbenchmarks.

## Phase structure

### Phase SQA-1 - Read-path callsite audit

- Audit propstore loops that still do `iter() -> require()` or
  `iter() -> require_handle()` on whole families.
- Replace obvious full-family scan callsites with:
  - `iter_handles(...)` when the family/placement supports it, or
  - pinned snapshot usage when point loads are still required.
- Priority surfaces:
  - `propstore/compiler/workflows.py`
  - `propstore/app/claims.py`
  - `propstore/app/contexts.py`
  - `propstore/app/forms.py`
  - `propstore/app/concepts/mutation.py`

Exit criteria:

- Full-family scan callsites in compiler/build paths stop re-resolving branch
  head and stop using avoidable point-read loops.

Execution status: COMPLETE on 2026-04-25.

Audit result:

- Replaced whole-family `iter() -> require()` and
  `iter() -> require_handle()` scans with existing Quire `iter_handles()`
  across compiler, sidecar, grounding, app workflow, source registry, merge,
  artifact-code, and consistency paths.
- Left fixed source-branch side-file loads as point reads. Those families use
  fixed-file placements and are not enumerable through Quire's family scan API.
- Left three `compiler.build_repository` schema-diagnostic loops as
  `iter() -> require_handle()` because current Quire `iter_handles()` cannot
  continue after a decode failure while preserving one diagnostic per bad ref.
- Left ref-only enumeration as `iter()` where the code only needs names or
  existence checks.

Files updated:

- `propstore/artifact_codes.py`
- `propstore/app/claims.py`
- `propstore/app/concepts/display.py`
- `propstore/app/concepts/mutation.py`
- `propstore/app/contexts.py`
- `propstore/app/forms.py`
- `propstore/app/micropubs.py`
- `propstore/app/predicates.py`
- `propstore/app/rules.py`
- `propstore/claim_references.py`
- `propstore/compiler/context.py`
- `propstore/compiler/workflows.py`
- `propstore/concept_ids.py`
- `propstore/core/aliases.py`
- `propstore/grounding/loading.py`
- `propstore/merge/merge_classifier.py`
- `propstore/merge/structured_merge.py`
- `propstore/sidecar/build.py`
- `propstore/source/registry.py`
- `propstore/world/consistency.py`

### Phase SQA-2 - Bulk-write packing policy

- Add a post-write packing hook only for bulk Git mutation workflows.
- First candidates:
  - `propstore/source/finalize.py`
  - `propstore/source/promote.py`
  - `propstore/app/project_init.py`
- Keep the hook explicit and local to the workflow. Do not hide it behind
  generic per-commit mutation plumbing.
- Measure wall-clock impact of the packing step itself so we know whether the
  read win justifies the write-side cost.

Exit criteria:

- At least one real bulk-write path packs after commit.
- The packing cost and the downstream read win are both measured and recorded.

### Phase SQA-3 - Propstore benchmark harness

- Add a propstore-owned benchmark or reproducible script that exercises:
  - full build read path from a pinned snapshot,
  - concept scan path,
  - claim scan path,
  - source promotion or finalize followed by readback.
- Record loose vs packed numbers on the same machine and repo shape.
- Keep the benchmark focused on propstore workflows rather than generic Quire
  microbenchmarks.

Exit criteria:

- Propstore can reproduce the storage findings without depending on ad hoc
  external notes.

### Phase SQA-4 - Optional upstream path

- Evaluate whether a Dulwich loose-object cache is worth upstream work.
- Only pursue this if packed-repo policy plus propstore callsite cleanup still
  leaves unacceptable loose-repo latency in real workflows.
- Treat this as optional because packed repos already approach the raw
  filesystem floor on the measured workload.

Exit criteria:

- Either:
  - a concrete upstream Dulwich design note exists, or
  - the team explicitly records that packed-repo policy is sufficient.

## What not to do

- Do not add "pack after `pks build`". `pks build` is not the Git write phase.
- Do not build a compatibility wrapper around old scan APIs. Update callers to
  the direct iterator-first path.
- Do not optimize YAML first.
- Do not assume a sidecar rebuild will fix authored-artifact read costs.

## Exit criteria

- Propstore has at least one measured packed-after-bulk-write path.
- Compiler/build read paths use pinned or loaded-artifact iteration where
  applicable.
- A propstore-local benchmark reproduces loose vs packed behavior.
- The repo has a documented operational rule for when packing happens and when
  it does not.

## Short verdict

The problem is real, but the shape is now clear:

- `pks build` is the wrong hook.
- Loose Git is the bad case.
- Packed Git is close to the raw filesystem floor.
- YAML is not the bottleneck.
- The next practical moves are propstore callsite cleanup plus post-bulk-write
  packing, validated by propstore-owned benchmarks.
