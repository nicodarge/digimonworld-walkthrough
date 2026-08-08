"""Every verify.py check, probed against the input it must REFUSE.

A check read against what it was meant to mean is not a check. Each test here
mutates a real built page so the defect is the only difference, then asserts
that check fires -- and `test_the_unmutated_baseline_is_clean` is what stops the
whole file passing vacuously if the fixtures ever drift.
"""
import os
import re
import subprocess
import sys

import pytest

import verify

REPO = verify.REPO
TOOLS = os.path.join(REPO, "tools")
TMP = "__pytest_tmp.html"


def errors_for(lang, page, *subs, count=1):
    """Copy a built page with substitutions applied, check it, return errors.

    The copy lives beside the original so relative assets and links still
    resolve; anything else would make every asset check fire at once and drown
    the one defect under test.

    count=0 replaces every occurrence, which some checks need: "no labelled
    cell" cannot fire while one label survives, so breaking the first is not a
    defect at all.
    """
    src = os.path.join(REPO, lang, page)
    text = open(src, encoding="utf-8").read()
    for old, new in subs:
        assert old in text, f"fixture drift: {old!r} not found in {lang}/{page}"
        text = text.replace(old, new) if count == 0 else text.replace(old, new, count)

    tmp = os.path.join(REPO, lang, TMP)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        verify.errors.clear()
        verify.check_page(tmp, lang)
        return list(verify.errors)
    finally:
        os.unlink(tmp)
        verify.errors.clear()


def matching(errors, pattern):
    return [e for e in errors if re.search(pattern, e, re.I)]


# --------------------------------------------------------------------------

def test_the_unmutated_baseline_is_clean():
    """Without this, every other test in the file could pass for free."""
    assert errors_for("fr", "index.html") == []


@pytest.mark.parametrize("attr,expected", [
    ('rel="canonical"', "canonical"),
    ('property="og:title"', "og:title"),
    ('property="og:image"', "og:image"),
    ('rel="icon"', "favicon"),
    ('name="description"', "description"),
])
def test_missing_crawler_metadata_is_refused(attr, expected):
    errs = errors_for("fr", "index.html", (attr, attr.replace('="', '="x')))
    assert matching(errs, f"missing {re.escape(expected)}")


def test_an_image_without_alt_is_refused():
    """The Digimon sprites are the content, not decoration."""
    errs = errors_for("fr", "digivolution.html", ('alt="', 'data-was-alt="'))
    assert matching(errs, "image without alt")


def test_a_broken_internal_link_is_refused():
    errs = errors_for("fr", "index.html", ('href="solution.html"', 'href="nope.html"'))
    assert matching(errs, "broken internal link")


def test_a_hotlinked_image_is_refused():
    """Fidelity to the archive stops at depending on someone else's server."""
    errs = errors_for("fr", "index.html",
                      ("</main>", '<img src="https://example.com/x.png" alt="x"></main>'))
    assert matching(errs, "hotlinked")


def test_an_anchor_with_no_target_is_refused():
    """The walkthrough navigates by anchors; a lost id sends you to the top."""
    errs = errors_for("fr", "index.html",
                      ("</main>", '<a href="#nowhere">x</a></main>'))
    assert matching(errs, "anchor with no target")


def test_an_unclassified_table_is_refused():
    errs = errors_for("fr", "peche.html", ('class="t-cards"', 'class="t-nope"'))
    assert matching(errs, "neither t-cards nor t-scroll")


def test_a_card_table_with_no_labelled_cell_is_refused():
    errs = errors_for("fr", "peche.html", ("data-label=", "data-nolabel="), count=0)
    assert matching(errs, "without a single labelled cell")


def test_a_text_banner_left_as_an_image_is_refused():
    """A wide, short strip is rendered text the build failed to convert."""
    errs = errors_for(
        "fr", "index.html",
        ("</main>", '<article><img src="../images/banton2.gif" '
                    'width="290" height="25" alt=""></article></main>'))
    assert matching(errs, "section banner left as an image")


def test_a_published_email_address_is_refused():
    errs = errors_for("fr", "index.html", ("</main>", "kev@example.com</main>"))
    assert matching(errs, "email address published")


def test_leftover_legacy_markup_is_refused():
    errs = errors_for("fr", "index.html", ("</main>", "index.php?page=Solution</main>"))
    assert matching(errs, "leftover legacy markup")


def test_a_missing_language_switcher_is_refused():
    errs = errors_for("fr", "index.html", ('class="lang-switch"', 'class="gone"'))
    assert matching(errs, "language switcher")


# --- og:image, the asset nothing on the page references ---------------------

OG = 'property="og:image" content="'


@pytest.mark.parametrize("replacement,pattern", [
    ('property="og:image" content="/images/og-card.png" data-x="',
     "not an absolute URL"),
    ('property="og:image" content="https://evil.example/x.png" data-x="',
     "not an absolute URL"),
])
def test_an_og_image_that_is_not_on_this_origin_is_refused(replacement, pattern):
    errs = errors_for("fr", "index.html", (OG, replacement))
    assert matching(errs, pattern)


def test_an_og_image_pointing_at_a_missing_file_is_refused():
    errs = errors_for("fr", "index.html", ("og-card.png", "og-card-gone.png"))
    assert matching(errs, "missing file")


def test_og_image_dimensions_that_do_not_match_the_file_are_refused():
    """The declared size is a literal; nothing else keeps it honest."""
    errs = errors_for("fr", "index.html",
                      ('property="og:image:width" content="1200"',
                       'property="og:image:width" content="800"'))
    assert matching(errs, "but declares")


# --- png_size, read from IHDR so CI needs no imaging library ---------------

def test_png_size_reads_the_real_dimensions():
    assert verify.png_size(os.path.join(REPO, "images", "og-card.png")) == (1200, 630)


def test_png_size_returns_none_for_something_that_is_not_a_png():
    assert verify.png_size(os.path.join(REPO, "images", "banton2.gif")) is None


# --- the root landing page, which sits outside the per-language loop -------

def run_verify():
    proc = subprocess.run([sys.executable, os.path.join(TOOLS, "verify.py")],
                          capture_output=True, text=True, cwd=REPO)
    return proc.returncode, proc.stdout + proc.stderr


def mutate_root(old, new):
    path = os.path.join(REPO, "index.html")
    original = open(path, encoding="utf-8").read()
    assert old in original, f"fixture drift: {old!r} not in index.html"
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(original.replace(old, new, 1))
        return run_verify()
    finally:
        with open(path, "w", encoding="utf-8") as f:
            f.write(original)


def test_root_page_missing_canonical_is_refused():
    code, out = mutate_root('rel="canonical"', 'rel="xcanonical"')
    assert code != 0 and "canonical" in out


def test_root_page_missing_description_is_refused():
    code, out = mutate_root('name="description"', 'name="xdescription"')
    assert code != 0 and "description" in out


def test_hreflang_on_the_root_page_is_refused():
    """Its canonical points at en/; declaring hreflang here competes with it."""
    code, out = mutate_root("<link rel=\"canonical\"",
                            '<link rel="alternate" hreflang="fr" href="fr/">\n'
                            '<link rel="canonical"')
    assert code != 0 and "hreflang" in out


def test_the_site_verifies_clean_as_committed():
    code, out = run_verify()
    assert code == 0, out
