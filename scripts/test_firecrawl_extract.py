#!/usr/bin/env python3
"""Tests for firecrawl_extract.py brand extraction heuristics."""
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from firecrawl_extract import (
    extract_hex_colors,
    extract_google_fonts,
    load_api_key,
    pick_accent,
)


class TestExtractHexColors(unittest.TestCase):
    def test_finds_6_digit_hex(self):
        html = '<div style="color: #3B82F6">hello</div>'
        assert extract_hex_colors(html) == ["#3B82F6"]

    def test_finds_3_digit_hex(self):
        html = '<span style="color: #f0c">'
        assert extract_hex_colors(html) == ["#f0c"]

    def test_filters_black_white_neutrals(self):
        html = 'color:#000000; color:#ffffff; color:#eee; color:#3B82F6;'
        result = extract_hex_colors(html)
        assert "#000000" not in result
        assert "#ffffff" not in result
        assert "#eee" not in result
        assert "#3B82F6" in result

    def test_deduplicates(self):
        html = "#3B82F6 #3B82F6 #3B82F6"
        assert extract_hex_colors(html) == ["#3B82F6"]

    def test_max_10_colors(self):
        colors = " ".join(f"#{i:02x}{i:02x}{(i*3)%256:02x}" for i in range(20, 40))
        result = extract_hex_colors(colors)
        assert len(result) <= 10

    def test_empty_html(self):
        assert extract_hex_colors("") == []

    def test_style_block(self):
        html = "<style>.btn { background: #F59E0B; border: 1px solid #D97706; }</style>"
        result = extract_hex_colors(html)
        assert "#F59E0B" in result
        assert "#D97706" in result


class TestExtractGoogleFonts(unittest.TestCase):
    def test_single_family(self):
        html = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700">'
        assert extract_google_fonts(html) == ["Inter"]

    def test_multi_word_family(self):
        html = '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400">'
        assert extract_google_fonts(html) == ["Space Grotesk"]

    def test_no_fonts(self):
        assert extract_google_fonts("<html><body>no fonts</body></html>") == []

    def test_deduplicates(self):
        html = (
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400">'
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@700">'
        )
        assert extract_google_fonts(html) == ["Inter"]


class TestPickAccent(unittest.TestCase):
    def test_returns_first_color(self):
        assert pick_accent(["#3B82F6", "#F59E0B"]) == "#3B82F6"

    def test_fallback_on_empty(self):
        assert pick_accent([]) == "#2563eb"


class TestLoadApiKey(unittest.TestCase):
    def test_reads_from_env_var(self):
        os.environ["FIRECRAWL_API_KEY"] = "test-key-123"
        try:
            assert load_api_key() == "test-key-123"
        finally:
            del os.environ["FIRECRAWL_API_KEY"]

    def test_reads_from_dotenv_file(self):
        os.environ.pop("FIRECRAWL_API_KEY", None)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("OTHER_VAR=foo\n")
            f.write("FIRECRAWL_API_KEY=fc-from-file\n")
            f.flush()
            # Monkey-patch the path
            import firecrawl_extract as mod
            orig = os.path.expanduser
            mod_expanduser = lambda p: f.name if ".env" in p else orig(p)
            os.path.expanduser = mod_expanduser
            try:
                assert load_api_key() == "fc-from-file"
            finally:
                os.path.expanduser = orig
                os.unlink(f.name)

    def test_returns_empty_when_missing(self):
        os.environ.pop("FIRECRAWL_API_KEY", None)
        import firecrawl_extract as mod
        orig = os.path.expanduser
        os.path.expanduser = lambda p: "/nonexistent/.env" if ".env" in p else orig(p)
        try:
            assert load_api_key() == ""
        finally:
            os.path.expanduser = orig


if __name__ == "__main__":
    unittest.main()
