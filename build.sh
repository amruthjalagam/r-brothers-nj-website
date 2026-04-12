#!/usr/bin/env bash
# build.sh — backward-compatible wrapper. Delegates to factory.sh.
# For direct factory control, use factory.sh --site-json --out flags.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/factory.sh" "$@"
