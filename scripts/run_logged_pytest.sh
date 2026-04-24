#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
repo_root=$(dirname "$script_dir")
label="pytest"
uv_no_sources="false"
while [ "$#" -gt 0 ]; do
    case "$1" in
        --label|-Label)
            label="$2"
            shift 2
            ;;
        --no-sources|-NoSources)
            uv_no_sources="true"
            shift
            ;;
        *)
            break
            ;;
    esac
done

if [ "$uv_no_sources" = "true" ]; then
    if [ ! -x "$repo_root/.venv/bin/python" ]; then
        echo "Expected synced virtualenv at '$repo_root/.venv/bin/python'. Run 'uv sync --dev --locked --no-sources' first." >&2
        exit 1
    fi
    PROPSTORE_UV_NO_SOURCES=1 exec "$repo_root/.venv/bin/python" "$script_dir/run_logged_pytest.py" --label "$label" -- "$@"
fi

exec uv run python "$script_dir/run_logged_pytest.py" --label "$label" -- "$@"
