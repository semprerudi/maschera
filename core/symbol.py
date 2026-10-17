#!/usr/bin/env python3
"""Die Maske auf eine quadratische Flaeche legen — ohne sie zu veraendern.

Vier Stellen machen aus `maske.svg` ein Symbol: drei Verpackungen und die
Anwendung selbst, die daraus das Zeichen im Ablagefach baut
(`app/fenster.py`). Die Rechnung steht deshalb in `core/`, das in jeder
Verpackung mitfaehrt — sonst waere das Paketsymbol richtig und das
Ablagefach verzogen.

`maske.svg` selbst bleibt, wie sie ist. Sie ist die eine Quelle fuer
Favicon, Kopfzeile, Startbildschirm und Symbol. Seit 17.10.2026 bekommt das
SYMBOL hier zusaetzlich einen hellen Aussenrand (`mit_rand`, `symbol`) — die
Oberflaeche nicht, die kennt das Thema und faerbt in `maske.svg` selbst um.
"""
from __future__ import annotations

import re

MASSE = re.compile(
    r'viewBox="\s*([-\d.]+)\s+([-\d.]+)\s+([\d.]+)\s+([\d.]+)\s*"')


def quadratisch(text: str) -> str:
    """Denselben Inhalt auf einer quadratischen Flaeche, mittig.

    Es wird gerechnet, nicht getippt: feste Zahlen waeren beim naechsten
    Nachzeichnen der Maske still falsch, und ein verzogenes Symbol faellt
    niemandem auf, weil es immer noch ein Symbol ist.

    Ohne lesbare `viewBox` bleibt der Text unveraendert: ein Symbol, das
    ein wenig verzogen ist, ist besser als keines.
    """
    treffer = MASSE.search(text)
    if not treffer:
        return text

    x, y, breite, hoehe = (float(g) for g in treffer.groups())
    kante = max(breite, hoehe)
    # Die Differenz je zur Haelfte auf beide Seiten: das Bild bleibt in
    # der Mitte, statt an einer Kante zu kleben.
    neu = (f'viewBox="{x - (kante - breite) / 2:g} '
           f'{y - (kante - hoehe) / 2:g} {kante:g} {kante:g}"')
    return text.replace(treffer.group(0), neu, 1)


# DER HELLE AUSSENRAND (seit 17.10.2026). Ein Symbol kennt kein Thema: dasselbe
# Bild steht in der hellen Leiste und auf dem schwarzen Startbildschirm des
# Software-Stores. Dort verschwand der dunkle Rand der Maske im Grund, und
# an der Kante blieb ein zufaelliger heller Saum. Ein BEWUSSTER schmaler
# heller Rand traegt auf beiden: auf hell faellt er nicht auf, auf dunkel
# zeichnet er den Umriss nach.
#
# Anteil an der Breite der Maske. Die Haelfte des Strichs liegt aussen, die
# innere Haelfte deckt der dunkle Rand-Pfad zu.
RAND_ANTEIL = 0.03
RAND_FARBE = "#ffffff"
_MASSSTAB = re.compile(r'scale\(\s*([-\d.]+)')


def mit_rand(text: str) -> str:
    """Die Maske mit einem schmalen hellen Aussenrand, Flaeche vergroessert.

    Ohne lesbare `viewBox` oder ohne die Flaeche `maske-flaeche` bleibt der
    Text unveraendert — eine fremde Datei bekommt keinen Strich an der
    falschen Stelle.
    """
    treffer = MASSE.search(text)
    if not treffer or 'class="maske-flaeche"' not in text:
        return text
    x, y, breite, hoehe = (float(g) for g in treffer.groups())
    rand = breite * RAND_ANTEIL
    # Die Pfade stehen in einer Gruppe mit `scale(…)` (potrace). Die
    # Strichbreite gilt in DEREN Einheiten — also durch den Massstab teilen.
    m = _MASSSTAB.search(text)
    massstab = abs(float(m.group(1))) if m else 1.0
    strich = 2 * rand / (massstab or 1.0)
    text = text.replace(
        'class="maske-flaeche"',
        f'class="maske-flaeche" stroke="{RAND_FARBE}" '
        f'stroke-width="{strich:g}" stroke-linejoin="round"', 1)
    neu = (f'viewBox="{x - rand:g} {y - rand:g} '
           f'{breite + 2 * rand:g} {hoehe + 2 * rand:g}"')
    return text.replace(treffer.group(0), neu, 1)


def symbol(text: str) -> str:
    """Das Symbol: mit hellem Rand, quadratisch. Fuer jede Stelle, an der
    aus der Maske ein Programmsymbol wird — Pakete, Ablagefach, Fenster."""
    return quadratisch(mit_rand(text))
