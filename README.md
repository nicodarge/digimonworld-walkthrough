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

## Languages

The site is **bilingual (French / English)** with a language switcher in the
header:

- `index.html` — language landing that redirects to `fr/` or `en/` based on the
  browser, with manual links as a fallback.
- `fr/*.html` — French pages (the original language of the content).
- `en/*.html` — English pages (translated, same structure).

French is the source of truth; English is generated from per-page translation
fragments in `sources/fragments/<slug>.en.html`. Place names use the **official
Digimon World (PSX) English area names** (File City, Factorial Town, Dragon Eye
Lake, Misty Trees, Mount Infinity, Speedy Time Zone, …) rather than literal
translations of the French fan-site names — see `tools/apply_place_names.py`.

## Structure

```text
index.html        # language landing (redirect FR/EN)
fr/  en/          # the pages, one tree per language
style.css         # modern responsive styles (shared)
nav.js            # mobile nav toggle + wide-table scroll wrapping (shared)
id2/              # Digimon sprites
images/ design/ screenshots/ css/ js/ Download/   # original assets (shared)
sources/          # the restoration's source of truth
  raw/            #   archived pages captured from the Wayback Machine
  raw/evol/       #   archived &evol= sub-pages
  fragments/      #   per-page content fragments: <slug>.fr.html + <slug>.en.html
  wayback-*.txt   #   CDX manifests (which URLs/timestamps were captured)
tools/
  build.py        # regenerates fr/ + en/ from sources/
  verify.py       # checks links, assets, i18n parity, leftover legacy markup
  requirements.txt
.github/workflows/ci.yml   # build-reproducibility + verify + Pages deploy
.pre-commit-config.yaml    # same checks locally before each commit
```

## Rebuilding & verifying

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -r tools/requirements.txt
python tools/build.py     # regenerate fr/ and en/ from sources/
python tools/verify.py    # fail on any broken link, missing asset, parity gap
```

The build is deterministic: same sources → identical output. CI rebuilds and
fails if the committed pages are stale, then runs `verify.py`, then deploys to
GitHub Pages. Install the local checks with `pre-commit install`.

## Credits & legal

Original content and walkthrough by the author of `saetta.free.fr/DigimonWorld`.
This is a non-commercial preservation copy with attribution. *Digimon* is a
trademark of Bandai; this is an unofficial fan resource for informational and
archival purposes.
