#!/usr/bin/env python3
"""Die Maske auf eine quadratische Flaeche legen — ohne sie zu veraendern.

Vier Stellen machen aus `maske.svg` ein Symbol: drei Verpackungen und die
Anwendung selbst, die daraus das Zeichen im Ablagefach baut
(`app/fenster.py`). Die Rechnung steht deshalb in `core/`, das in jeder
Verpackung mitfaehrt — sonst waere das Paketsymbol richtig und das
Ablagefach verzogen.

`maske.svg` selbst bleibt, wie sie ist. Sie ist die eine Quelle fuer
Favicon, Kopfzeile, Startbildschirm und Symbol.
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
