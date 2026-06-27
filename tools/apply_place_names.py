#!/usr/bin/env python3
"""Replace the French fan-site place names left in the English fragments with the
official Digimon World (1999 PSX) English area names.

Verified against the in-game area lists on Grindosaur, GameFAQs and Neoseeker
(not literal translations — the actual names the English release uses). Run once
to normalize sources/fragments/*.en.html; the corrected fragments are then the
source of truth for the English build.
"""
import os
import re
import glob

FRAG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "sources", "fragments")

# Ordered longest-first so multi-word names are replaced before their substrings.
# French (fan-site) -> official English (PSX release).
REPLACEMENTS = [
    ("Pied du Mont Panorama", "foot of Mount Panorama"),
    ("Grotte secrète de la plage", "Secret Beach Cave"),
    ("Forteresse d'Ogremon", "Ogre Fortress"),
    ("Forteresse des Ogres", "Ogre Fortress"),
    ("Manoir de Lord Grey", "Grey Lord's Mansion"),
    ("Clairière de Kunemon", "Kunemon's Bed"),
    ("Sanctuaire des Glaces", "Ice Sanctuary"),
    ("Espace Temps Express", "Speedy Time Zone"),
    ("Dimension Parallèle", "Back Dimension"),
    ("Lac de Dragonnoeil", "Dragon Eye Lake"),
    ("Lac Dragonnoeil", "Dragon Eye Lake"),
    ("Bosquet des Brumes", "Misty Trees"),
    ("Pays des Scarabées", "Beetle Land"),
    ("Marais des Lézards", "Geko Swamp"),
    ("Marais des lézards", "Geko Swamp"),
    ("Bourg l'Industrie", "Factorial Town"),
    ("Bourg L'industrie", "Factorial Town"),
    ("Bourg l'Industire", "Factorial Town"),   # preserve-typo variant
    ("Bourg L'Industire", "Factorial Town"),
    ("Grotte Volcanique", "Lava Cave"),
    ("Mont Panorama", "Mount Panorama"),
    ("Mont Éternel", "Mount Infinity"),
    ("Mont Eternel", "Mount Infinity"),
    ("Forêt Amida", "Amida Forest"),
    ("La Mangrove", "the Mangrove"),
    ("LudoBourg", "Toy Town"),
    ("Ludo Bourg", "Toy Town"),   # translator split the name
    ("Digipont", "Digi Bridge"),
    ("Pays des Dinos", "Ancient Dino Region"),
    ("Grand Canyon", "Great Canyon"),
]

# Case-sensitive standalone words handled with word boundaries.
WORD_REPLACEMENTS = [
    (r"\bDécharge\b", "Trash Mountain"),
    (r"\bdécharge\b", "Trash Mountain"),
    (r"\bForteresse\b", "fortress"),   # bare references to the Ogre Fortress
]

def fix(text):
    for fr, en in REPLACEMENTS:
        text = text.replace(fr, en)
    for pat, en in WORD_REPLACEMENTS:
        text = re.sub(pat, en, text)
    # upgrade the translators' "Dino Region" to the official "Ancient Dino Region"
    text = re.sub(r"(?<!Ancient )\bDino Region\b", "Ancient Dino Region", text)
    return text

def main():
    changed = 0
    for path in sorted(glob.glob(os.path.join(FRAG, "*.en.html"))):
        before = open(path, encoding="utf-8").read()
        after = fix(before)
        if after != before:
            open(path, "w", encoding="utf-8").write(after)
            changed += 1
            print("updated", os.path.basename(path))
    print(f"{changed} fragment(s) updated")

if __name__ == "__main__":
    main()
