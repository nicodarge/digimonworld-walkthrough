# Digimon World — Solution & Guide

A restored static copy of the French fan-site **`saetta.free.fr/DigimonWorld`**, a
walkthrough and guide for *Digimon World* (PlayStation, 1999). The original was a
PHP site on a free.fr personal space; PHP was eventually disabled there, leaving
the site broken. This repository rebuilds it as a clean, modern, static site from
the [Wayback Machine](https://web.archive.org/web/2023/http://saetta.free.fr/DigimonWorld/)
snapshots (mostly 2023-04-29).

## What it contains

17 pages recovered in full, including:

- **Solution** — the complete step-by-step walkthrough.
- **Digivolution** — the full evolution tree (55 Digimon: Rookies, Champions,
  Ultimates, Mega) with conditions (weight, care mistakes, stat requirements).
- **Techniques** — techniques learned by each Digimon and their special move.
- Objects, Shops, Battle Arena, Fishing, Treasure Hunt, Cards, Medals,
  Emulation, Action Replay codes & tips, downloads, history and contact.

## What changed vs. the original

- HTML 4 / iso-8859-1 → **HTML5 / UTF-8**, responsive layout, mobile menu.
- The dynamic `index.php?page=X` routing → plain static `.html` files.
- The Digivolution and Techniques pages relied on a JavaScript hover widget whose
  data lived in hidden `pop*` `<div>`s. Those are now rendered as **visible,
  accessible cards** — no JavaScript required to read the data.
- Dead PHP artifacts (the guestbook, which the original author had already
  removed) were dropped. Some external links in the content point to sites that
  no longer exist; they are kept as-is for fidelity.

## Structure

```
*.html         # generated pages (index.html = home)
style.css      # modern responsive styles
nav.js         # mobile nav toggle + wide-table scroll wrapping
id2/           # Digimon sprites
images/ design/ screenshots/ css/ js/ Download/   # original assets
sources/       # the restoration's source of truth
  raw/         #   archived pages captured from the Wayback Machine
  raw/evol/    #   archived &evol= sub-pages
  wayback-*.txt#   CDX manifests (which URLs/timestamps were captured)
tools/
  build.py     # regenerates the *.html pages from sources/raw
  requirements.txt
```

The site is plain static files — open `index.html` locally, or serve the folder
with any static web server.

## Rebuilding

The HTML pages are generated from the archived sources in `sources/raw`:

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -r tools/requirements.txt
python tools/build.py
```

Editing the archived content or the build script and re-running regenerates the
site deterministically.

## Credits & legal

Original content and walkthrough by the author of `saetta.free.fr/DigimonWorld`.
This is a non-commercial preservation copy with attribution. *Digimon* is a
trademark of Bandai; this is an unofficial fan resource for informational and
archival purposes.
