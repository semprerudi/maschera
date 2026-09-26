"""Vertrauensaufloesung: `Mitschreiber.vertrauen_zu`.

Haelt drei Fehlerarten fest:

  1. Ausgedehnte Modellspannen verlieren ihren Wert. `auf_wortgrenzen`
     verschiebt die Koordinaten, BEVOR zusammengefuehrt wird; danach passt
     der Schluessel `(tag, start, end)` nicht mehr. Betroffen waeren
     ausgerechnet die ausgedehnten, also die unsicheren.

  2. Regex-Treffer erben eine Modellzahl. Finden Regex und Modell dieselbe
     Spanne, trifft der Schluessel zufaellig. `vertrauen` ist laut
     `docs/API_OBERFLAECHE.md` bei `regex` und `propagation` null.

  3. Zwei Wege zu derselben Zahl. Bericht und API muessen dieselbe
     Aufloesung benutzen, sonst laufen sie auseinander.

⚠️ **Ohne Modell.** Der `Mitschreiber` wird mit einer Attrappe gefuellt; das
Verhalten haengt nur an der Buchfuehrung, nicht am Checkpoint. Deshalb laeuft
diese Pruefung auf jeder Maschine, auch ohne CUDA.
"""
import sys
from dataclasses import dataclass
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))

from filter_document import Mitschreiber  # noqa: E402

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


@dataclass
class Roh:
    """Was ein Scorer liefert."""
    tag: str
    start: int
    end: int
    score: float


@dataclass
class Fund:
    """Was nach dem Zusammenfuehren ankommt."""
    tag: str
    start: int
    end: int
    source: str


class Attrappe:
    def __init__(self, roh):
        self._roh = roh

    def score(self, text):
        return self._roh


def mitschreiber(*roh) -> Mitschreiber:
    m = Mitschreiber(Attrappe(list(roh)))
    m.score("egal")
    return m


print("1. Exakter Treffer kommt unveraendert durch")
m = mitschreiber(Roh("FULLNAME", 10, 19, 0.94))
check(m.vertrauen_zu(Fund("FULLNAME", 10, 19, "model")) == 0.94,
      "exakter Schluessel liefert nicht den abgelegten Wert")
print("   OK   0.94")

print("2. Ausgedehnte Spanne behaelt ihren Wert")
# `auf_wortgrenzen` hat 10..19 auf 8..22 gezogen. Vor der Korrektur kam die
# Fundstelle mit None an — und eine Modellvermutung bei 0.31 sah in der
# Oberflaeche aus wie eine Pruefsumme.
m = mitschreiber(Roh("ORG", 10, 19, 0.31))
v = m.vertrauen_zu(Fund("ORG", 8, 22, "model"))
check(v == 0.31, f"ausgedehnte Modellspanne kommt mit {v!r} statt 0.31 an")
print("   OK   0.31 trotz verschobener Koordinaten")

print("3. Bei mehreren ueberlappenden gilt die unsicherste")
# Die Ausdehnung hat Zeichen dazugenommen, ueber die das Modell nichts gesagt
# hat. Die Anzeige darf nicht sicherer wirken als der Befund.
m = mitschreiber(Roh("FULLNAME", 10, 15, 0.97),
                 Roh("FULLNAME", 16, 21, 0.42))
v = m.vertrauen_zu(Fund("FULLNAME", 10, 21, "model"))
check(v == 0.42, f"nimmt {v!r} statt der unsichersten 0.42")
print("   OK   0.42")

print("4. Regex erbt keine Modellzahl")
# Derselbe Bereich, zufaellig gleiche Koordinaten. Vor der Korrektur stand an
# einem deterministischen Treffer eine Modellzahl.
m = mitschreiber(Roh("IBAN", 40, 61, 0.88))
v = m.vertrauen_zu(Fund("IBAN", 40, 61, "regex"))
check(v is None, f"regex-Fundstelle traegt {v!r} statt None")
v = m.vertrauen_zu(Fund("IBAN", 40, 61, "checksum"))
check(v is None, f"checksum-Fundstelle traegt {v!r} statt None")
v = m.vertrauen_zu(Fund("IBAN", 40, 61, "propagation"))
check(v is None, f"propagation-Fundstelle traegt {v!r} statt None")
v = m.vertrauen_zu(Fund("IBAN", 40, 61, "rule"))
check(v is None, f"rule-Fundstelle traegt {v!r} statt None")
print("   OK   regex, checksum, propagation, rule alle None")

print("5. Fremdes Tag am selben Ort faerbt nicht ab")
m = mitschreiber(Roh("GIVENNAME", 10, 19, 0.77))
v = m.vertrauen_zu(Fund("FULLNAME", 10, 19, "model"))
check(v is None, f"FULLNAME uebernimmt {v!r} von GIVENNAME")
print("   OK   None")

print("6. Beruehrung ohne Ueberlappung zaehlt nicht")
# 10..19 und 19..25 grenzen aneinander, teilen aber kein Zeichen.
m = mitschreiber(Roh("ORG", 10, 19, 0.55))
v = m.vertrauen_zu(Fund("ORG", 19, 25, "model"))
check(v is None, f"angrenzende Spanne uebernimmt {v!r}")
print("   OK   None")

print("7. Kein Wert vorhanden — kein Absturz")
m = mitschreiber()
check(m.vertrauen_zu(Fund("ORG", 0, 5, "model")) is None,
      "leerer Mitschreiber liefert nicht None")
print("   OK   None")

print("8. Bericht und API benutzen dieselbe Aufloesung")
# ⚠️ Der eigentliche Punkt. Die Korrektur lag ab dem 15.8. als eigene Fassung
# in `serve.py`, waehrend `filter_document.py` weiter roh nachschlug. Wer eine
# zweite Kopie anlegt, laesst beide wieder auseinander laufen.
quelle = (WURZEL / "app" / "serve.py").read_text(encoding="utf-8")
check("roh_vertrauen.get(" not in quelle,
      "serve.py loest den Schluessel wieder selbst auf statt ueber "
      "Mitschreiber.vertrauen_zu")
check("z.scorer.vertrauen_zu(" in quelle,
      "serve.py ruft Mitschreiber.vertrauen_zu nicht auf")
bericht = (WURZEL / "tools" / "filter_document.py").read_text(encoding="utf-8")
check("vertrauen.get((s.tag, s.start, s.end))" not in bericht,
      "filter_document.py schlaegt wieder roh nach")
check("scorer.vertrauen_zu(s)" in bericht,
      "filter_document.py ruft Mitschreiber.vertrauen_zu nicht auf")
print("   OK   eine Stelle, zwei Aufrufer")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Vertrauensaufloesung in Ordnung.")
