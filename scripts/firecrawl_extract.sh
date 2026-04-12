#!/usr/bin/env bash
# firecrawl_extract.sh — Extract brand tokens from a client's existing website.
# Usage: bash firecrawl_extract.sh <url> <output_dir>
# Output: <output_dir>/brand.json
# Requires: FIRECRAWL_API_KEY in ~/MyVault/.env or env
# Firecrawl free tier: 500 credits (~70 full-page extractions). Hobby: $16/mo.

set -euo pipefail

URL="${1:?Usage: $0 <url> <output_dir>}"
OUTPUT_DIR="${2:?Usage: $0 <url> <output_dir>}"

# Load API key
ENV_FILE="$HOME/MyVault/.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$ENV_FILE"
fi

if [[ -z "${FIRECRAWL_API_KEY:-}" ]]; then
  echo "ERROR: FIRECRAWL_API_KEY not set. Add to ~/MyVault/.env" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

python3 "$(dirname "$0")/firecrawl_extract.py" "$URL" "$OUTPUT_DIR/brand.json"
