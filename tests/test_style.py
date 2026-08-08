"""Rules that must not clobber the centring of an element carrying .wrap.

`.wrap` centres the page column with `margin: 0 auto`. Any later rule that
matches the same element and sets a margin shorthand with an explicit
horizontal value silently wins, and that element drifts out of the column while
everything around it stays put -- which is exactly what happened to the hero
and the nav: both sat 110px left of the content card, on every page, for as
long as the stylesheet has existed. Nothing else here catches it. verify.py
reads the HTML, not the rendered layout, and the markup was correct all along.
"""
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = open(os.path.join(REPO, "style.css"), encoding="utf-8").read()

# Selectors whose elements carry class="wrap" in the generated pages.
WRAPPED = [".site-nav ul", ".hero"]

# margin shorthands whose horizontal component is a length rather than auto:
# `margin: 0`, `margin: 22px 0 6px`, `margin: 1px 2px 3px 4px`.
HORIZONTAL_IS_FIXED = re.compile(
    r"margin:\s*"
    r"(?:[\w.%-]+\s*;"                      # one value  -> applies to all sides
    r"|[\w.%-]+\s+(?!auto)[\w.%-]+\s*;"     # two        -> second is horizontal
    r"|[\w.%-]+\s+(?!auto)[\w.%-]+\s+[\w.%-]+\s*;"          # three
    r"|[\w.%-]+\s+(?!auto)[\w.%-]+\s+[\w.%-]+\s+[\w.%-]+\s*;)"  # four
)


def rule_body(selector):
    """The declarations of the first rule whose selector list starts with this."""
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", CSS)
    assert m, f"no rule for {selector} in style.css"
    return m.group(1)


def test_wrap_carrying_rules_keep_their_auto_side_margins():
    for selector in WRAPPED:
        body = rule_body(selector)
        if "margin" not in body:
            continue
        assert not HORIZONTAL_IS_FIXED.search(body + ";"), (
            f"{selector} sets a margin with a fixed horizontal value; it carries "
            f".wrap, so this un-centres it. Use auto: {body.strip()!r}")


def test_the_probe_itself_catches_the_shapes_it_must():
    """A guard nobody has fed a bad value is not a guard."""
    bad = ["margin: 0;", "margin: 22px 0 6px;", "margin: 1px 2px;",
           "margin: 1px 2px 3px 4px;"]
    good = ["margin: 0 auto;", "margin: 22px auto 6px;", "margin-top: 4px;",
            "margin: 0 auto 6px;"]
    for decl in bad:
        assert HORIZONTAL_IS_FIXED.search(decl), f"should be refused: {decl}"
    for decl in good:
        assert not HORIZONTAL_IS_FIXED.search(decl), f"should be accepted: {decl}"


def test_wrap_still_centres():
    """The premise everything above rests on."""
    assert re.search(r"^\.wrap\s*\{[^}]*margin:\s*0\s+auto", CSS, re.M)
