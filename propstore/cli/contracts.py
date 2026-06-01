"""Contract manifest CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.output import emit, emit_success
from propstore.contracts import build_propstore_contract_manifest
from propstore.repository import Repository
