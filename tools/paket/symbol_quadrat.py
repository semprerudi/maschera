#!/usr/bin/env python3
"""Die Maske quadratisch in eine Datei schreiben — fuer die Bauskripte.

    python3 tools/paket/symbol_quadrat.py app/static/maske.svg ziel.svg

Die Rechnung steht in `core/symbol.py` und nicht hier: auch die Anwendung
braucht sie fuer das Zeichen im Ablagefach, und `tools/paket/` faehrt in
keiner Verpackung mit.

Wofuer es das braucht: `flatpak-validate-icon` bricht ab («Expected a
square icon but got: 1278x1506»), und ein Symbolthema zieht ein
nicht-quadratisches Bild in der Leiste breit.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.symbol import MASSE, quadratisch  # noqa: E402


def main(quelle: Path, ziel: Path) -> int:
    text = quelle.read_text(encoding="utf-8")
    treffer = MASSE.search(text)
    if not treffer:
        print(f"{quelle.name} hat keine lesbare viewBox — nichts zu tun.")
        return 1

    # ⚠️ `install -D` legt Elternverzeichnisse an, Python nicht — und das
    # Ziel ist im Flatpak-Bau ein Pfad, den es noch nicht gibt.
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(quadratisch(text), encoding="utf-8")

    b, h = float(treffer.group(3)), float(treffer.group(4))
    print(f"{ziel.name}: {b:g}x{h:g} -> {max(b, h):g}x{max(b, h):g}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            f"Aufruf: {Path(sys.argv[0]).name} <quelle.svg> <ziel.svg>")
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
