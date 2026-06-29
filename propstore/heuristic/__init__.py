"""Heuristic analysis layer.

Heuristic surfaces (calibration, similarity, stance classification) bridge raw
model outputs to the formal opinion algebra. Their output is graded evidence, not
truth: a calibrated probability becomes a ``doxa.Opinion`` whose typed provenance
is carried beside it, and absence of evidence becomes a vacuous opinion rather
than a fabricated number (CLAUDE.md honest-ignorance discipline).
"""

from __future__ import annotations
