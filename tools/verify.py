#!/usr/bin/env python3
"""Verify the generated site. Fails (exit 1) on any broken link, missing asset,
hotlinked image, leftover legacy markup, language/parity problem, or malformed
page. Run locally (`python tools/verify.py`) and in CI.
"""
import os
import re
import sys
import glob
from html.parser import HTMLParser
from bs4 import BeautifulSoup

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ("fr", "en")
ASSET_ATTRS = [("img", "src"), ("script", "src"), ("link", "href"), ("source", "src")]
# substrings that must never survive in a generated page.
# (The Wayback attribution link web.archive.org/web/2023/http://saetta.free.fr/...
#  is legitimate and intentionally NOT forbidden.)
FORBIDDEN = ["index.php?page=", "function.include", "function.main", "id_/http"]

errors = []
warnings = []

def err(page, msg):
    errors.append(f"{page}: {msg}")

def warn(page, msg):
    warnings.append(f"{page}: {msg}")

class WellFormed(HTMLParser):
    """Minimal sanity parse — raises on malformed markup."""
    pass

def rel(path):
    return os.path.relpath(path, REPO)

def check_page(path, lang):
    raw = open(path, encoding="utf-8").read()
    name = rel(path)
    # 1. parses without exception
    try:
        WellFormed().feed(raw)
    except Exception as e:  # noqa: BLE001
        err(name, f"HTML parse error: {e}")
    soup = BeautifulSoup(raw, "lxml")
    base = os.path.dirname(path)

    # 2. <html lang> matches the directory
    htmltag = soup.find("html")
    if not htmltag or htmltag.get("lang") != lang:
        err(name, f'<html lang> should be "{lang}", got "{htmltag.get("lang") if htmltag else None}"')

    # 3. a single <h1>
    h1s = soup.select("main h1, article h1")
    if len(h1s) != 1:
        err(name, f"expected exactly one content <h1>, found {len(h1s)}")

    # 4. assets resolve on disk; no hotlinked images
    for tag, attr in ASSET_ATTRS:
        for e in soup.find_all(tag):
            v = (e.get(attr) or "").strip()
            if not v:
                continue
            if v.startswith(("http://", "https://", "data:", "mailto:", "#")):
                if tag == "img":
                    err(name, f"hotlinked/external image: {v}")
                continue
            target = os.path.normpath(os.path.join(base, v.split("#")[0]))
            if not (os.path.exists(target) and os.path.getsize(target) > 0):
                err(name, f"missing asset {attr}={v}")

    # 5. internal links resolve
    for a in soup.find_all("a", href=True):
        h = a["href"].strip()
        if h.startswith(("http://", "https://", "mailto:", "#")) or not h:
            continue
        target = os.path.normpath(os.path.join(base, h.split("#")[0]))
        if not os.path.exists(target):
            err(name, f"broken internal link: {h}")

    # 6. language switcher present and pointing at both languages
    if not soup.select_one('.lang-switch a[href*="/fr/"]') or not soup.select_one('.lang-switch a[href*="/en/"]'):
        err(name, "missing or incomplete language switcher")

    # 7. no leftover legacy markup
    for bad in FORBIDDEN:
        if bad in raw:
            err(name, f"leftover legacy markup: {bad!r}")

    # 8. soft: obvious untranslated French in the English tree
    if lang == "en":
        text = soup.select_one("main").get_text(" ", strip=True).lower() if soup.select_one("main") else ""
        fr_markers = re.findall(r"\b(lorsqu|aujourd|vélocité|digivolue|niveau|toutefois|pêche|épée)\w*", text)
        if len(fr_markers) > 3:
            warn(name, f"possible untranslated French ({len(fr_markers)} markers, e.g. {fr_markers[:4]})")

def main():
    pages = {}
    for lang in LANGS:
        d = os.path.join(REPO, lang)
        if not os.path.isdir(d):
            err(lang + "/", "language directory missing")
            continue
        slugs = set()
        for path in sorted(glob.glob(os.path.join(d, "*.html"))):
            slugs.add(os.path.basename(path))
            check_page(path, lang)
        pages[lang] = slugs

    # 9. FR/EN parity — same set of pages
    if "fr" in pages and "en" in pages:
        only_fr = pages["fr"] - pages["en"]
        only_en = pages["en"] - pages["fr"]
        if only_fr:
            err("parity", f"pages in FR but not EN: {sorted(only_fr)}")
        if only_en:
            err("parity", f"pages in EN but not FR: {sorted(only_en)}")

    # 10. root landing exists and redirects
    root = os.path.join(REPO, "index.html")
    if not os.path.exists(root):
        err("index.html", "root language landing missing")
    else:
        rl = open(root, encoding="utf-8").read()
        if "location.replace" not in rl or 'href="fr/' not in rl or 'href="en/' not in rl:
            err("index.html", "root landing must redirect and link both languages")

    n_pages = sum(len(s) for s in pages.values())
    print(f"checked {n_pages} pages across {len(pages)} languages")
    for w in warnings:
        print("  WARN ", w)
    if errors:
        print(f"\n{len(errors)} ERROR(S):")
        for e in errors:
            print("  FAIL ", e)
        sys.exit(1)
    print("OK — all checks passed")

if __name__ == "__main__":
    main()
