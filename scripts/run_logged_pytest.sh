#!/usr/bin/env sh
set -eu

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
    PROPSTORE_UV_NO_SOURCES=1 exec uv run --locked --no-sources python scripts/run_logged_pytest.py --label "$label" -- "$@"
fi

exec uv run python scripts/run_logged_pytest.py --label "$label" -- "$@"
