#!/usr/bin/env python3
"""Rebuild the Digimon World fan-site as a clean, modern, bilingual static site.

Source: pages recovered from the Wayback Machine (saetta.free.fr/DigimonWorld),
a now-defunct PHP fan-site (index.php?page=X[&evol=Y]). Each archived page =
shared chrome + one content cell. We extract that cell, rewrite legacy links to
static .html, and wrap everything in one modern HTML5 + responsive template.

Output layout:
  /index.html        language landing (redirect FR/EN)
  /fr/*.html         French pages   (original language)
  /en/*.html         English pages  (translated content fragments)
  /style.css /nav.js shared, referenced as ../ from inside /fr and /en
  /id2 /images ...   shared assets, referenced as ../ from inside /fr and /en

The extracted page content (the part that carries real prose) is written to
sources/fragments/<slug>.fr.html. Translators produce <slug>.en.html with the
same HTML structure; the English build consumes those. Chrome (nav, hero,
footer, home page, titles) is translated inline via the STRINGS table below.

Three pages relied on a JS hover widget whose data lives in hidden `pop*` divs
(full digivolution tree, per-digimon techniques). We render those hidden cards
as visible, accessible content instead — no JavaScript required.
"""
import re
import os
import html
from bs4 import BeautifulSoup

from enhance import enhance

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)          # tools/ -> repository root
RAW = os.path.join(REPO, "sources", "raw")
FRAG = os.path.join(REPO, "sources", "fragments")
OUT = REPO
LANGS = ("fr", "en")

# raw page name, output slug, FR nav label, EN nav label, FR h1, EN h1
PAGES = [
    ("Accueil",       "index",          "Accueil",         "Home",         "Bienvenue",          "Welcome"),
    ("Histoire",      "histoire",       "Histoire",        "Story",        "Histoire",           "Story"),
    ("Solution",      "solution",       "Solution",        "Walkthrough",  "Solution",           "Walkthrough"),
    ("Digivolution",  "digivolution",   "Digivolution",    "Digivolution", "Digivolution",       "Digivolution"),
    ("Techniques",    "techniques",     "Techniques",      "Techniques",   "Techniques",         "Techniques"),
    ("Objets",        "objets",         "Objets",          "Items",        "Objets digivolutifs","Digivolution Items"),
    ("Magasins",      "magasins",       "Magasins",        "Shops",        "Magasins",           "Shops"),
    ("Arene",         "arene",          "Arène",           "Arena",        "Arène de combat",    "Battle Arena"),
    ("Peche",         "peche",          "Pêche",           "Fishing",      "Pêche",              "Fishing"),
    ("Chasse",        "chasse",         "Chasse au trésor","Treasure Hunt","Chasse au trésor",   "Treasure Hunt"),
    ("Cartes",        "cartes",         "Cartes",          "Cards",        "Cartes",             "Cards"),
    ("Medailles",     "medailles",      "Médailles",       "Medals",       "Médailles",          "Medals"),
    ("Emulation",     "emulation",      "Émulation",       "Emulation",    "Émulation",          "Emulation"),
    ("AstucesAR",     "astuces",        "Codes & Astuces", "Codes & Tips", "Codes & Astuces",    "Codes & Tips"),
    ("Download",      "telechargements","Téléchargements", "Downloads",    "Téléchargements",    "Downloads"),
    ("Participation", "participation",  "Participation",   "Contribute",   "Participation",      "Contribute"),
    ("Contact",       "contact",        "Contact",         "Contact",      "Contact",            "Contact"),
]

# Canonical origin. Every absolute URL the site emits (canonical, hreflang,
# Open Graph, sitemap) is built from it, so moving hosts is a one-line change.
SITE_URL = "https://digimon-world.groniko.fr"
REPO_URL = "https://github.com/nicodarge/digimonworld-walkthrough"

# One description per page. A single shared description across 34 pages is a
# duplicate-content signal, and it is what search engines quote under the title.
DESCRIPTIONS = {
    "index": ("Guide complet de Digimon World (PlayStation) : solution pas à pas, arbre de "
              "digivolution, techniques, objets et astuces. Site de préservation.",
              "Complete guide to Digimon World (PlayStation): step-by-step walkthrough, "
              "digivolution tree, techniques, items and tips. A preservation site."),
    "histoire": ("L'histoire de Digimon World et de File Island, et le contexte de la série "
                 "Digimon à l'époque du jeu.",
                 "The story of Digimon World and File Island, and the background of the Digimon "
                 "series at the time of the game."),
    "solution": ("La solution complète de Digimon World, zone par zone : Capitale, Forêt "
                 "Originelle, Grand Canyon, Mont Eternel, et le recrutement de chaque Digimon.",
                 "The complete Digimon World walkthrough, area by area: File City, Native Forest, "
                 "Great Canyon, Mount Infinity, and how to recruit every Digimon."),
    "digivolution": ("L'arbre de digivolution complet des 55 Digimon : conditions de poids, "
                     "erreurs de soin et statistiques requises pour chaque évolution.",
                     "The complete digivolution tree for all 55 Digimon: weight, care mistakes "
                     "and stat requirements for every evolution."),
    "techniques": ("Les techniques apprises par chaque Digimon de Digimon World, ainsi que leur "
                   "Technique Spéciale.",
                   "The techniques each Digimon learns in Digimon World, along with its Special "
                   "Technique."),
    "objets": ("Les objets digivolutifs de Digimon World : en quoi chacun fait évoluer, et où le "
               "trouver.",
               "Digivolution items in Digimon World: what each one evolves into, and where to "
               "find it."),
    "magasins": ("Tous les magasins de Digimon World : emplacement, articles vendus et conditions "
                 "pour les débloquer.",
                 "Every shop in Digimon World: location, goods sold and how to unlock them."),
    "arene": ("L'arène de combat de Digimon World : fonctionnement des tournois, adversaires et "
              "récompenses.",
              "The Battle Arena in Digimon World: how the tournaments work, opponents and "
              "rewards."),
    "peche": ("La pêche dans Digimon World : poissons, appâts, emplacements et ce qu'on en tire.",
              "Fishing in Digimon World: fish, bait, locations and what you get from them."),
    "chasse": ("La chasse au trésor de Digimon World : où creuser et ce que l'on peut y trouver.",
               "The treasure hunt in Digimon World: where to dig and what can be found."),
    "cartes": ("Le jeu de cartes de Digimon World : règles, liste des cartes et comment les "
               "obtenir.",
               "The card game in Digimon World: rules, card list and how to obtain them."),
    "medailles": ("Les médailles de Digimon World : la liste complète et comment débloquer "
                  "chacune d'elles.",
                  "Medals in Digimon World: the complete list and how to unlock each one."),
    "emulation": ("Émuler Digimon World sur PC : émulateurs PlayStation, configuration et "
                  "problèmes connus.",
                  "Emulating Digimon World on PC: PlayStation emulators, setup and known issues."),
    "astuces": ("Astuces et codes Action Replay pour Digimon World, et les bugs connus des "
                "versions françaises.",
                "Tips and Action Replay codes for Digimon World, and the known bugs in the French "
                "releases."),
    "telechargements": ("Les fichiers proposés par le site d'origine de Saetta, conservés dans "
                        "cette copie de préservation.",
                        "The files offered by Saetta's original site, kept in this preservation "
                        "copy."),
    "participation": ("Comment le site d'origine invitait ses lecteurs à contribuer au guide "
                      "Digimon World.",
                      "How the original site invited its readers to contribute to the Digimon "
                      "World guide."),
    "contact": ("Contacter les mainteneurs de cette copie de préservation du guide Digimon World "
                "de Saetta.",
                "Contact the maintainers of this preservation copy of Saetta's Digimon World "
                "guide."),
}

LINKMAP = {raw.lower(): (slug + ".html") for raw, slug, *_ in PAGES}
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

IMG_ALIAS = {
    "id2/Mojyamon.gif": "id2/Moyjamon.gif",
    "http://digitalmonsters.free.fr/images/saison_un/saison/01.jpg": "images/histoire_saison_01.jpg",
    "http://digitalmonsters.free.fr/images/saison_un/saison/02.jpg": "images/histoire_saison_02.jpg",
}

def fix_imgs(scope):
    for img in scope.find_all("img", src=True):
        src = img["src"].strip()
        img["src"] = IMG_ALIAS.get(src, src)

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

def pop_cards(path, tiers, intro):
    soup = load(path)
    rules = style_rules(soup)
    cell = content_cell(soup)
    fix_imgs(cell)
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

def astuces():
    out, rules = [], []
    for sub, label in [("AstucesAR_Astuces", "Astuces"),
                       ("AstucesAR_AR", "Codes Action Replay")]:
        soup = load(os.path.join(RAW, "evol", sub + ".html"))
        rules += style_rules(soup)
        cell = content_cell(soup)
        lead = cell.find("div", align="center")
        if lead and lead.find("a"):
            lead.decompose()
        clean_cell(cell, drop_lead_title=True)
        out.append(f'<section class="sub"><h2>{html.escape(label)}</h2>\n'
                   f'{cell.decode_contents().strip()}\n</section>')
    seen, uniq = set(), []
    for r in rules:
        k = r.split("{")[0].strip()
        if k not in seen:
            seen.add(k); uniq.append(r)
    return "\n".join(out), uniq

DIGI_TIERS = [("poptrain", "Digimon de départ"), ("popchamp", "Champions"),
              ("popult", "Ultimes"), ("popult2", "Méga")]
DIGI_INTRO = ('<p>Arbre de digivolution complet. Couleur = stade d\'évolution. '
              '<em>Erreurs de soin</em> = nombre d\'erreurs toléré, '
              '<em>Poids</em> = poids cible, plus les conditions de statistiques.</p>')
TECH_INTRO = '<p>Techniques apprises par chaque Digimon, ainsi que leur Technique Spéciale.</p>'

def fr_content(raw, slug):
    """The FR content fragment for a non-home page + its inline style rules."""
    if raw == "Digivolution":
        return pop_cards(os.path.join(RAW, "Digivolution.html"), DIGI_TIERS, DIGI_INTRO)
    if raw == "Techniques":
        return pop_cards(os.path.join(RAW, "Techniques.html"),
                         [("poptech", "Techniques par Digimon")], TECH_INTRO)
    if raw == "AstucesAR":
        return astuces()
    return generic(os.path.join(RAW, raw + ".html"))

# ---- home page (hand-authored, per language) ------------------------------

HOME_CARDS = [  # slug, icon, (fr_title, fr_desc), (en_title, en_desc)
    ("solution", "📖", ("Solution", "Le walkthrough complet, pas à pas."),
                       ("Walkthrough", "The complete step-by-step walkthrough.")),
    ("digivolution", "🥚", ("Digivolution", "L'arbre d'évolution des 55 Digimon et leurs conditions."),
                           ("Digivolution", "The evolution tree of all 55 Digimon and their conditions.")),
    ("techniques", "⚔️", ("Techniques", "Les techniques apprises par chaque Digimon."),
                         ("Techniques", "The techniques each Digimon can learn.")),
    ("objets", "🎒", ("Objets", "Les objets digivolutifs."),
                     ("Items", "Digivolution items.")),
    ("magasins", "🏪", ("Magasins", "Ce qu'on trouve dans chaque boutique."),
                       ("Shops", "What each shop sells.")),
    ("arene", "🏟️", ("Arène de combat", "Le fonctionnement de l'arène."),
                     ("Battle Arena", "How the arena works.")),
    ("peche", "🎣", ("Pêche", "Tout sur la pêche."),
                    ("Fishing", "Everything about fishing.")),
    ("astuces", "💡", ("Codes & Astuces", "Conseils et codes Action Replay."),
                      ("Codes & Tips", "Tips and Action Replay codes.")),
]

def home_content(lang):
    i = 0 if lang == "fr" else 1
    cards = "\n".join(
        f'    <a class="sec-card" href="{slug}.html"><span class="ic">{ic}</span>'
        f'<h3>{html.escape(loc[i][0])}</h3><p>{html.escape(loc[i][1])}</p></a>'
        for slug, ic, fr_t, en_t in HOME_CARDS for loc in [(fr_t, en_t)]
    )
    if lang == "fr":
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
<div class="callout callout-warn">
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
    return f"""<div class="callout">
  <strong>Preservation site.</strong> This is a restoration of
  <em>saetta.free.fr/DigimonWorld</em>, a French fan-site that is now gone (PHP was disabled on
  Free's personal pages). The content was recovered from the
  <a href="https://web.archive.org/web/2023/http://saetta.free.fr/DigimonWorld/">Wayback Machine</a>
  and reworked. The original forum and guestbook no longer exist and have been removed.
</div>
<p><strong>Digimon World</strong> (PlayStation, 1999) is a game where you raise a Digimon, a bit like
  a Tamagotchi, to make it strong enough to help the Digimon of File Island rebuild their town. This
  guide gathers everything you need to finish it.</p>
<div class="callout callout-warn">
  <strong>Good to know:</strong> a bug present in several French releases prevents you from entering
  the Ogre Fortress (Great Canyon). Whamon and Shellmon then become unrecruitable; you can still beat
  the game, but it is harder.
</div>
<h2>Where to start</h2>
<div class="sections">
{cards}
</div>
<h2>Raising your Digimon well</h2>
<ul>
  <li>Only feed it when it asks: overfeeding, or the wrong food, can make it sick.</li>
  <li>Take it to the toilet as soon as it asks, otherwise it loses happiness and you lose discipline.</li>
  <li>Let it sleep when it asks: it then recovers all its HP and MP.</li>
  <li>Tired? Let it rest for an hour with Punimon or Centarumon in town.</li>
  <li>Hurt in battle: use a bandage quickly. Sick: a medicine, or Centarumon for 300 Bits.</li>
</ul>"""

# ---- per-language UI strings ----------------------------------------------

STRINGS = {
    "fr": {
        "html_lang": "fr",
        "skip": "Aller au contenu",
        "tagline": "— Solution &amp; Guide",
        "nav_aria": "Navigation principale",
        "tagline_plain": "Solution & Guide",
        "og_locale": "fr_FR",
        "contribute": "Contribuer sur GitHub",
        "desc": ("Solution complète et guide du jeu Digimon World (PSX) : soluce pas à pas, "
                 "arbre de digivolution, techniques, objets, magasins, médailles, pêche et codes."),
        "hero_tag": ('La solution complète et le guide du jeu <strong>Digimon World</strong> sur '
                     'PlayStation : soluce pas à pas, arbre de digivolution, techniques, objets, '
                     'magasins et astuces.'),
        "hero_cta1": "Lire la solution", "hero_cta2": "Arbre de digivolution",
        "hero_alt": "Digimon World — bannière du site original de Saetta",
        "foot1": ('Fan-site dédié à <strong>Digimon World</strong> (PlayStation). Contenu original de '
                  'saetta.free.fr, récupéré depuis la '
                  '<a href="https://web.archive.org/web/2023/http://saetta.free.fr/DigimonWorld/">Wayback Machine</a>.'),
        "foot2": ("Digimon est une marque de Bandai. Site non officiel, à but informatif et de "
                  "préservation."),
    },
    "en": {
        "html_lang": "en",
        "skip": "Skip to content",
        "tagline": "— Walkthrough &amp; Guide",
        "nav_aria": "Main navigation",
        "tagline_plain": "Walkthrough & Guide",
        "og_locale": "en_GB",
        "contribute": "Contribute on GitHub",
        "desc": ("Complete walkthrough and guide for Digimon World (PSX): step-by-step solution, "
                 "digivolution tree, techniques, items, shops, medals, fishing and codes."),
        "hero_tag": ('The complete walkthrough and guide for <strong>Digimon World</strong> on '
                     'PlayStation: step-by-step solution, digivolution tree, techniques, items, '
                     'shops and tips.'),
        "hero_cta1": "Read the walkthrough", "hero_cta2": "Digivolution tree",
        "hero_alt": "Digimon World — banner from Saetta's original site",
        "foot1": ('Fan-site for <strong>Digimon World</strong> (PlayStation). Original content from '
                  'saetta.free.fr, recovered from the '
                  '<a href="https://web.archive.org/web/2023/http://saetta.free.fr/DigimonWorld/">Wayback Machine</a>.'),
        "foot2": ("Digimon is a trademark of Bandai. Unofficial site, for informational and "
                  "preservation purposes."),
    },
}

TEMPLATE = """<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Digimon World</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{site}/{lang}/{page}">
<link rel="alternate" hreflang="fr" href="{site}/fr/{page}">
<link rel="alternate" hreflang="en" href="{site}/en/{page}">
<link rel="alternate" hreflang="x-default" href="{site}/en/{page}">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Digimon World — {tagline_plain}">
<meta property="og:locale" content="{og_locale}">
<meta property="og:title" content="{title} — Digimon World">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}/{lang}/{page}">
<meta property="og:image" content="{site}/images/banton2.gif">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="../style.css">
<style>{page_styles}</style>
</head>
<body>
<a class="skip" href="#content">{skip}</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="index.html"><b>Digimon</b>&nbsp;World <span>{tagline}</span></a>
    <div class="header-right">
      <div class="lang-switch">
        <a href="../fr/{page}"{fr_active}>FR</a>
        <a href="../en/{page}"{en_active}>EN</a>
      </div>
      <button class="nav-toggle" aria-label="Menu" aria-expanded="false">☰</button>
    </div>
  </div>
</header>
<nav class="site-nav" aria-label="{nav_aria}">
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
    <p>{foot1}</p>
    <p class="muted">{foot2}</p>
    <p><a class="gh-link" href="{repo}"><svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.42 7.42 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>{contribute}</a></p>
  </div>
</footer>
<script src="../nav.js"></script>
</body>
</html>
"""

def hero(lang):
    s = STRINGS[lang]
    return f"""<section class="hero wrap" aria-label="Digimon World">
  <img src="../images/banton2.gif" width="808" height="157" alt="{s['hero_alt']}">
  <p class="tag">{s['hero_tag']}</p>
  <div class="cta">
    <a class="btn btn-primary" href="solution.html">{s['hero_cta1']}</a>
    <a class="btn btn-ghost" href="digivolution.html">{s['hero_cta2']}</a>
  </div>
</section>"""

def build_nav(lang, active_slug):
    items = []
    for raw, slug, fr_nav, en_nav, *_ in PAGES:
        label = fr_nav if lang == "fr" else en_nav
        href = ("index.html" if slug == "index" else slug + ".html")
        cls = ' class="active"' if slug == active_slug else ""
        items.append(f'    <li><a href="{href}"{cls}>{html.escape(label)}</a></li>')
    return "\n".join(items)

_ASSET_RE = re.compile(r'(src|href)="((?:id2|images|screenshots|design|css|js|Download)/[^"]*)"')
def subdir_assets(s):
    """Prefix relative asset paths with ../ for pages living in /fr or /en."""
    return _ASSET_RE.sub(r'\1="../\2"', s)

def render(lang, slug, h1, content, rules, with_hero):
    s = STRINGS[lang]
    page = ("index.html" if slug == "index" else slug + ".html")
    desc = DESCRIPTIONS[slug][0 if lang == "fr" else 1]
    out = TEMPLATE.format(
        html_lang=s["html_lang"], title=html.escape(h1), desc=html.escape(desc),
        site=SITE_URL, lang=lang, repo=REPO_URL, contribute=s["contribute"],
        tagline_plain=s["tagline_plain"], og_locale=s["og_locale"],
        page=page, skip=s["skip"], tagline=s["tagline"], nav_aria=s["nav_aria"],
        page_styles=" ".join(rules), nav=build_nav(lang, slug),
        hero=(hero(lang) if with_hero else ""),
        content=subdir_assets(enhance(content, lang, h1)),
        foot1=s["foot1"], foot2=s["foot2"],
        fr_active=(' class="active"' if lang == "fr" else ""),
        en_active=(' class="active"' if lang == "en" else ""),
    )
    d = os.path.join(OUT, lang)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, page), "w", encoding="utf-8") as f:
        f.write(out)

ROOT_LANDING = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Digimon World — Walkthrough &amp; Guide</title>
<link rel="alternate" hreflang="fr" href="fr/">
<link rel="alternate" hreflang="en" href="en/">
<link rel="alternate" hreflang="x-default" href="en/">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<script>
  var l = (navigator.language || "en").toLowerCase().indexOf("fr") === 0 ? "fr" : "en";
  location.replace(l + "/");
</script>
<style>
  body{font:16px/1.6 "Segoe UI",Arial,sans-serif;background:#0b1f3a;color:#eef3f8;
       display:flex;min-height:100vh;margin:0;align-items:center;justify-content:center;text-align:center}
  a{display:inline-block;margin:8px;padding:12px 26px;border-radius:999px;background:#ff8a1f;
    color:#1a2533;font-weight:700;text-decoration:none}
  a.alt{background:rgba(255,255,255,.12);color:#fff}
</style>
</head>
<body>
<div>
  <h1>Digimon World</h1>
  <p>Choisissez votre langue / Choose your language</p>
  <p><a href="fr/">Français</a><a class="alt" href="en/">English</a></p>
</div>
</body>
</html>
"""

NOT_FOUND = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 — Digimon World</title>
<meta name="robots" content="noindex">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<main id="content" class="wrap">
  <article class="page">
    <h1>404</h1>
    <p>Cette page n'existe pas. Elle a peut-&ecirc;tre disparu avec le site d'origine.</p>
    <p>This page does not exist. It may have gone with the original site.</p>
    <p class="cta">
      <a class="btn btn-primary" href="/fr/">Accueil</a>
      <a class="btn btn-ghost" href="/en/">Home</a>
    </p>
  </article>
</main>
</body>
</html>
"""

ROBOTS = """User-agent: *
Allow: /

Sitemap: {site}/sitemap.xml
"""


def write_site_files(missing_en):
    """Emit the files that describe the site to crawlers, plus the 404 page."""
    urls = []
    for _raw, slug, *_ in PAGES:
        page = "index.html" if slug == "index" else slug + ".html"
        for lang in LANGS:
            if lang == "en" and slug in missing_en:
                continue
            urls.append(f"{SITE_URL}/{lang}/{page}")
    body = "\n".join(
        f"  <url><loc>{html.escape(u)}</loc></url>" for u in urls)
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               f"{body}\n</urlset>\n")
    for name, text in (("sitemap.xml", sitemap),
                       ("robots.txt", ROBOTS.format(site=SITE_URL)),
                       ("404.html", NOT_FOUND)):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(text)


def main():
    os.makedirs(FRAG, exist_ok=True)
    # collect FR content + rules once, dump fragments for translation
    fr_frag, rules_by = {}, {}
    for raw, slug, fr_nav, en_nav, fr_h1, en_h1 in PAGES:
        if slug == "index":
            continue
        content, rules = fr_content(raw, slug)
        fr_frag[slug] = content
        rules_by[slug] = rules
        with open(os.path.join(FRAG, slug + ".fr.html"), "w", encoding="utf-8") as f:
            f.write(content)

    missing_en = []
    for raw, slug, fr_nav, en_nav, fr_h1, en_h1 in PAGES:
        with_hero = (slug == "index")
        # French
        fr_c = home_content("fr") if slug == "index" else fr_frag[slug]
        fr_r = [] if slug == "index" else rules_by[slug]
        render("fr", slug, fr_h1, fr_c, fr_r, with_hero)
        # English
        if slug == "index":
            render("en", slug, en_h1, home_content("en"), [], with_hero)
        else:
            ep = os.path.join(FRAG, slug + ".en.html")
            if os.path.exists(ep):
                en_c = open(ep, encoding="utf-8").read()
                render("en", slug, en_h1, en_c, rules_by[slug], with_hero)
            else:
                missing_en.append(slug)

    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(ROOT_LANDING)
    write_site_files(missing_en)

    print(f"built FR: {len(PAGES)} pages | EN: {len(PAGES)-len(missing_en)} pages")
    if missing_en:
        print("missing EN translations for:", ", ".join(missing_en))

if __name__ == "__main__":
    main()
