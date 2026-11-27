#!/usr/bin/env python3
"""Ein gebautes Paket maskiert die Referenztexte wie abgelegt.

    python3 tools/paket/referenz_pruefen.py --anlegen http://127.0.0.1:4197
    python3 tools/paket/referenz_pruefen.py http://127.0.0.1:4141

Je Sprache (de, fr, it, en) ein erfundener Brief aus `tools/onnx_vergleich.py`
geht ueber `/api/anonymisieren`; das Ergebnis muss Zeichen fuer Zeichen der
Referenz in `tests/referenz_mac/referenz.json` gleichen. Angelegt wird die
Referenz mit dem torch-Weg; der Workflow prueft beide Mac-Pakete dagegen,
also auch das Intel-Paket, das mit onnxruntime rechnet (seit 23.11.2026).

Nur die kurzen Briefe: in ihnen liegt kein Vertrauenswert naeher als 0,05 an
seiner Schwelle, eine Rechenabweichung zwischen zwei Prozessoren kann das
Ergebnis also nicht kippen. Die langen Texte prueft `onnx_vergleich.py`.

Nur Standardbibliothek: es laeuft auch neben einem eingefrorenen Paket.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WURZEL / "tools"))
from onnx_vergleich import TEXTE  # noqa: E402

REFERENZ = WURZEL / "tests" / "referenz_mac" / "referenz.json"


def maskiere(adresse: str, text: str, sprache: str) -> str:
    anfrage = urllib.request.Request(
        adresse.rstrip("/") + "/api/anonymisieren",
        data=json.dumps({"text": text, "sprache": sprache}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(anfrage, timeout=300) as r:
        return json.load(r)["maskiert"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("adresse")
    ap.add_argument("--anlegen", action="store_true")
    a = ap.parse_args()
    ergebnis = {s: maskiere(a.adresse, t, s) for s, t in TEXTE.items()}
    if a.anlegen:
        # Die Referenz gehoert zu EINEM Modell. `tests/test_modell.py` Punkt 13
        # vergleicht den Namen mit `packs/ch/modell.json`: beim Wechsel auf
        # ch-v71f fiel die alte Referenz erst im Release-Lauf auf GitHub auf.
        modell = json.loads((WURZEL / "packs" / "ch" / "modell.json")
                            .read_text(encoding="utf-8"))["name"]
        ergebnis = {"_modell": modell, **ergebnis}
        REFERENZ.parent.mkdir(parents=True, exist_ok=True)
        REFERENZ.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1)
                            + "\n", encoding="utf-8")
        print(f"Angelegt: {REFERENZ.relative_to(WURZEL)}")
        return 0
    soll = json.loads(REFERENZ.read_text(encoding="utf-8"))
    fehler = 0
    for sprache, text in ergebnis.items():
        if text == soll.get(sprache):
            print(f"   OK   {sprache}")
        else:
            fehler += 1
            print(f"   FEHL {sprache}\n      soll: {soll.get(sprache)!r}\n      ist:  {text!r}")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
