#!/usr/bin/env bash
# factory.sh — Build node for Client Systems Factory
# Usage: bash factory.sh [--site-json path/to/site.json] [--out dist/]
# Reads _factory control block from site.json to drive all decisions.
# build.sh still works for backward compatibility (it calls this script).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Argument parsing ────────────────────────────────────────────────────────
SITE_JSON="${SITE_JSON:-content/site.json}"
OUT_DIR="${OUT_DIR:-dist}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --site-json) SITE_JSON="$2"; shift 2 ;;
    --out)       OUT_DIR="$2";   shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ── Validate site.json exists and is v2 ────────────────────────────────────
if [[ ! -f "$SITE_JSON" ]]; then
  echo "ERROR: site.json not found at $SITE_JSON" >&2
  exit 1
fi

SCHEMA_VERSION=$(python3 -c "
import json, sys
d = json.load(open('$SITE_JSON'))
print(d.get('_factory', {}).get('schema_version', '1'))
")

if [[ "$SCHEMA_VERSION" != "2" ]]; then
  echo "ERROR: site.json must be schema_version 2. Got: $SCHEMA_VERSION" >&2
  echo "  Add a _factory block or run: python3 scripts/migrate_v1_to_v2.py $SITE_JSON" >&2
  exit 1
fi

echo "==> factory.sh — reading $SITE_JSON"

# ── Read factory flags ──────────────────────────────────────────────────────
FIRECRAWL_SOURCE=$(python3 -c "
import json; d=json.load(open('$SITE_JSON'))
print(d['_factory'].get('firecrawl_source',''))
")
ANIM_SCROLL=$(python3 -c "
import json; d=json.load(open('$SITE_JSON'))
print('1' if d['_factory']['animations']['scroll_timeline'] else '0')
")
ANIM_VIDEO=$(python3 -c "
import json; d=json.load(open('$SITE_JSON'))
print('1' if d['_factory']['animations']['video_scrub'] else '0')
")
VIDEO_SRC=$(python3 -c "
import json; d=json.load(open('$SITE_JSON'))
print(d['_factory']['animations'].get('video_src',''))
")
BASE_URL=$(python3 -c "
import json; d=json.load(open('$SITE_JSON'))
print(d['_factory']['seo']['base_url'])
")
SITE_NAME=$(python3 -c "
import json; d=json.load(open('$SITE_JSON'))
print(d['_factory']['seo']['site_name'])
")

# ── Step 0: Clean and recreate dist/ ───────────────────────────────────────
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# ── Step 1: Firecrawl brand extraction (if configured) ─────────────────────
BRAND_JSON=""
if [[ -n "$FIRECRAWL_SOURCE" ]]; then
  echo "==> Firecrawl extraction from $FIRECRAWL_SOURCE"
  bash scripts/firecrawl_extract.sh "$FIRECRAWL_SOURCE" "$OUT_DIR"
  BRAND_JSON="$OUT_DIR/brand.json"
  echo "    brand.json written"
fi

# ── Step 2: Determine extra script tags ────────────────────────────────────
EXTRA_SCRIPTS=""
if [[ "$ANIM_SCROLL" == "1" ]]; then
  EXTRA_SCRIPTS="$EXTRA_SCRIPTS\n  <script src=\"/js/scroll-timeline.js\" defer></script>"
fi
if [[ "$ANIM_VIDEO" == "1" && -n "$VIDEO_SRC" ]]; then
  EXTRA_SCRIPTS="$EXTRA_SCRIPTS\n  <script src=\"/js/video-scrub.js\" defer></script>"
fi

# ── Step 3: Assemble HTML pages ────────────────────────────────────────────
echo "==> Assembling pages..."
python3 scripts/render.py assemble \
  --site-json "$SITE_JSON" \
  --extra-scripts "$EXTRA_SCRIPTS" \
  --out "$OUT_DIR"

# ── Step 4: Copy static assets ─────────────────────────────────────────────
for dir in css js assets; do
  if [[ -d "$dir" ]]; then
    cp -r "$dir" "$OUT_DIR/"
  fi
done
[[ -d admin ]]    && cp -r admin    "$OUT_DIR/admin"
[[ -f robots.txt ]] && cp robots.txt "$OUT_DIR/robots.txt"

# Copy animation kit if enabled
if [[ "$ANIM_SCROLL" == "1" ]]; then
  cp js/scroll-timeline.js "$OUT_DIR/js/scroll-timeline.js"
fi
if [[ "$ANIM_VIDEO" == "1" ]]; then
  cp js/video-scrub.js "$OUT_DIR/js/video-scrub.js"
fi

# ── Step 5: Apply brand tokens to copied variables.css ─────────────────────
echo "==> Applying brand tokens to $OUT_DIR/css/variables.css"
python3 scripts/render.py apply-brand \
  --site-json "$SITE_JSON" \
  ${BRAND_JSON:+--brand-json "$BRAND_JSON"} \
  --src css/variables.css \
  --out "$OUT_DIR/css/variables.css"

# ── Step 6: Minify with esbuild ────────────────────────────────────────────
ESBUILD="node_modules/.bin/esbuild"
if [[ -f "$ESBUILD" ]]; then
  echo "==> Minifying..."
  find "$OUT_DIR/css" -name "*.css" -print0 | xargs -0 -I{} \
    "$ESBUILD" --bundle=false --minify --allow-overwrite "{}" --outfile="{}"
  find "$OUT_DIR/js" -name "*.js" -print0 | xargs -0 -I{} \
    "$ESBUILD" --bundle=false --minify --allow-overwrite "{}" --outfile="{}"
else
  echo "  (esbuild not installed — skip minification. Run: npm install)"
fi

# ── Step 7: Generate sitemap ───────────────────────────────────────────────
echo "==> Generating sitemap.xml..."
python3 scripts/render.py sitemap \
  --base-url "$BASE_URL" \
  --out-dir "$OUT_DIR"

echo "==> Build complete — $OUT_DIR/ is ready for Cloudflare Pages."
echo "    Site: $SITE_NAME ($BASE_URL)"
