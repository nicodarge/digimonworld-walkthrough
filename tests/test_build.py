"""build.py's link rewriting, and the invariants of the generated pages.

The site was a PHP app (index.php?page=X); every one of those links had to
become a static path, and a wrong mapping is a 404 nobody notices until a
reader hits it.
"""
import os
import re

import build

REPO = build.REPO


def read(*parts):
    with open(os.path.join(REPO, *parts), encoding="utf-8") as f:
        return f.read()


# --------------------------------------------------------------------------
# Link rewriting
# --------------------------------------------------------------------------

def test_a_php_page_link_becomes_its_static_page():
    assert build.map_internal_href("index.php?page=Solution") == "solution.html"
    assert build.map_internal_href("index.php?page=Digivolution") == "digivolution.html"


def test_the_mapping_is_case_insensitive():
    """The archive is not consistent about it."""
    assert build.map_internal_href("index.php?page=solution") == "solution.html"


def test_an_unknown_page_falls_back_to_the_home_page():
    """Better than emitting a link to a file that was never recovered."""
    assert build.map_internal_href("index.php?page=Guestbook") == "index.html"


def test_the_site_root_becomes_the_home_page():
    assert build.map_internal_href("http://saetta.free.fr/DigimonWorld/") == "index.html"


def test_an_external_link_is_left_alone():
    """None means "not ours"; the caller keeps the href verbatim."""
    assert build.map_internal_href("https://web.archive.org/web/2023/x") is None
    assert build.map_internal_href("https://example.com/") is None


def test_every_page_in_the_table_maps_to_itself():
    for _raw, slug, *_ in build.PAGES:
        page = "index.html" if slug == "index" else f"{slug}.html"
        assert build.map_internal_href(f"index.php?page={_raw}") == page


# --------------------------------------------------------------------------
# The root landing page
# --------------------------------------------------------------------------

def test_the_root_page_substitutes_the_site_url():
    """It is written with replace(), not format(): its CSS is full of braces."""
    html = read("index.html")
    assert "{site}" not in html
    assert build.SITE_URL in html


def test_the_root_page_css_survived_the_substitution():
    """A stray .format() would have raised on the braces, or eaten them."""
    html = read("index.html")
    assert "display:flex" in html
    assert html.count("{") == html.count("}")


def test_the_root_page_points_its_canonical_at_a_real_page():
    html = read("index.html")
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    assert m, "no canonical on the root page"
    target = m.group(1)[len(build.SITE_URL):].lstrip("/")
    assert os.path.exists(os.path.join(REPO, target)), target


def test_the_root_page_declares_no_hreflang():
    """hreflang belongs on the canonical page; here it competes with it."""
    assert not re.search(r'<link[^>]+hreflang', read("index.html"))


# --------------------------------------------------------------------------
# Both language trees
# --------------------------------------------------------------------------

def test_both_languages_have_the_same_pages():
    fr = {os.path.basename(p) for p in os.listdir(os.path.join(REPO, "fr"))}
    en = {os.path.basename(p) for p in os.listdir(os.path.join(REPO, "en"))}
    assert fr == en


def test_every_page_declares_a_distinct_description():
    """One shared description is what a crawler reads as duplicate content."""
    for lang in ("fr", "en"):
        seen = {}
        for name in sorted(os.listdir(os.path.join(REPO, lang))):
            html = read(lang, name)
            m = re.search(r'<meta name="description" content="([^"]*)"', html)
            assert m, f"{lang}/{name} has no description"
            assert m.group(1) not in seen, (
                f"{lang}/{name} repeats the description of {seen.get(m.group(1))}")
            seen[m.group(1)] = name


def test_the_crawler_files_exist():
    for f in ("sitemap.xml", "robots.txt", "404.html", "favicon.svg",
              os.path.join("images", "og-card.png")):
        assert os.path.exists(os.path.join(REPO, f)), f


def test_the_sitemap_lists_every_built_page():
    sitemap = read("sitemap.xml")
    for lang in ("fr", "en"):
        for name in sorted(os.listdir(os.path.join(REPO, lang))):
            assert f"{build.SITE_URL}/{lang}/{name}" in sitemap, f"{lang}/{name}"


# --------------------------------------------------------------------------
# Cache busting
# --------------------------------------------------------------------------

def test_shared_assets_are_referenced_with_a_content_version():
    """Cloudflare caches .css and .js by extension for four hours by default.

    With stable filenames the edge cannot tell a new deploy from the old one:
    a stylesheet fix sat on the origin while the edge served the previous file
    and the layout stayed broken for visitors, with every check green.
    """
    html = read("fr", "index.html")
    assert re.search(r'style\.css\?v=[0-9a-f]{10}"', html)
    assert re.search(r'nav\.js\?v=[0-9a-f]{10}"', html)
    assert re.search(r'style\.css\?v=[0-9a-f]{10}"', read("404.html"))


def test_the_version_is_derived_from_the_file_and_moves_with_it():
    """Content-derived, so the build stays reproducible and the URL only moves
    when the file does."""
    assert build.asset_version("style.css") == build.asset_version("style.css")
    assert build.asset_version("style.css") != build.asset_version("nav.js")

    html = read("fr", "index.html")
    stamped = re.search(r'style\.css\?v=([0-9a-f]{10})"', html).group(1)
    assert stamped == build.asset_version("style.css")


def test_every_page_carries_the_same_version():
    """A page left on an older stamp would fetch a stylesheet the rest is not
    using."""
    stamps = set()
    for lang in ("fr", "en"):
        for name in sorted(os.listdir(os.path.join(REPO, lang))):
            m = re.search(r'style\.css\?v=([0-9a-f]{10})"', read(lang, name))
            assert m, f"{lang}/{name} does not version its stylesheet"
            stamps.add(m.group(1))
    assert len(stamps) == 1, stamps


# --------------------------------------------------------------------------
# No inline script anywhere
# --------------------------------------------------------------------------

INLINE_SCRIPT = re.compile(r"<script(?![^>]*\ssrc=)[^>]*>")


def test_no_page_carries_an_inline_script():
    """What lets the vhost send script-src 'self' instead of 'unsafe-inline'.

    The language chooser's redirect was the only one, and it lived on the page a
    visitor hits first.
    """
    pages = ["index.html", "404.html"]
    for lang in ("fr", "en"):
        pages += [os.path.join(lang, n) for n in sorted(os.listdir(os.path.join(REPO, lang)))]
    for page in pages:
        assert not INLINE_SCRIPT.search(read(page)), f"{page} has an inline <script>"


def test_the_root_page_loads_the_chooser_and_it_redirects():
    html = read("index.html")
    assert re.search(r'<script src="lang\.js\?v=[0-9a-f]{10}"', html)
    assert "location.replace" in read("lang.js")


def test_the_chooser_is_not_the_only_way_out():
    """Scripting off, or a crawler: both languages stay reachable by link."""
    html = read("index.html")
    assert 'href="fr/' in html and 'href="en/' in html
