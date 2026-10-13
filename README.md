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
404.html          # not-found page, bilingual
favicon.svg       # site icon
robots.txt        # crawler policy, points at the sitemap
sitemap.xml       # every page of both language trees
style.css         # modern responsive styles (shared)
archive.css       # generated: the archive's own .StyleNN rules, one namespace
                  #   per page — the same class name means different things on
                  #   different pages, so they cannot share a global stylesheet
                  #   unprefixed. Emitted by build.py, do not edit.
root.css          # styles for the language landing only
lang.js           # language redirect for the landing page
nav.js            # mobile nav toggle + wide-table scroll wrapping (shared)
id2/              # Digimon sprites
images/           # original assets, plus og-card.png (the share card)
design/ screenshots/ css/ js/ Download/           # original assets (shared)
sources/          # the restoration's source of truth
  raw/            #   archived pages captured from the Wayback Machine
  raw/evol/       #   archived &evol= sub-pages
  fragments/      #   per-page content fragments: <slug>.fr.html + <slug>.en.html
  wayback-*.txt   #   CDX manifests (which URLs/timestamps were captured)
tools/
  build.py        # regenerates fr/ + en/ from sources/, plus the files above
  enhance.py      # turns the archived 2003 markup into accessible, responsive
                  #   HTML: banner images become real headings, sprites get an
                  #   alt, header rows become <th> and stamp data-label on each
                  #   cell for the mobile card layout. Imported by build.py.
  verify.py       # checks links, assets, i18n parity, leftover legacy markup
  make_og_image.py  # composes images/og-card.png, the 1200x630 share card.
                  #   Run by hand, never by build.py: its output is committed,
                  #   and wiring it in would make the CI reproducibility gate
                  #   depend on Pillow rendering identically across versions.
  requirements.txt
.github/workflows/ci.yml   # build-reproducibility + verify + gate
.pre-commit-config.yaml    # same checks locally before each commit
renovate.json              # dependency updates (Renovate)
```

## Rebuilding & verifying

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -r tools/requirements.txt
python tools/build.py     # regenerate fr/ and en/ from sources/
python tools/verify.py    # fail on any broken link, missing asset, parity gap
```

The build is deterministic: same sources → identical output. CI rebuilds and
fails if the committed pages are stale, then runs `verify.py`, then the tests.
Install the local checks with `pre-commit install`.

## Tests

```sh
pip install -r tools/requirements-dev.txt
pytest tests/ -q
```

Two kinds, and the second is the point.

`tests/test_enhance.py` and `tests/test_build.py` cover the transforms: the
table conversion, the icon links, the sprite alts, the link rewriting, and the
email redaction — where each case names what must **survive**, not only what
must go. The redaction deletes content, and an over-deletion is silent:
`verify.py` fails on an address that survives, never on a paragraph that
vanished.

`tests/test_ci.py` asserts every workflow job runs on a GitHub-hosted image.
This repository is public and its workflows are triggered by pull requests,
including from forks — a self-hosted runner would execute that code on the
owner's own machine, with whatever credentials the runner's user carries.
Nothing here needs that, and the guard is fed `self-hosted`, a label list and a
runner-group name to check it refuses them.

`tests/test_verify.py` feeds every `verify.py` check the input it exists to
refuse — a duplicate description, a missing canonical, an image with no alt, a
broken anchor, a hotlinked image, an unlabelled card table, an `og:image` that
is relative or on another host or the wrong size — and asserts it fails. A
check only ever shown valid input proves nothing about what it lets through.
`test_the_unmutated_baseline_is_clean` is what stops that file passing
vacuously if the fixtures drift.

The suite is measured by mutation rather than trusted: breaking the redaction's
`<br>` boundary, its whitespace-tolerant forward scan, the `og:image` dimension
comparison, its absolute-URL requirement, or the redaction call itself each
makes tests fail. That is what says the tests can catch a regression, rather
than merely pass.

## Dependency updates

`renovate.json` configures Renovate, which runs from the scheduled workflow in
the Puppet repository (this repository must be listed in its
`.github/renovate-global.json`), not from an app installed here.
`enabledManagers` is an allowlist, so an ecosystem added to the repository is
ignored until it is listed. Renovate enables GitHub auto-merge on its own pull
requests (`platformAutomerge`), so GitHub merges each one once the required
checks pass; the `gate` CI job needs every other job, so it is the one check
for the ruleset to require. The `pre-commit` CI job runs every hook, so a hook
bump is exercised before it merges. The Puppet repository's bump review and merge workflows are not used
here: they need a self-hosted runner, which `tests/test_ci.py` forbids on this
public repository.

## Hosting

The site is served at <https://digimon-world.groniko.fr>, self-hosted rather
than on GitHub Pages. Delivery is pull-only: the web server clones this
repository over anonymous HTTPS and keeps it at the tip of `main`, so a merge
reaches the site on the server's next configuration run. Nothing is pushed from
CI and no credential exists on either side — which is why this repository is
public.

`SITE_URL` in `tools/build.py` is that origin. It is baked into every canonical
link, `og:url` and sitemap entry, so it is the one place to change if the site
ever moves.

## Credits & legal

Original content and walkthrough by the author of `saetta.free.fr/DigimonWorld`.
This is a non-commercial preservation copy with attribution. *Digimon* is a
trademark of Bandai; this is an unofficial fan resource for informational and
archival purposes.
