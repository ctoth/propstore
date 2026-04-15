"""Back-compat shim for assignment-level ``solve_ic_merge``.

The real module now lives at :mod:`propstore.world.ic_merge`. This shim
preserves the historical import path ``propstore.repo.ic_merge`` so
existing code (and the backward-compatible ``propstore.repo`` package
re-exports) keeps working.

The primary production entrypoint is ``solve_ic_merge(problem)``, which
solves one assignment-level merge problem over a declared concept domain
subject to an integrity constraint ``mu``. All public and the three
module-private helpers used by ``tests/test_ic_merge.py`` are re-exported
below so the shim is a drop-in replacement for the original module.
"""
from __future__ import annotations

from propstore.world.ic_merge import (  # noqa: F401
    ICMergeProblem,
    ICMergeResult,
    MergeOperator,
    _eval_cel_constraint_z3,
    assignment_satisfies_mu,
    claim_distance,
    enumerate_candidate_assignments,
    solve_ic_merge,
)

__all__ = [
    "ICMergeProblem",
    "ICMergeResult",
    "MergeOperator",
    "claim_distance",
    "solve_ic_merge",
]
