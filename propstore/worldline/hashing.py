from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

import rfc8785
from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineDependencies,
    WorldlineSensitivityReport,
    WorldlineStep,
    WorldlineTargetValue,
)
from propstore.worldline.revision_types import WorldlineRevisionState
