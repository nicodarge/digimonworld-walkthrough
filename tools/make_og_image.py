#!/usr/bin/env python3
"""Compose images/og-card.png, the 1200x630 image social platforms preview.

Run by hand, not by build.py, and deliberately so. The output is committed as a
static asset: wiring it into the build would put Pillow in the CI install and
make the reproducibility gate depend on Pillow rendering pixel-identically
across versions, which it does not promise. Regenerate only when the banner or
the wording changes.

    pip install pillow && python tools/make_og_image.py

Why it exists: og:image pointed straight at images/banton2.gif, the site
banner, which is 808x157 -- roughly 5.1:1 where share cards expect 1.91:1. Every
preview cropped most of it away. This places the banner on the site's own navy
with room around it, so the card is read at the ratio it is served at.
"""
import os

from PIL import Image, ImageDraw, ImageFont, ImageSequence

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

W, H = 1200, 630
NAVY = (11, 31, 58)
NAVY_2 = (17, 41, 74)
AMBER = (255, 138, 31)
INK = (238, 243, 248)
MUTED = (174, 191, 208)

BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REGULAR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def font(path, size):
    """Load a font, or say which package is missing rather than 'cannot open resource'.

    Liberation Sans is metric-compatible with Arial, which is what the site's
    own font stack falls back to, so the card matches the pages. These paths are
    Debian's; a maintainer on another OS has to point them at a local copy, and
    the bare OSError Pillow raises does not hint at any of that.
    """
    if not os.path.exists(path):
        raise SystemExit(
            f"font not found: {path}\n"
            "Install fonts-liberation (Debian/Ubuntu), or edit BOLD/REGULAR at "
            "the top of this script to point at a local Liberation Sans."
        )
    return ImageFont.truetype(path, size)


# The banner is a 10-frame animation of a lightning effect. Frames 4 and 5 wash
# the title in purple and read badly at card size; frame 0 has the cleanest
# lettering, so the card is not a lottery over whichever frame a decoder picks.
BANNER_FRAME = 0


def banner():
    src = Image.open(os.path.join(REPO, "images", "banton2.gif"))
    for i, frame in enumerate(ImageSequence.Iterator(src)):
        if i == BANNER_FRAME:
            return frame.convert("RGBA")
    raise SystemExit(f"banner has no frame {BANNER_FRAME}")


def centred(draw, text, face, y, fill):
    """Draw text horizontally centred, y being its visual top.

    The parameter is `face`, not `font`: that name belongs to the loader above,
    and shadowing a module-level helper with a parameter is how the same mistake
    reached verify.py in this branch.
    """
    left, top, right, bottom = draw.textbbox((0, 0), text, font=face)
    draw.text(((W - (right - left)) / 2 - left, y - top), text, font=face, fill=fill)
    return bottom - top


def main():
    card = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(card)

    # Vertical wash, navy at the edges to navy-2 in the middle. Flat navy under
    # a bright illustration reads as a screenshot on a slide; this gives the
    # banner something to sit in.
    for y in range(H):
        t = 1 - abs((y / H) - 0.5) * 2
        draw.line([(0, y), (W, y)],
                  fill=tuple(int(a + (b - a) * t) for a, b in zip(NAVY, NAVY_2)))

    art = banner()
    art_w = 1040
    art_h = round(art.height * art_w / art.width)
    art = art.resize((art_w, art_h), Image.LANCZOS)
    art_x, art_y = (W - art_w) // 2, 96

    # A hairline frame so the illustration has an edge against the background
    # rather than bleeding into it.
    draw.rectangle([art_x - 1, art_y - 1, art_x + art_w, art_y + art_h],
                   outline=(60, 90, 125))
    card.paste(art, (art_x, art_y), art)

    # No title line above the banner: the banner already reads DIGIMON WORLD in
    # letters twice that size, and setting it again turns the card into a
    # caption of itself. The text below says what the banner cannot -- what the
    # site is, and where it lives.
    headline = font(BOLD, 46)
    meta = font(REGULAR, 28)
    small = font(REGULAR, 25)

    bar_y = art_y + art_h + 52
    draw.rectangle([(W - 72) // 2, bar_y, (W + 72) // 2, bar_y + 5], fill=AMBER)

    centred(draw, "Solution & Guide  ·  Walkthrough & Guide", headline, bar_y + 40, INK)
    centred(draw, "PlayStation, 1999  ·  Français / English", meta, bar_y + 104, MUTED)
    centred(draw, "digimon-world.groniko.fr", small, bar_y + 156, AMBER)

    out = os.path.join(REPO, "images", "og-card.png")
    card.save(out, optimize=True)
    print(f"wrote {out} ({card.size[0]}x{card.size[1]}, "
          f"{os.path.getsize(out) // 1024} KiB)")


if __name__ == "__main__":
    main()
