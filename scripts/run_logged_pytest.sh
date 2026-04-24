#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
repo_root=$(dirname "$script_dir")
venv_python="$repo_root/.venv/bin/python"
if [ ! -x "$venv_python" ] && [ -x "$repo_root/.venv/Scripts/python.exe" ]; then
    venv_python="$repo_root/.venv/Scripts/python.exe"
fi
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
    if [ ! -x "$venv_python" ]; then
        echo "Expected synced virtualenv at '$repo_root/.venv/bin/python' (or Windows '.venv/Scripts/python.exe'). Run 'uv sync --dev --locked --no-sources' first." >&2
        exit 1
    fi
    PROPSTORE_UV_NO_SOURCES=1 exec "$venv_python" "$script_dir/run_logged_pytest.py" --label "$label" -- "$@"
fi

exec uv run python "$script_dir/run_logged_pytest.py" --label "$label" -- "$@"
