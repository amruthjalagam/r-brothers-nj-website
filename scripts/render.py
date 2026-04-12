#!/usr/bin/env python3
"""
render.py — Template rendering engine for factory.sh

Sub-commands:
  assemble   — inject partials + module blocks + CMS tokens into HTML pages
  apply-brand — rewrite CSS custom properties in variables.css from site.json tokens
  sitemap    — generate sitemap.xml from dist/ HTML files

All sub-commands read site.json for configuration.
"""
# STUB:TDD — integration tested via test_build.sh smoke test
import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path


# ─────��────────────────────────────���─────────────────────────────────���────────
# Helpers
# ────────���───────────────────────────────────────────���────────────────────────

def load_json(path):
    with open(path) as f:
        return json.load(f)

def read_partial(name, partials_dir="partials"):
    path = os.path.join(partials_dir, f"{name}.html")
    if not os.path.exists(path):
        return f"<!-- MISSING PARTIAL: {name} -->"
    with open(path) as f:
        return f.read()

def inject_partials(html, header, footer):
    html = html.replace("<!-- HEADER -->", header)
    html = html.replace("<!-- FOOTER -->", footer)
    return html

def inject_modules(html, factory, partials_dir="partials"):
    """Replace <!-- MODULE:name --> placeholders based on modules flags."""
    modules = factory.get("modules", {})
    module_map = {
        "odoo-lead-form":  modules.get("odoo_lead_form", False),
        "odoo-calendar":   modules.get("odoo_calendar", False),
        "odoo-invoice":    modules.get("odoo_invoice", False),
        "odoo-reviews":    modules.get("odoo_reviews", False),
        "social-feed":     modules.get("social_feed", False),
        "patient-intake":  modules.get("patient_intake", False),
    }
    for module_name, enabled in module_map.items():
        placeholder = f"<!-- MODULE:{module_name} -->"
        replacement = read_partial(module_name, partials_dir) if enabled else ""
        html = html.replace(placeholder, replacement)
    return html

def inject_head_extras(html, extra_scripts, factory):
    """Inject Google Fonts link and extra script tags before </head>."""
    brand = factory.get("brand", {})
    fonts_url = brand.get("google_fonts_url", "")

    inject = ""
    if fonts_url:
        inject += '\n  <link rel="preconnect" href="https://fonts.googleapis.com">'
        inject += f'\n  <link href="{fonts_url}" rel="stylesheet">'
    if extra_scripts:
        inject += extra_scripts

    if inject:
        html = html.replace("</head>", inject + "\n</head>", 1)
    return html

def apply_cms_tokens(html, site_data):
    """Replace data-cms="key.subkey" values with site.json content."""
    def replacer(m):
        key_path = m.group(1)
        parts = key_path.split(".")
        val = site_data
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p, "")
            else:
                val = ""
                break
        return str(val) if val else m.group(0)  # leave unchanged if missing

    return re.sub(r'data-cms="([^"]+)"', lambda m: replacer(m), html)


# ───────────────────────────────────────────────────────────���─────────────────
# Sub-command: assemble
# ─��────────────��─────────────────────────────��────────────────────────────────

def cmd_assemble(args):
    site_data = load_json(args.site_json)
    factory = site_data.get("_factory", {})
    pages = factory.get("pages", [])

    header = read_partial("header")
    footer = read_partial("footer")
    extra_scripts = args.extra_scripts or ""

    os.makedirs(args.out, exist_ok=True)

    built = []
    for page_slug in pages:
        src = f"{page_slug}.html"
        if not os.path.exists(src):
            print(f"  SKIP {src} (not found)", file=sys.stderr)
            continue

        with open(src) as f:
            html = f.read()

        html = inject_partials(html, header, footer)
        html = inject_modules(html, factory)
        html = inject_head_extras(html, extra_scripts, factory)
        html = apply_cms_tokens(html, site_data)

        # Inject lead form runtime config if module enabled
        if factory.get("modules", {}).get("odoo_lead_form"):
            lf = factory.get("lead_form", {})
            lf_archetype = lf.get("archetype_fields", factory.get("archetype", "service"))
            services_json = json.dumps(lf.get("services", []))
            snippet = (
                '\n<script>'
                'window.LEAD_FORM_ARCHETYPE="' + lf_archetype + '";'
                'window.LEAD_FORM_SERVICES=' + services_json + ';'
                '</script>'
            )
            html = html.replace("</body>", snippet + "\n</body>", 1)

        dest = os.path.join(args.out, src)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w") as f:
            f.write(html)

        built.append(src)
        print(f"  built: {dest}")

    print(f"  {len(built)} pages assembled.")


# ────────────────────────────��───────────────────────────���────────────────────
# Sub-command: apply-brand
# ─────────��──────────────────────────────────────────��────────────────────────

def cmd_apply_brand(args):
    site_data = load_json(args.site_json)
    factory = site_data.get("_factory", {})
    brand = factory.get("brand", {})

    # brand.json from Firecrawl can override site.json brand tokens
    if args.brand_json and os.path.exists(args.brand_json):
        extracted = load_json(args.brand_json)
        for key in ("accent_color", "accent_hover", "gold_color", "gold_hover",
                    "font_headline", "font_body", "google_fonts_url"):
            if extracted.get(key):
                brand[key] = extracted[key]

    with open(args.src) as f:
        css = f.read()

    replacements = {
        "--color-accent:": brand.get("accent_color", ""),
        "--color-accent-hover:": brand.get("accent_hover", ""),
        "--color-gold:": brand.get("gold_color", ""),
        "--color-gold-hover:": brand.get("gold_hover", ""),
    }

    for prop, value in replacements.items():
        if not value:
            continue
        # Replace the value on the line containing the property
        css = re.sub(
            rf'({re.escape(prop)}\s+)#[0-9a-fA-F]{{3,6}}',
            rf'\g<1>{value}',
            css,
        )

    # Font family replacement: match the quoted value inside the property
    if brand.get("font_headline"):
        css = re.sub(
            r"(--font-headline:\s+')[^']+(')",
            rf"\g<1>{brand['font_headline']}, system-ui, -apple-system, sans-serif\g<2>",
            css,
        )
    if brand.get("font_body"):
        css = re.sub(
            r"(--font-body:\s+')[^']+(')",
            rf"\g<1>{brand['font_body']}, system-ui, -apple-system, sans-serif\g<2>",
            css,
        )

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        f.write(css)

    print(f"  variables.css written to {args.out}")


# ─────────────────────────────────────────────────────────────���───────────────
# Sub-command: sitemap
# ─────────────────────────────────────────────────────────────────────────────

SITEMAP_EXCLUDE = re.compile(r'404|archive|account|admin/')

def cmd_sitemap(args):
    today = date.today().isoformat()
    html_files = sorted(Path(args.out_dir).rglob("*.html"))

    urls = []
    for p in html_files:
        rel = p.relative_to(args.out_dir).as_posix()
        if SITEMAP_EXCLUDE.search(rel):
            continue
        loc = f"{args.base_url}/" if rel == "index.html" else f"{args.base_url}/{rel}"
        urls.append((loc, today))

    sitemap_path = os.path.join(args.out_dir, "sitemap.xml")
    with open(sitemap_path, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for loc, lastmod in urls:
            f.write(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>\n")
        f.write("</urlset>\n")

    print(f"  sitemap.xml: {len(urls)} URLs → {sitemap_path}")


# ───────────────────────────────────────────���─────────────────────────────────
# CLI entry
# ──��──────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="factory render engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_assemble = sub.add_parser("assemble")
    p_assemble.add_argument("--site-json", required=True)
    p_assemble.add_argument("--extra-scripts", default="")
    p_assemble.add_argument("--out", required=True)

    p_brand = sub.add_parser("apply-brand")
    p_brand.add_argument("--site-json", required=True)
    p_brand.add_argument("--brand-json", default="")
    p_brand.add_argument("--src", required=True)
    p_brand.add_argument("--out", required=True)

    p_sitemap = sub.add_parser("sitemap")
    p_sitemap.add_argument("--base-url", required=True)
    p_sitemap.add_argument("--out-dir", required=True)

    args = parser.parse_args()
    {
        "assemble":    cmd_assemble,
        "apply-brand": cmd_apply_brand,
        "sitemap":     cmd_sitemap,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
