#!/usr/bin/env python3
"""Post-process an extracted content fragment into accessible, responsive markup.

The fragments in sources/fragments/ keep the archived structure verbatim, so the
restoration stays auditable against the Wayback snapshots. Everything that turns
that 2003 markup into a usable page happens here, once, for both languages:

  * section banners (images/<area>.jpg) become real <h2>/<h3> headings, taking
    their text from the shortcut table already present in the same fragment —
    derived per language, never hard-coded;
  * Digimon sprites (id2/<Name>.gif) get an alt from their file name;
  * the 12x15px screenshot and back-to-top icons become labelled links with a
    touch-sized hit area;
  * header rows and full-width title rows become <th>, which also gives every
    data cell a data-label the stylesheet uses for the mobile card layout;
  * the legacy centred title that duplicates the page <h1> is dropped.

Everything is structural: a fragment with none of these patterns passes through
unchanged.
"""
import os
import re

from bs4 import BeautifulSoup

# Sub-heading banner repeated inside the walkthrough. Its text is baked into the
# image, so unlike the area banners it cannot be derived from the fragment.
RECRUIT_BANNER = "recru.jpg"
RECRUIT_LABEL = {"fr": "Recrutons !", "en": "Recruiting"}
TOP_LABEL = {"fr": "Retour en haut", "en": "Back to top"}
SCREEN_LABEL = {"fr": "Voir la capture d'écran", "en": "View the screenshot"}
SCROLL_HINT = {"fr": "Faites défiler le tableau horizontalement",
               "en": "Scroll the table horizontally"}


def _anchor_labels(soup):
    """Map anchor id -> link text, read from the fragment's own shortcut links.

    The walkthrough opens with a table of `<a href="#ludo">LudoBourg</a>` links,
    translated alongside the rest of the content. Reading the headings back from
    it keeps FR and EN in sync without a second mapping to maintain.
    """
    labels = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href.startswith("#") or len(href) < 2:
            continue
        text = a.get_text(" ", strip=True)
        if text and href[1:] not in labels:
            labels[href[1:]] = text
    return labels


# Tags the archive wraps a banner in, or pads it with, without adding meaning.
# The banner still opens its paragraph when it sits behind one of these.
_TRANSPARENT = ("span", "font", "br")


def _opens_paragraph(p, img):
    """True when nothing meaningful precedes `img` inside `p`."""
    for node in p.descendants:
        if node is img:
            return True
        if getattr(node, "name", None):
            if node.name not in _TRANSPARENT:
                return False
        elif str(node).strip():
            return False
    return False


def _banner_heading(p, labels, lang):
    """Turn a paragraph opening on a section banner into a real heading.

    The paragraph is stripped of the banner, of the named anchor the heading
    now carries and of the back-to-top icon, and keeps the section's opening
    prose. Returns the heading tag, or None when this is not a section banner.
    """
    img = p.find("img", src=True)
    if img is None:
        return None
    src = os.path.basename(img["src"])
    if not src.endswith((".jpg", ".png")) or src == "top.png":
        return None
    if not _opens_paragraph(p, img):
        return None

    if src == RECRUIT_BANNER:
        level, anchor, text = "h3", None, RECRUIT_LABEL[lang]
    else:
        anchor_tag = img.find_next("a", id=True)
        anchor = anchor_tag["id"] if anchor_tag else None
        text = labels.get(anchor)
        if not text:
            return None
        level = "h2"

    heading = BeautifulSoup("", "lxml").new_tag(level)
    heading.string = text
    if anchor:
        heading["id"] = anchor
        anchor_tag.decompose()
    img.decompose()
    # The back-to-top icon belongs to the banner, not to the prose.
    for a in p.find_all("a", href=True):
        icon = a.find("img", src=True)
        if icon and os.path.basename(icon["src"]) == "top.png" and not a.get_text(strip=True):
            a.decompose()
    # Leading separators left behind once the banner is gone.
    for node in list(p.children):
        if getattr(node, "name", None) == "br" or (
                not getattr(node, "name", None) and not str(node).strip()):
            node.extract()
            continue
        break
    return heading


def _is_banner(img):
    src = os.path.basename(img.get("src", ""))
    return src.endswith((".jpg", ".png")) and src != "top.png"


def _split_banner_paragraphs(soup):
    """Give a banner buried mid-paragraph its own paragraph to open.

    The archive is inconsistent: most section banners start a `<p>`, but a few
    sit after a `<br/><br/>` in the middle of the previous section's prose. Both
    mean the same thing, so split the paragraph and let both take the same path.
    """
    changed = True
    while changed:
        changed = False
        for p in soup.find_all("p"):
            for img in p.find_all("img", src=True):
                if (not _is_banner(img) or img.parent is not p
                        or _opens_paragraph(p, img)):
                    continue
                head = BeautifulSoup("", "lxml").new_tag("p")
                for node in list(p.children):
                    if node is img:
                        break
                    head.append(node.extract())
                while head.contents:
                    last = head.contents[-1]
                    if getattr(last, "name", None) == "br" or (
                            not getattr(last, "name", None) and not str(last).strip()):
                        last.extract()
                        continue
                    break
                if head.get_text(strip=True) or head.find(["img", "a"]):
                    p.insert_before(head)
                changed = True
                break
            if changed:
                break


def _headings(soup, lang):
    _split_banner_paragraphs(soup)
    labels = _anchor_labels(soup)
    for p in soup.find_all("p"):
        heading = _banner_heading(p, labels, lang)
        if heading is None:
            continue
        p.insert_before(heading)
        if not (p.get_text(strip=True) or p.find(["img", "a"])):
            p.decompose()


def _sprite_alt(soup):
    """id2/Agumon.gif -> alt="Agumon". The sprite IS the information here."""
    for img in soup.find_all("img", src=True):
        if img.get("alt"):
            continue
        src = img["src"]
        if "id2/" in src:
            img["alt"] = os.path.splitext(os.path.basename(src))[0]
        else:
            img["alt"] = ""


def _icon_links(soup, lang):
    """Give the 12x15px icon links a name and a class the stylesheet sizes up."""
    for a in soup.find_all("a", href=True):
        img = a.find("img", src=True)
        if img is None or a.get_text(strip=True):
            continue
        src = os.path.basename(img["src"])
        if src == "top.png":
            a["class"] = a.get("class", []) + ["to-top"]
            a["aria-label"] = TOP_LABEL[lang]
            if a["href"] == "#":
                a["href"] = "#content"
        elif src == "screen.gif":
            a["class"] = a.get("class", []) + ["screen-link"]
            a["aria-label"] = SCREEN_LABEL[lang]


def _cells(row):
    return row.find_all(["td", "th"], recursive=False)


def _is_header_row(row, after_title=False):
    """A column-header row, in either of the two shapes the archive uses.

    Most tables emphasise the header cells (`<strong>`); a few only centre them,
    and those are only recognisable by position — directly under the row that
    names the section. Centring alone is not enough, several tables centre every
    cell they contain.
    """
    cells = _cells(row)
    if len(cells) < 2 or not all(c.get_text(strip=True) for c in cells):
        return False
    if all(c.find("strong") for c in cells):
        return True
    return after_title and all(c.find("div", align="center") for c in cells)


def _is_title_row(row, width):
    cells = _cells(row)
    return (len(cells) == 1 and cells[0].find("strong")
            and int(cells[0].get("colspan", 1)) >= max(2, width))


def _table_width(table):
    return max((len(_cells(r)) for r in table.find_all("tr")), default=0)


def _tables(soup, lang):
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        width = _table_width(table)
        headers, after_title = [], False
        for row in rows:
            if _is_title_row(row, width):
                cell = _cells(row)[0]
                cell.name = "th"
                cell["scope"] = "colgroup"
                headers, after_title = [], True   # a new section restarts the columns
                continue
            was_after_title, after_title = after_title, False
            if not headers and _is_header_row(row, was_after_title):
                for cell in _cells(row):
                    cell.name = "th"
                    cell["scope"] = "col"
                    headers.append(cell.get_text(" ", strip=True))
                continue
            if headers:
                for cell, label in zip(_cells(row), headers):
                    if cell.name == "td" and label:
                        cell["data-label"] = label
        # A table whose columns are never named cannot become a card list; the
        # stylesheet scrolls those instead of squeezing them to one word wide.
        table["class"] = table.get("class", []) + (
            ["t-cards"] if any(_cells(r) and _cells(r)[0].get("data-label")
                               for r in rows) else ["t-scroll"])
        if "t-scroll" in table["class"]:
            table["data-scroll-hint"] = SCROLL_HINT[lang]


def _drop_duplicate_title(soup, h1):
    """Remove the legacy centred title that repeats the page's own <h1>."""
    norm = re.sub(r"\W+", "", h1).lower()
    for el in soup.find_all(["p", "div", "h2", "h3"], limit=6):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if re.sub(r"\W+", "", text).lower() == norm and not el.find(["img", "a"]):
            el.decompose()
        return


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _redact_emails(body):
    """Drop third-party email addresses from the published pages.

    The archive carries contributors' personal addresses from 2003, written
    when the page was one corner of a personal free.fr space. Republishing them
    on an indexed site hands them to every address harvester that passes, and
    the people concerned never agreed to that -- their contribution was the
    tool, not their inbox.

    Attribution survives: a mailto link keeps its visible text, so "Par
    <a>Fire_Storm</a>" simply becomes "Par Fire_Storm". Only the address goes.
    This is done here rather than in sources/, which stays verbatim so the
    restoration remains auditable against the Wayback snapshots.
    """
    for a in body.find_all("a", href=True):
        if a["href"].strip().lower().startswith("mailto:"):
            a.unwrap()

    # An address that was only an href is already gone. One that was visible
    # text leaves the clause that introduced it pointing at nothing -- "vous
    # pouvez le contacter a l'adresse suivante" followed by a line break reads
    # as a broken page, not a redacted one. In this archive each such clause
    # sits on its own <br>-delimited line, so drop the line: back to the
    # previous <br> in the same parent, through the address, and the <br> that
    # closed it.
    for node in list(body.find_all(string=EMAIL_RE)):
        parent = node.parent
        if parent is None:
            continue
        siblings = list(parent.children)
        if node not in siblings:
            continue

        idx = siblings.index(node)
        start = 0
        for i in range(idx - 1, -1, -1):
            if getattr(siblings[i], "name", None) == "br":
                start = i + 1
                break

        end = idx
        if idx + 1 < len(siblings) and getattr(siblings[idx + 1], "name", None) == "br":
            end = idx + 1

        for victim in siblings[start:end + 1]:
            victim.extract()

    # Belt and braces. An address somewhere this archive does not currently put
    # one -- inside a table cell, say -- still has to go, even if the prose
    # around it then reads a little short. verify.py fails on any address that
    # reaches the output, so this branch is what keeps a future source edit
    # from turning that check into a hard stop.
    for node in list(body.find_all(string=EMAIL_RE)):
        node.replace_with(EMAIL_RE.sub("", node))


def enhance(fragment, lang, h1):
    """Apply every structural fix to one page's content fragment."""
    soup = BeautifulSoup(fragment, "lxml")
    body = soup.body or soup
    _drop_duplicate_title(body, h1)
    _headings(body, lang)
    _sprite_alt(body)
    _icon_links(body, lang)
    _tables(body, lang)
    _redact_emails(body)
    return body.decode_contents().strip()
