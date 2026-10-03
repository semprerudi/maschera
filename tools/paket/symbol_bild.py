#!/usr/bin/env python3
"""Die Maske mit einem Ziehrahmen unten rechts — das Symbol fuer «Bilder».

    python3 tools/paket/symbol_bild.py app/static/maske.svg ziel.svg

Die Maske liegt quadratisch auf der Flaeche (`core/symbol.py`), darueber
ein gestrichelter Rahmen mit vier Ecken in der unteren rechten Ecke — wie
das Auswahlfenster eines Bildschirmfotos. Alle Masse folgen aus der
Kantenlaenge der Flaeche, nicht aus festen Zahlen: wird die Maske
nachgezeichnet, passt der Rahmen mit.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.symbol import MASSE, quadratisch  # noqa: E402

BLAU = "#2f80ed"


def rahmen(x: float, y: float, kante: float) -> str:
    """Das Auswahlfenster: Flaeche, gestrichelte Kante, vier Ecken."""
    seite = kante * 0.46
    links = x + kante - seite - kante * 0.04
    oben = y + kante - seite - kante * 0.04
    strich = kante * 0.028
    ecke = kante * 0.075
    ecken = "".join(
        f'<rect x="{px - ecke / 2:g}" y="{py - ecke / 2:g}" '
        f'width="{ecke:g}" height="{ecke:g}" fill="#ffffff" '
        f'stroke="{BLAU}" stroke-width="{strich * 0.8:g}"/>'
        for px in (links, links + seite) for py in (oben, oben + seite))
    return (
        '<g id="ziehrahmen">'
        f'<rect x="{links:g}" y="{oben:g}" width="{seite:g}" '
        f'height="{seite:g}" fill="#ffffff" fill-opacity="0.55"/>'
        f'<rect x="{links:g}" y="{oben:g}" width="{seite:g}" '
        f'height="{seite:g}" fill="none" stroke="{BLAU}" '
        f'stroke-width="{strich:g}" '
        f'stroke-dasharray="{strich * 2.6:g} {strich * 1.6:g}"/>'
        f'{ecken}</g>')


def main(quelle: Path, ziel: Path) -> int:
    text = quelle.read_text(encoding="utf-8")
    quadrat = quadratisch(text)
    treffer = MASSE.search(quadrat)
    if not treffer or "</svg>" not in quadrat:
        print(f"{quelle.name} hat keine lesbare viewBox — nichts zu tun.")
        return 1
    x, y, kante = (float(treffer.group(i)) for i in (1, 2, 3))
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(
        quadrat.replace("</svg>", rahmen(x, y, kante) + "</svg>"),
        encoding="utf-8")
    print(f"{ziel.name}: {kante:g}x{kante:g} mit Ziehrahmen")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            f"Aufruf: {Path(sys.argv[0]).name} <quelle.svg> <ziel.svg>")
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
