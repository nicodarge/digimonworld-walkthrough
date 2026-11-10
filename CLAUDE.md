# CLAUDE.md - digimonworld-walkthrough

Static, bilingual (FR/EN) restoration of the fan site `saetta.free.fr/DigimonWorld`, served at `digimon-world.groniko.fr`. The README has the structure, the build and the test design.

## Rules

- **Default branch is `main`** (not `production`). The public web server clones it anonymously and follows its tip, so a merge goes live on the server's next configuration run.
- **`fr/`, `en/`, `archive.css`, `sitemap.xml` and the rest of the build output are generated: never edit them.** Change `sources/fragments/<slug>.fr.html` and `<slug>.en.html` (French is the source of truth, English must keep parity) or `tools/`, then run `python tools/build.py` and commit the regenerated files. The `build-site` commit hook does it for a change under `sources/` or `tools/build.py`/`tools/enhance.py`; CI fails when committed pages are stale.
- `sources/raw/` and `sources/wayback-*.txt` are the Wayback captures: read-only evidence.
- English place names follow the official Digimon World (PSX) names (`tools/apply_place_names.py`), not literal translations.
- `tools/make_og_image.py` is run by hand and its output (`images/og-card.png`) committed; never wire it into `build.py` (reproducibility gate).
- `SITE_URL` in `tools/build.py` is baked into every canonical link, `og:url` and sitemap entry.
- Email redaction deletes content: a test for it names what must survive, not only what must go.
- **CI jobs run on GitHub-hosted runners on purpose**: the repository is public and takes fork PRs, so `tests/test_ci.py` refuses `self-hosted` labels. Do not move a job to a self-hosted runner.

## Commands

```sh
pip install -r tools/requirements.txt && python tools/build.py   # regenerate
python tools/verify.py                                          # links, assets, i18n parity
pip install -r tools/requirements-dev.txt && pytest tests/ -q    # tests
```

Verification and tests are CI's job (`.github/workflows/ci.yml`, the `gate` job is the required check): push and read CI instead of running them before every commit. Commit-stage hooks only fix files and rebuild; `check-yaml` and `markdownlint` are `manual` (CI only), `check-merge-conflict` runs in both. Every hook names its `stages` (`default_stages` is `[pre-commit]`).

## Merging

Squash-merge once `gate` is green. Renovate PRs enable GitHub auto-merge themselves (`platformAutomerge`); the Puppet bump-review/bump-merge workflows are not used here.
