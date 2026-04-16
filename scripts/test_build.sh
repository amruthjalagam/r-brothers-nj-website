#!/usr/bin/env bash
# test_build.sh — Build Smoke Test (corresponds to check node 4✓ in spec)
# Usage: bash test_build.sh [site_json_path]
# Exit 0 = all checks pass. Exit 1 = at least one check failed.

set -euo pipefail

SITE_JSON="${1:-content/site.json}"
OUT_DIR="/tmp/factory-build-test-$$"
FAILS=0

check() {
  local label="$1"
  local result="$2"
  if [[ "$result" == "pass" ]]; then
    echo "  PASS  $label"
  else
    echo "  FAIL  $label — $result"
    FAILS=$((FAILS + 1))
  fi
}

echo "==> Build Smoke Test (4✓)"
echo "    site.json: $SITE_JSON"
echo "    out:       $OUT_DIR"

# Run factory
bash factory.sh --site-json "$SITE_JSON" --out "$OUT_DIR" 2>&1

# ── Check 1: All pages listed in site.json were built ────────────────
PAGES=$(python3 -c "
import json
d = json.load(open('$SITE_JSON'))
print(' '.join(d['_factory']['pages']))
")
for page in $PAGES; do
  if [[ -f "$OUT_DIR/${page}.html" ]]; then
    check "page built: ${page}.html" "pass"
  else
    check "page built: ${page}.html" "file not found"
  fi
done

# ── Check 2: No unresolved placeholders or TODO text ───────────────
UNRESOLVED=$(python3 -c "
import os, re
issues = []
pattern = re.compile(r'<!-- MODULE:|<!-- HEADER -->|<!-- FOOTER -->|\\bplaceholder\\b|\\btodo\\b', re.IGNORECASE)
for f in os.listdir('$OUT_DIR'):
    if not f.endswith('.html'): continue
    c = open('$OUT_DIR/' + f).read()
    matches = pattern.findall(c)
    if matches:
        issues.append(f + ': ' + ', '.join(sorted(set(matches))))
print(';'.join(issues) if issues else 'ok')
")
check "no unresolved placeholders or TODO text" "$([[ "$UNRESOLVED" == "ok" ]] && echo pass || echo "$UNRESOLVED")"

# ── Check 3: sitemap.xml generated ──────────────────────────────────
check "sitemap.xml exists" "$([[ -f "$OUT_DIR/sitemap.xml" ]] && echo pass || echo 'missing')"

SITEMAP_COUNT=$(python3 -c "
import re
c = open('$OUT_DIR/sitemap.xml').read()
print(len(re.findall('<url>', c)))
" 2>/dev/null || echo 0)
check "sitemap has entries" "$([[ "$SITEMAP_COUNT" -gt 0 ]] && echo pass || echo 'count=0')"

# ── Check 4: CSS assets copied ──────────────────────────────────────
check "css assets present"     "$([[ -d "$OUT_DIR/css" ]] && echo pass || echo 'missing')"
check "variables.css present"  "$([[ -f "$OUT_DIR/css/variables.css" ]] && echo pass || echo 'missing')"

# ── Check 5: index.html has no broken CSS import ────────────────────
MISSING_IMPORTS=$(python3 -c "
import re, os
c = open('$OUT_DIR/index.html').read()
hrefs = re.findall(r'href=\"(/[^\"]+\.css)\"', c)
missing = []
for h in hrefs:
    # convert root-relative to path under out_dir
    path = '$OUT_DIR' + h
    if not os.path.exists(path):
        missing.append(h)
print(';'.join(missing) if missing else 'ok')
")
check "no broken CSS imports in index.html" "$([[ "$MISSING_IMPORTS" == "ok" ]] && echo pass || echo "$MISSING_IMPORTS")"

# ── Check 6: Lead form module (if enabled) ───────────────────────────
LF_ENABLED=$(python3 -c "
import json
d = json.load(open('$SITE_JSON'))
print('1' if d['_factory']['modules'].get('odoo_lead_form') else '0')
")
if [[ "$LF_ENABLED" == "1" ]]; then
  LF_PRESENT=$(python3 -c "
c = open('$OUT_DIR/index.html').read()
print('1' if 'odooLeadForm' in c else '0')
  ")
  check "lead form injected in index.html" "$([[ "$LF_PRESENT" == "1" ]] && echo pass || echo 'odooLeadForm not found')"
fi

# ── Summary ──────────────────────────────────────────────────────────
echo ""
if [[ "$FAILS" -eq 0 ]]; then
  echo "==> SMOKE TEST PASSED (all checks)"
else
  echo "==> SMOKE TEST FAILED ($FAILS checks failed)"
  rm -rf "$OUT_DIR"
  exit 1
fi

rm -rf "$OUT_DIR"
exit 0
