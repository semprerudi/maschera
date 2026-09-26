#!/usr/bin/env python3
"""Wo die Golddokumente liegen — eine Stelle, allgemein, und laut, wenn leer.

    python3 tests/test_goldpfad.py

Der Ort: `MASCHERA_GOLD`, sonst der Datenordner des Programms
(`core.pfade.daten("gold")`). Kein Rueckfall in den Projektbaum — dort
duerfen echte Dokumente nie liegen.

Die Pruefung fasst keine echten Golddokumente an. Sie legt sich leere
Verzeichnisse in `tempfile` an und setzt `MASCHERA_GOLD` und
`XDG_DATA_HOME` darauf. Das geht nur, weil `core/pfade.py` die Umgebung
zur AUFRUFZEIT liest.
"""
import os
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

from core import pfade  # noqa: E402

failures: list[str] = []


def check(ok, msg):
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


class Umgebung:
    """Setzt Umgebungsvariablen und stellt sie zuverlaessig zurueck."""

    def __init__(self, **neu):
        self.neu = neu

    def __enter__(self):
        self.alt = {k: os.environ.get(k) for k in self.neu}
        for k, v in self.neu.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = str(v)
        return self

    def __exit__(self, *_):
        for k, v in self.alt.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


print("1. MASCHERA_GOLD gesetzt — gilt")
with tempfile.TemporaryDirectory() as t:
    (Path(t) / "ch" / "real").mkdir(parents=True)
    with Umgebung(MASCHERA_GOLD=t):
        ort, hinweis = pfade.gold_lesen("ch", "real")
        check(ort == Path(t) / "ch" / "real",
              f"MASCHERA_GOLD nicht befolgt: {ort}")
        check(hinweis is None, "Hinweis, obwohl das Verzeichnis da ist")
        check(pfade.gold_schreiben("ch", "markup") == Path(t) / "ch" / "markup",
              "gold_schreiben folgt MASCHERA_GOLD nicht")
print("   OK   MASCHERA_GOLD gewinnt")

print("\n2. Ohne Variable: der Datenordner des Programms")
with tempfile.TemporaryDirectory() as t:
    with Umgebung(MASCHERA_GOLD=None, XDG_DATA_HOME=t):
        ort, _ = pfade.gold_lesen("ch", "real")
        erwartet = Path(t) / "maschera" / "gold" / "ch" / "real"
        check(ort == erwartet, f"Vorgabeort ist {ort}, erwartet {erwartet}")
        check(ort.parent.parent == pfade.daten("gold"),
              "der Vorgabeort ist nicht `daten(\"gold\")`")
print("   OK   XDG_DATA_HOME/maschera/gold")

print("\n3. Ein leerer Ort meldet sich")
# Eine Messung ueber ein leeres Verzeichnis meldete sonst «0 Lecks».
with tempfile.TemporaryDirectory() as t:
    with Umgebung(MASCHERA_GOLD=t):
        for art in ("real", "markup"):
            _, hinweis = pfade.gold_lesen("ch", art)
            check(bool(hinweis) and "MASCHERA_GOLD" in hinweis,
                  f"leerer Ort fuer {art} bleibt still oder nennt die "
                  "Variable nicht")
print("   OK   Hinweis mit Pfad und Variable")

print("\n4. Nie im Projektbaum")
for gold in (None, "/tmp/irgendwo"):
    with tempfile.TemporaryDirectory() as t:
        with Umgebung(MASCHERA_GOLD=gold, XDG_DATA_HOME=t):
            for art in ("real", "markup"):
                for fn in (pfade.gold_lesen, pfade.gold_schreiben):
                    ort = fn("ch", art)
                    ort = ort[0] if isinstance(ort, tuple) else ort
                    check(WURZEL not in ort.parents,
                          f"{fn.__name__}({art}) zeigt in den Projektbaum: "
                          f"{ort}")
print("   OK   weder lesen noch schreiben im Projektbaum")

print("\n5. Unbekannte Art wird abgelehnt, nicht stillschweigend gebaut")
for art in ("rael", "", "synthetic"):
    for fn in (pfade.gold_lesen, pfade.gold_schreiben):
        try:
            fn("ch", art)
            check(False, f"{fn.__name__}('ch', {art!r}) haette abbrechen "
                         f"muessen")
        except ValueError:
            pass
print("   OK   nur 'real' und 'markup'")

print("\n6. Der Pfad steht nur an EINER Stelle")
# Die Werkzeuge holen den Ort aus `core.pfade` und bauen ihn nicht selbst.
# Die Wache liest den Quelltext und kann Kommentar nicht von Code
# unterscheiden — gewollt: so bleibt der Weg ueber `core.pfade` der bequeme.
WERKZEUGE = ("eval_documents.py", "gold_from_markup.py",
             "kalibriere_schwellen.py", "hole_musterbriefe.py",
             "streuung.py")
vorher = len(failures)
for name in WERKZEUGE:
    quelle = (WURZEL / "tools" / name).read_text(encoding="utf-8")
    for muster in ('"packs" / "ch"', '"eval" / "real"', '"eval" / "markup"',
                   '"ch" / "eval"', '"maschera-gold"', 'MASCHERA_GOLD")'):
        check(muster not in quelle,
              f"tools/{name} baut den Goldpfad selbst ({muster}) — "
              f"core.pfade.gold_lesen()/gold_schreiben() benutzen")
if len(failures) == vorher:
    print(f"   OK   {len(WERKZEUGE)} Werkzeuge, keines baut den Pfad selbst")

print("\n7. Kein Ordneraufbau eines Rechners im Aufloeser")
quelle = (WURZEL / "core" / "pfade.py").read_text(encoding="utf-8")
for muster in ("/home/", '"daten"', "maschera-gold"):
    check(muster not in quelle,
          f"core/pfade.py enthaelt {muster!r} — ein Ort, den es nur auf "
          "einer bestimmten Maschine gibt")
print("   OK   nur MASCHERA_GOLD und der Datenordner nach Plattform-Norm")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("BESTANDEN — Goldpfad allgemein, eine Stelle, laut wenn leer")
