"""What enhance.py turns the 2003 markup into.

These pin behaviour that was previously only ever probed by hand, and the
redaction cases are the ones that matter most: it deletes content, and an
over-deletion is silent -- verify.py fails on an address that SURVIVES, never
on a paragraph that vanished.
"""
import re

from enhance import enhance

FR = dict(lang="fr", h1="Titre")


def out(fragment, lang="fr", h1="Titre"):
    return enhance(fragment, lang, h1)


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------

def test_header_row_becomes_th_and_labels_its_cells():
    """All cells emphasised is the archive's usual way of marking a header."""
    html = out('<table>'
               '<tr><td><strong>Nom</strong></td><td><strong>Prix</strong></td></tr>'
               '<tr><td>Potion</td><td>100</td></tr>'
               '</table>')
    assert "<th" in html
    assert 'data-label="Nom"' in html
    assert 'data-label="Prix"' in html
    assert "t-cards" in html


def test_table_without_a_header_row_scrolls_instead_of_carding():
    """A card layout with no column names would label nothing."""
    html = out('<table><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></table>')
    assert "t-scroll" in html
    assert "data-label" not in html


def test_every_table_is_classified():
    """verify.py rejects a table that is neither; nothing may slip between."""
    for frag in ('<table><tr><td><strong>A</strong></td><td><strong>B</strong></td></tr>'
                 '<tr><td>1</td><td>2</td></tr></table>',
                 '<table><tr><td>x</td></tr></table>'):
        html = out(frag)
        assert "t-cards" in html or "t-scroll" in html


# --------------------------------------------------------------------------
# Icon links
# --------------------------------------------------------------------------

def test_screenshot_icon_gets_a_class_and_an_accessible_name():
    html = out('<p><a href="screenshots/x.jpg"><img src="images/screen.gif" '
               'width="12" height="15"/></a></p>')
    assert "screen-link" in html
    assert "aria-label" in html


def test_back_to_top_icon_targets_the_content_landmark():
    """href="#" scrolls nowhere and tells a screen reader nothing."""
    html = out('<p><a href="#"><img src="images/top.png" width="12" height="15"/></a></p>')
    assert 'href="#content"' in html
    assert "to-top" in html


def test_an_icon_link_that_also_has_text_is_left_alone():
    """Only the bare icons are controls; a link with a label is prose."""
    html = out('<p><a href="x.html">Lire <img src="images/screen.gif"/></a></p>')
    assert "screen-link" not in html


# --------------------------------------------------------------------------
# Sprites
# --------------------------------------------------------------------------

def test_sprite_alt_comes_from_the_file_name():
    """The Digimon sprites ARE the content of the digivolution pages."""
    assert 'alt="Agumon"' in out('<p><img src="id2/Agumon.gif"/></p>')


# --------------------------------------------------------------------------
# Email redaction. Each case names what must SURVIVE, not only what must go.
# --------------------------------------------------------------------------

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def test_mailto_attribution_keeps_the_name():
    html = out('<p><em>Par <a href="mailto:kev@example.com">Fire_Storm</a></em></p>')
    assert "Fire_Storm" in html
    assert not EMAIL.search(html)


def test_isolated_contact_clause_goes_entirely():
    """A clause introducing an address that is gone reads as a broken page."""
    html = out('<p>Blabla.<br/>Contactez-le a: kev@example.com<br/>Suite.</p>')
    assert "Contactez" not in html
    assert "Blabla." in html and "Suite." in html
    assert not EMAIL.search(html)


def test_a_line_carrying_other_content_keeps_it():
    """The bound that stops the line deletion eating a neighbour."""
    html = out('<td>Contact: kev@example.com, phone: 555-1234</td>')
    assert "555-1234" in html
    assert not EMAIL.search(html)


def test_an_address_mid_paragraph_keeps_its_neighbouring_sentences():
    html = out('<p>Some intro. Contact kev@example.com for help. '
               'More info follows.<br/>Next line.</p>')
    assert "Some intro." in html
    assert "More info follows." in html
    assert "Next line." in html
    assert not EMAIL.search(html)


def test_address_as_first_child_with_a_following_break():
    html = out('<p>kev@example.com<br/>Reste.</p>')
    assert "Reste." in html
    assert not EMAIL.search(html)


def test_two_addresses_in_one_parent_both_go():
    html = out('<p>a@example.com<br/>c@example.org<br/>Fin.</p>')
    assert "Fin." in html
    assert not EMAIL.search(html)


def test_the_closing_break_goes_even_with_whitespace_before_it():
    """Unwrapping the mailto leaves a space between the address and its <br>.

    A forward scan that only looked at the immediately next sibling stopped at
    that space, left the <br>, and both emulation pages gained a blank line --
    invisible to every other check, and only caught by diffing against main.

    The mailto form is load-bearing in this fixture: unwrapping the link is what
    splits the address and the <br> into separate siblings with a space between
    them. Written as plain text, the address and the space are a single node,
    the <br> is already adjacent, and the bug does not reproduce -- which is
    exactly how the first version of this test passed against the bug.
    """
    html = out('<p>a<br/>Contactez : '
               '<a href="mailto:x@example.com">x@example.com</a> <br/>b</p>')
    assert html.count("<br") == 1


def test_text_that_merely_contains_an_at_sign_is_untouched():
    """The redaction must not treat every @ as an address and eat a line."""
    html = out('<p>Le combo @ 3 coups fait mal.<br/>Suite.</p>')
    assert "Le combo @ 3 coups fait mal." in html
    assert "Suite." in html


def test_a_mailto_href_alone_is_enough_to_redact():
    """Even when the visible text is not itself an address."""
    html = out('<p><a href="mailto:kev@example.com">Ecrire</a></p>')
    assert "Ecrire" in html
    assert "mailto:" not in html
