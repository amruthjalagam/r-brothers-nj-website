#!/usr/bin/env python3
"""
migrate_v1_to_v2.py — Add _factory block to a v1 site.json.
Usage: python3 migrate_v1_to_v2.py path/to/site.json
Writes the updated file in place. Original backed up as site.json.v1.bak
"""
import json, os, shutil, sys

V2_FACTORY_DEFAULTS = {
    "schema_version": "2",
    "archetype": "service",
    "industry": "",
    "template_variant": "base",
    "firecrawl_source": "",
    "pages": ["index", "about", "services", "contact", "faq", "gallery"],
    "modules": {
        "odoo_lead_form": False, "odoo_calendar": False,
        "odoo_invoice": False, "odoo_reviews": False,
        "social_feed": False, "patient_intake": False,
    },
    "animations": {
        "scroll_timeline": False, "video_scrub": False,
        "video_src": "", "reduced_motion_fallback": True,
    },
    "brand": {
        "accent_color": "#2563eb", "accent_hover": "#1d4ed8",
        "gold_color": "#f59e0b", "gold_hover": "#d97706",
        "font_headline": "Space Grotesk", "font_body": "Inter",
        "google_fonts_url": "",
    },
    "seo": {"base_url": "https://example.com", "site_name": "", "og_image": "/assets/og-image.jpg"},
    "lead_form": {"archetype_fields": "service", "services": []},
    "deploy": {"cloudflare_project": "", "github_repo": "", "custom_domain": ""},
}

path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    print("Usage: migrate_v1_to_v2.py path/to/site.json"); sys.exit(1)

data = json.load(open(path))
if data.get("_factory", {}).get("schema_version") == "2":
    print("Already v2 — nothing to do."); sys.exit(0)

shutil.copy2(path, path + ".v1.bak")
data["_factory"] = V2_FACTORY_DEFAULTS
# Pre-fill site_name from brand if available
if data.get("brand", {}).get("name"):
    data["_factory"]["seo"]["site_name"] = data["brand"]["name"]

with open(path, "w") as f:
    json.dump(data, f, indent=2)
print(f"Migrated to v2. Backup at {path}.v1.bak")
print("Review and fill in: archetype, industry, pages, modules, brand tokens, seo.base_url")
