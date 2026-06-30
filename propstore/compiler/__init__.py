"""The propstore compiler — the AUTHORED -> CHECKED repository workflows.

This package owns ``pks build`` / ``pks validate`` orchestration: the shared
per-family semantic pipelines, the canonical :class:`CompilationContext`, and the
two terminal workflows that run them. Per PLAN.md §12.6, build and validate share
ONE pass framework and ONE check set, differing only in terminal sink — build
materialises the sidecar, validate does not.

It is the layer *above* the families: ``compiler`` imports from
``propstore.families`` and the substrate packages; nothing in those layers
depends on a compiler workflow. CLI adapters present these reports (Phase 10);
they do not decide which passes run.
"""
