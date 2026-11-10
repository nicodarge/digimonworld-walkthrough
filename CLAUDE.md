# CLAUDE.md - digimonworld-walkthrough

Static, bilingual (FR/EN) restoration of the fan site `saetta.free.fr/DigimonWorld`, served at
`digimon-world.groniko.fr`. The README has the structure, the build and the test design.

## Rules

- **Default branch is `main`** (not `production`). The public web server clones it anonymously and follows its
  tip, so a merge goes live on the server's next configuration run.
- **Pages and root files are generated: never edit `fr/`, `en/`, `index.html`, `404.html`, `robots.txt`,
  `sitemap.xml` or `archive.css`.** Run `python tools/build.py` and commit the result; CI fails when committed
  pages are stale.
- **French is derived, English is hand-written.** `build.py` rewrites every `sources/fragments/<slug>.fr.html`
  from `sources/raw/` through `tools/enhance.py` on each build, so a hand edit there is lost: change the
  transforms in `tools/`. Only `sources/fragments/<slug>.en.html` is edited by hand; keep parity with the
  French page.
- `sources/raw/` and `sources/wayback-*.txt` are the Wayback captures: read-only evidence.
- English place names follow the official Digimon World (PSX) names. `tools/apply_place_names.py` was a
  run-once normaliser already applied to the `.en.html` fragments: new English text uses the same names.
- The `build-site` commit hook rebuilds on a change under `sources/` or to `build.py`/`enhance.py`. An edit to
  `style.css`, `nav.js`, `lang.js` or `root.css` changes content hashes in every page and does not fire it:
  run `python tools/build.py` by hand.
- `tools/make_og_image.py` is run by hand and its output (`images/og-card.png`) committed; never wire it into
  `build.py` (reproducibility gate).
- `SITE_URL` in `tools/build.py` is baked into every canonical link, `og:url` and sitemap entry.
- Email redaction deletes content: a test for it names what must survive, not only what must go.
- **CI jobs run on GitHub-hosted runners on purpose**: the repository is public and takes fork PRs, so
  `tests/test_ci.py` refuses `self-hosted` labels. Do not move a job to a self-hosted runner.
- Markdown lines are capped at 120 characters (`.markdownlint.json`, `MD013`; code blocks and tables exempt).

## Commands

```sh
pip install -r tools/requirements.txt && python tools/build.py   # regenerate
python tools/verify.py                                          # links, assets, i18n parity
pip install -r tools/requirements-dev.txt && pytest tests/ -q    # tests
```

Verification and tests are CI's job (`.github/workflows/ci.yml`; the `gate` job is the required check): push
and read CI. Commit-stage hooks only fix files and rebuild; `check-yaml` and `markdownlint` are `manual` (CI
only), `check-merge-conflict` runs in both. Every hook names its `stages`.

## Merging

Squash-merge once `gate` is green. Renovate PRs enable GitHub auto-merge themselves (`platformAutomerge`); the
Puppet bump-review/bump-merge workflows are not used here.
