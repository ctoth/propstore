#!/usr/bin/env sh
set -eu

label="pytest"
if [ "${1:-}" = "--label" ] || [ "${1:-}" = "-Label" ]; then
    label="$2"
    shift 2
fi

exec uv run python scripts/run_logged_pytest.py --label "$label" -- "$@"
