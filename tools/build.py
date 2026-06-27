#!/usr/bin/env python3
"""Rebuild the Digimon World fan-site as a clean, modern static site.

Source: pages recovered from the Wayback Machine (saetta.free.fr/DigimonWorld),
a now-defunct PHP fan-site (index.php?page=X[&evol=Y]). Each archived page =
shared chrome + one content cell. We extract that cell, rewrite legacy links to
static .html, and wrap everything in one modern HTML5 + responsive template.

Three pages relied on a JS hover widget whose data lives in hidden `pop*` divs
(full digivolution tree, per-digimon techniques). We render those hidden cards
as visible, accessible content instead — no JavaScript required.
"""
import re
import os
import html
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)          # tools/ -> repository root
RAW = os.path.join(REPO, "sources", "raw")
OUT = REPO                            # generated pages live at the repo root

# (raw page name, output slug, nav label)
PAGES = [
    ("Accueil",       "index",          "Accueil"),
    ("Histoire",      "histoire",       "Histoire"),
    ("Solution",      "solution",       "Solution"),
    ("Digivolution",  "digivolution",   "Digivolution"),
    ("Techniques",    "techniques",     "Techniques"),
    ("Objets",        "objets",         "Objets digivolutifs"),
    ("Magasins",      "magasins",       "Magasins"),
    ("Arene",         "arene",          "Arène de combat"),
    ("Peche",         "peche",          "Pêche"),
    ("Chasse",        "chasse",         "Chasse au trésor"),
    ("Cartes",        "cartes",         "Cartes"),
    ("Medailles",     "medailles",      "Médailles"),
    ("Emulation",     "emulation",      "Émulation"),
    ("AstucesAR",     "astuces",        "Codes & Astuces"),
    ("Download",      "telechargements","Téléchargements"),
    ("Participation", "participation",  "Participation"),
    ("Contact",       "contact",        "Contact"),
]

LINKMAP = {raw.lower(): (slug + ".html") for raw, slug, _ in PAGES}
LINKMAP["news"] = "index.html"

def map_internal_href(href):
    h = html.unescape(href).strip()
    if h.rstrip("/").endswith("DigimonWorld"):
        return "index.html"
    m = re.search(r"index\.php\?page=([A-Za-z0-9_]+)", h, re.I)
    if m:
        return LINKMAP.get(m.group(1).lower(), "index.html")
    if h in ("index.php", "index"):
        return "index.html"
    return None

def load(path):
    with open(path, "rb") as f:
        return BeautifulSoup(f.read().decode("iso-8859-1"), "lxml")

# original referenced a few sprites by an alternate (typo) romanization,
# and hotlinked two history images from another (now-dead) site -> localized
IMG_ALIAS = {
    "id2/Mojyamon.gif": "id2/Moyjamon.gif",
    "http://digitalmonsters.free.fr/images/saison_un/saison/01.jpg": "images/histoire_saison_01.jpg",
    "http://digitalmonsters.free.fr/images/saison_un/saison/02.jpg": "images/histoire_saison_02.jpg",
}

def fix_imgs(scope):
    """Trim stray whitespace in src, remap typo sprites, localize hotlinks."""
    for img in scope.find_all("img", src=True):
        src = img["src"].strip()
        src = IMG_ALIAS.get(src, src)
        img["src"] = src

def style_rules(soup):
    rules, seen = [], set()
    for st in soup.find_all("style"):
        for m in re.finditer(r"\.Style\d+\s*\{[^}]*\}", st.get_text()):
            r = re.sub(r"\s+", " ", m.group(0)).strip()
            key = r.split("{")[0].strip()
            if key not in seen:
                seen.add(key); rules.append(r)
    return rules

def clean_cell(cell, drop_lead_title=True):
    """Strip chrome, rewrite links, drop a leading duplicate title div."""
    for tag in cell.find_all(["style", "title", "script"]):
        tag.decompose()
    fix_imgs(cell)
    for a in cell.find_all("a", href=True):
        new = map_internal_href(a["href"])
        if new is not None:
            a["href"] = new
        if a.get("rel"):
            del a["rel"]
    if drop_lead_title:
        for el in cell.find_all(["p", "div"], recursive=True):
            txt = el.get_text(strip=True)
            if txt == "":
                continue
            if (el.name == "div" and el.get("align") == "center"
                    and len(txt) <= 40 and not el.find("a") and not el.find("img")):
                el.decompose()
            break
    for p in cell.find_all("p"):
        if p.get_text(strip=True).replace("\xa0", "") == "" and not p.find(["img", "a", "br"]):
            p.decompose()

def content_cell(soup):
    return soup.find_all("title")[1].find_parent("td")

def generic(path):
    soup = load(path)
    rules = style_rules(soup)
    cell = content_cell(soup)
    clean_cell(cell)
    return cell.decode_contents().strip(), rules

# ---- special: pop-card pages (Digivolution, Techniques) -------------------

def pop_cards(path, tiers, intro):
    """Render hidden pop* data divs as visible cards grouped by tier."""
    soup = load(path)
    rules = style_rules(soup)
    cell = content_cell(soup)
    fix_imgs(cell)
    # rewrite links inside cards, neutralize to plain text targets
    for a in cell.find_all("a", href=True):
        new = map_internal_href(a["href"])
        if new is not None:
            a["href"] = new
    parts = [intro]
    for cls, label in tiers:
        divs = cell.find_all("div", class_=cls)
        if not divs:
            continue
        parts.append(f'<h2 class="tier">{html.escape(label)} '
                     f'<span class="count">({len(divs)})</span></h2>')
        parts.append('<div class="cards">')
        for d in divs:
            d.attrs.pop("id", None)
            d["class"] = ["card", cls]
            for t in d.find_all(["script", "style"]):
                t.decompose()
            parts.append(str(d))
        parts.append('</div>')
    return "\n".join(parts), rules

# ---- special: Codes & Astuces (two archived sub-tabs) ---------------------

def astuces():
    out = []
    rules = []
    for sub, label in [("AstucesAR_Astuces", "Astuces"),
                       ("AstucesAR_AR", "Codes Action Replay")]:
        soup = load(os.path.join(RAW, "evol", sub + ".html"))
        rules += style_rules(soup)
        cell = content_cell(soup)
        # drop the leading sub-nav (centered div carrying the tab links)
        lead = cell.find("div", align="center")
        if lead and lead.find("a"):
            lead.decompose()
        clean_cell(cell, drop_lead_title=True)
        out.append(f'<section class="sub"><h2>{html.escape(label)}</h2>\n'
                   f'{cell.decode_contents().strip()}\n</section>')
    # de-dup style rules
    seen, uniq = set(), []
    for r in rules:
        k = r.split("{")[0].strip()
        if k not in seen:
            seen.add(k); uniq.append(r)
    return "\n".join(out), uniq

DIGI_TIERS = [
    ("poptrain", "Digimon de départ"),
    ("popchamp", "Champions"),
    ("popult",   "Ultimes"),
    ("popult2",  "Méga"),
]

# ---- template -------------------------------------------------------------

TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Digimon World</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="style.css">
<style>{page_styles}</style>
</head>
<body>
<a class="skip" href="#content">Aller au contenu</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="index.html">Digimon&nbsp;World <span>— Solution &amp; Guide</span></a>
    <button class="nav-toggle" aria-label="Menu" aria-expanded="false">☰</button>
  </div>
</header>
<nav class="site-nav" aria-label="Navigation principale">
  <ul class="wrap">
{nav}
  </ul>
</nav>
{hero}
<main id="content" class="wrap">
  <article class="page">
    <h1>{title}</h1>
{content}
  </article>
</main>
<footer class="site-footer">
  <div class="wrap">
    <p>Fan-site dédié à <strong>Digimon World</strong> (PlayStation). Contenu original de saetta.free.fr,
       récupéré depuis la <a href="https://web.archive.org/web/2023/http://saetta.free.fr/DigimonWorld/">Wayback Machine</a>.</p>
    <p class="muted">Digimon est une marque de Bandai. Site non officiel, à but informatif et de préservation.</p>
  </div>
</footer>
<script src="nav.js"></script>
</body>
</html>
"""

DESC = ("Solution complète et guide du jeu Digimon World (PSX) : soluce pas à pas, "
        "arbre de digivolution, techniques, objets, magasins, médailles, pêche et codes.")

HERO = """<section class="hero wrap" aria-label="Digimon World">
  <img src="images/banton2.gif" width="808" height="157" alt="Digimon World — bannière du site original de Saetta">
  <p class="tag">La solution complète et le guide du jeu <strong>Digimon World</strong> sur PlayStation :
     soluce pas à pas, arbre de digivolution, techniques, objets, magasins et astuces.</p>
  <div class="cta">
    <a class="btn btn-primary" href="solution.html">Lire la solution</a>
    <a class="btn btn-ghost" href="digivolution.html">Arbre de digivolution</a>
  </div>
</section>"""

# Curated home content (the original homepage was full of dead 2008 news about a
# forum that no longer exists — replaced with a preservation note + useful intro).
HOME_CARDS = [
    ("solution", "📖", "Solution", "Le walkthrough complet, pas à pas."),
    ("digivolution", "🥚", "Digivolution", "L'arbre d'évolution des 55 Digimon et leurs conditions."),
    ("techniques", "⚔️", "Techniques", "Les techniques apprises par chaque Digimon."),
    ("objets", "🎒", "Objets", "Les objets digivolutifs."),
    ("magasins", "🏪", "Magasins", "Ce qu'on trouve dans chaque boutique."),
    ("arene", "🏟️", "Arène de combat", "Le fonctionnement de l'arène."),
    ("peche", "🎣", "Pêche", "Tout sur la pêche."),
    ("astuces", "💡", "Codes & Astuces", "Conseils et codes Action Replay."),
]

def home_content():
    cards = "\n".join(
        f'    <a class="sec-card" href="{slug}.html"><span class="ic">{ic}</span>'
        f'<h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></a>'
        for slug, ic, t, d in HOME_CARDS
    )
    return f"""<div class="callout">
  <strong>Site de préservation.</strong> Ceci est une restauration de
  <em>saetta.free.fr/DigimonWorld</em>, un site de fans français aujourd'hui disparu (le PHP
  ayant été coupé sur les pages perso de Free). Le contenu a été récupéré depuis la
  <a href="https://web.archive.org/web/2023/http://saetta.free.fr/DigimonWorld/">Wayback Machine</a>
  puis remis en forme. Le forum et le livre d'or d'origine n'existent plus et ont été retirés.
</div>
<p><strong>Digimon World</strong> (PlayStation, 1999) est un jeu où l'on élève un Digimon, un peu
  à la manière d'un tamagotchi, pour le rendre assez fort et aider les Digimon de File Island à
  reconstruire leur cité. Ce guide rassemble tout ce qu'il faut pour le terminer.</p>
<div class="callout" style="background:#fdecec;border-color:#f3b6b6;border-left-color:#d6453f;color:#6a2420">
  <strong>À savoir :</strong> un bug présent sur plusieurs versions françaises empêche d'entrer dans la
  forteresse d'Ogremon (Grand Canyon). Whamon et Shellmon deviennent alors irrécupérables ; on peut
  tout de même finir le jeu, mais c'est plus difficile.
</div>
<h2>Par où commencer</h2>
<div class="sections">
{cards}
</div>
<h2>Bien élever son Digimon</h2>
<ul>
  <li>Ne le nourris que lorsqu'il le demande : trop de nourriture, ou certains types, peuvent le rendre malade.</li>
  <li>Emmène-le aux toilettes dès qu'il le demande, sinon il perd en bonheur et tu perds de l'autorité.</li>
  <li>Laisse-le dormir quand il le demande : il récupère alors tous ses PV et PM.</li>
  <li>Fatigué ? Fais-le reposer une heure auprès de Punimon ou Centarumon en ville.</li>
  <li>Blessé au combat : utilise vite un bandage. Malade : un médicament, ou Centarumon pour 300 Bits.</li>
</ul>"""

def build_nav(active_slug):
    items = []
    for raw, slug, label in PAGES:
        href = ("index.html" if slug == "index" else slug + ".html")
        cls = ' class="active"' if slug == active_slug else ""
        items.append(f'    <li><a href="{href}"{cls}>{html.escape(label)}</a></li>')
    return "\n".join(items)

DIGI_INTRO = ('<p>Arbre de digivolution complet : survolez les conditions pour chaque Digimon. '
              'Couleur = stade d\'évolution. <em>Erreurs de soin</em> = nombre d\'erreurs toléré, '
              '<em>Poids</em> = poids cible, plus les conditions de statistiques.</p>')
TECH_INTRO = ('<p>Techniques apprises par chaque Digimon, ainsi que leur Technique Spéciale.</p>')

def main():
    os.makedirs(OUT, exist_ok=True)
    for raw, slug, label in PAGES:
        hero = ""
        if slug == "index":
            content, rules, hero, label = home_content(), [], HERO, "Bienvenue"
        elif raw == "Digivolution":
            content, rules = pop_cards(os.path.join(RAW, "Digivolution.html"), DIGI_TIERS, DIGI_INTRO)
        elif raw == "Techniques":
            content, rules = pop_cards(os.path.join(RAW, "Techniques.html"),
                                       [("poptech", "Techniques par Digimon")], TECH_INTRO)
        elif raw == "AstucesAR":
            content, rules = astuces()
        else:
            content, rules = generic(os.path.join(RAW, raw + ".html"))
        outname = ("index.html" if slug == "index" else slug + ".html")
        page = TEMPLATE.format(
            title=html.escape(label), desc=html.escape(DESC),
            page_styles=" ".join(rules), nav=build_nav(slug), content=content, hero=hero,
        )
        with open(os.path.join(OUT, outname), "w", encoding="utf-8") as f:
            f.write(page)
        print(f"{raw:14s} -> {outname:22s} ({len(content):6d} bytes)")

if __name__ == "__main__":
    main()
