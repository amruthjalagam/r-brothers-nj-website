#!/usr/bin/env python3
"""
firecrawl_extract.py — Scrape a URL and extract brand tokens.

Uses Firecrawl /v1/scrape to get rendered HTML+metadata, then applies
heuristics to extract colors, fonts, and copy patterns.

Output: brand.json with the same shape as site.json._factory.brand
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error

def load_api_key():
    key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not key:
        env_path = os.path.expanduser("~/MyVault/.env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("FIRECRAWL_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    return key

def firecrawl_scrape(url, api_key):
    payload = json.dumps({
        "url": url,
        "formats": ["html", "metadata"],
        "actions": []
    }).encode()

    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Firecrawl HTTP {e.code}: {body}") from e

def extract_hex_colors(html):
    """Return unique hex colors found in inline styles and <style> blocks."""
    pattern = re.compile(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
    colors = list(dict.fromkeys(m.group(0) for m in pattern.finditer(html)))
    # Filter out near-black (#000 family) and near-white (#fff family) — not brand colors
    brand_colors = [
        c for c in colors
        if not re.match(r'^#(0{3,6}|f{3,6}|1{3}1{3}|eee|fff|ddd|ccc)$', c, re.I)
    ]
    return brand_colors[:10]

def extract_google_fonts(html):
    """Return Google Fonts families referenced in the page."""
    pattern = re.compile(r'fonts\.googleapis\.com/css2\?family=([^"&>]+)')
    matches = pattern.findall(html)
    families = []
    for m in matches:
        for part in m.split("&"):
            if part.startswith("family="):
                part = part[7:]
            name = part.split(":")[0].replace("+", " ").split("|")[0].strip()
            if name and name not in families:
                families.append(name)
    return families

def pick_accent(colors):
    """Heuristic: first non-neutral color is the brand accent."""
    return colors[0] if colors else "#2563eb"

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <url> <output.json>")
        sys.exit(1)

    url, output_path = sys.argv[1], sys.argv[2]
    api_key = load_api_key()
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY not found", file=sys.stderr)
        sys.exit(1)

    print(f"Scraping {url} via Firecrawl...")
    result = firecrawl_scrape(url, api_key)

    html = result.get("data", {}).get("html", "")
    metadata = result.get("data", {}).get("metadata", {})

    colors = extract_hex_colors(html)
    fonts = extract_google_fonts(html)
    accent = pick_accent(colors)

    # Build a partial brand.json — same shape as site.json._factory.brand
    brand = {
        "source_url": url,
        "extracted_colors": colors,
        "accent_color": accent,
        "accent_hover": accent,   # caller can refine
        "gold_color": colors[1] if len(colors) > 1 else "#f59e0b",
        "gold_hover": colors[1] if len(colors) > 1 else "#d97706",
        "font_headline": fonts[0] if fonts else "Space Grotesk",
        "font_body": fonts[1] if len(fonts) > 1 else "Inter",
        "google_fonts_url": (
            f"https://fonts.googleapis.com/css2?family="
            + "&family=".join(f.replace(" ", "+") + ":wght@400;600;700" for f in fonts[:2])
            + "&display=swap"
        ) if fonts else "",
        "page_title": metadata.get("title", ""),
        "meta_description": metadata.get("description", ""),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(brand, f, indent=2)

    print(f"brand.json written to {output_path}")
    print(f"  accent: {brand['accent_color']}")
    print(f"  fonts:  {brand['font_headline']} / {brand['font_body']}")
    print(f"  colors extracted: {len(colors)}")

if __name__ == "__main__":
    main()
