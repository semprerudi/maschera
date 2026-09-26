"""Test von Maskierung, Propagation und Rückführung.

    python3 tests/test_masking.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.masking import Span, mask, restore  # noqa: E402
from packs import load_pack  # noqa: E402

PACK = load_pack("ch")
failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        failures.append(msg)


DOC = """Einwohnerdienste der Stadt Bern
Verfuegung vom 3. Maerz 2024

Sehr geehrter Herr Meier

Hiermit wird bestaetigt, dass Hans Peter Meier, geboren am 14.07.1978, von
Hautemorges VD, seit 1. Januar 2019 an der Marktgasse 12, 3011 Bern
angemeldet ist.

Versichertennummer: 756.9217.0769.85
Dossier: EWK-2024-00812

Meier reichte die Unterlagen verspaetet ein. Die Einsprache von Meier ist
gestuetzt auf Art. 6 Abs. 1 Bst. i RHG (SR 431.02) abzuweisen.

Sachbearbeitung: Rita Bertschi
Kopie an: Hans Peter Meier, Marktgasse 12
"""


def find(needle: str, occurrence: int = 0) -> tuple[int, int]:
    start = -1
    for _ in range(occurrence + 1):
        start = DOC.index(needle, start + 1)
    return start, start + len(needle)


# Das simuliert, was Modell und Regex liefern: NUR die Treffer mit Anrede
# oder klarem Kontext. Die nackten "Meier" sind bewusst NICHT dabei —
# genau die soll die Propagation einsammeln.
spans = [
    Span("CITY", *find("Bern", 0)),
    Span("DATE", *find("3. Maerz 2024")),
    Span("FULLNAME", *find("Hans Peter Meier", 0)),
    Span("DATE", *find("14.07.1978")),
    Span("PLACE_OF_ORIGIN", *find("Hautemorges VD")),
    Span("DATE", *find("1. Januar 2019")),
    Span("STREET", *find("Marktgasse", 0)),
    Span("BUILDINGNUM", *find("12", 0)),
    Span("ZIPCODE", *find("3011")),
    Span("CITY", *find("Bern", 1)),
    Span("AHVN13", *find("756.9217.0769.85"), source="regex"),
    Span("CASE_ID", *find("EWK-2024-00812"), source="regex"),
    Span("FULLNAME", *find("Rita Bertschi")),
]

result = mask(DOC, spans, PACK)

print("Maskierter Text")
print("-" * 68)
print(result.text)
print("-" * 68)

print("\nWoerterbuch")
for ph, val in result.dictionary.items():
    print(f"  {ph:<20} {val!r}")

# --- 1. Round-Trip -----------------------------------------------------------
back = restore(result.text, result.dictionary)
check(back == DOC, "Rueckfuehrung ist nicht zeichengenau")
print(f"\n1. Round-Trip zeichengenau: {'OK' if back == DOC else 'FEHLGESCHLAGEN'}")

# --- 1b. Jeder Platzhalter des Packs ist rueckwandelbar ----------------------
#
# Sechs Platzhalter enthalten einen UNTERSTRICH im Namensteil —
# PLACE_OF_ORIGIN, CASE_ID, PATIENT_ID, QR_REFERENCE, MUNICIPALITY_ID,
# INSURANCE_CARD. Ein Muster `[A-Za-z0-9]+` kennte keinen: der Wert bliebe
# als Platzhalter stehen, statt zurueckzukehren.
#
# Diese Pruefung geht durch ALLE Tags des Packs, nicht nur durch die des
# Beispieldokuments — sonst faellt derselbe Fehler beim naechsten neuen Tag
# erst im Betrieb auf. Und sie prueft ZEICHENGENAU; «enthaelt die
# richtigen Werte» bliebe gruen.
print("\n1b. Jeder Platzhalter des Packs passt auf PLACEHOLDER_RE")
from core.masking import PLACEHOLDER_RE  # noqa: E402

nicht_erkannt = []
for t in PACK.get_tags():
    if not t.placeholder:
        continue
    for probe in (f"[{t.placeholder}_1]", f"[{t.placeholder}_12a]"):
        if not PLACEHOLDER_RE.fullmatch(probe):
            nicht_erkannt.append(probe)
check(not nicht_erkannt,
      f"nicht rueckwandelbar: {nicht_erkannt[:5]}")

# Und die Gegenprobe: was KEIN Platzhalter ist, darf nicht passen.
for kein in ("[_1]", "[123_1]", "[FULLNAME]", "[ABC]", "[]"):
    check(not PLACEHOLDER_RE.fullmatch(kein),
          f"{kein!r} wird faelschlich als Platzhalter gelesen")
print(f"   OK   {len([t for t in PACK.get_tags() if t.placeholder])} Platzhalter, "
      "5 Gegenproben")

# --- 2. Propagation ----------------------------------------------------------
propagated = [s for s in result.spans if s.source == "propagation"]
check(len(propagated) >= 4, f"zu wenig propagiert: {len(propagated)}")
check("Meier" not in result.text, "nacktes 'Meier' steht noch im maskierten Text")
print(f"2. Propagation: {len(propagated)} zusaetzliche Spannen, "
      f"kein 'Meier' mehr im Text: {'OK' if 'Meier' not in result.text else 'FEHL'}")

# --- 3. Koreferenz -----------------------------------------------------------
name_phs = {k for k in result.dictionary if k.startswith("[FULLNAME_")}
meier = {k for k, v in result.dictionary.items() if "Meier" in v}
check(
    all(k.startswith("[FULLNAME_1") for k in meier),
    f"Meier-Varianten haben verschiedene Gruppennummern: {sorted(meier)}",
)
check("[FULLNAME_2]" in name_phs, "Rita Bertschi muesste eine eigene Nummer haben")
print(f"3. Koreferenz: Meier-Varianten {sorted(meier)}, "
      f"zweite Person {'OK' if '[FULLNAME_2]' in name_phs else 'FEHL'}")

# --- 4. Heimatort wird maskiert ---------------------------------------------
# Nicht tag_only: Wohnorte im Schweizer Ortschaftenverzeichnis tragen
# Kantonskuerzel ("Reute AR") und sind damit ununterscheidbar von
# Heimatorten — die Fehlerrichtung ist asymmetrisch.
check("Hautemorges VD" not in result.text, "Heimatort steht noch im Klartext")
check("[PLACE_OF_ORIGIN_" in result.text, "Heimatort-Platzhalter fehlt")
check("[CITY_" in result.text, "Wohnort wurde nicht maskiert")
ok4 = ("Hautemorges VD" not in result.text and "[PLACE_OF_ORIGIN_" in result.text
       and "[CITY_" in result.text)
print(f"4. Heimatort und Wohnort beide maskiert: {'OK' if ok4 else 'FEHL'}")

# --- 5. Decoys unberuehrt ----------------------------------------------------
check("Art. 6 Abs. 1 Bst. i RHG (SR 431.02)" in result.text,
      "Rechtsverweis wurde angetastet")
print("5. Rechtsverweis unberuehrt: OK")

# --- 6. Erfundener Platzhalter ----------------------------------------------
tampered = result.text.replace("[FULLNAME_2]", "[FULLNAME_99]")
soft = restore(tampered, result.dictionary)
check("[FULLNAME_99]" in soft, "unbekannter Platzhalter muesste stehen bleiben")
try:
    restore(tampered, result.dictionary, strict=True)
    check(False, "strict=True haette werfen muessen")
    strict_ok = False
except ValueError:
    strict_ok = True
print(f"6. Erfundener Platzhalter: bleibt stehen, strict wirft: "
      f"{'OK' if strict_ok else 'FEHL'}")

# --- 7. Zeilenumbruch mitten in einer Entitaet ------------------------------
wrapped = "Die Einsprache von Hans Peter\nMeier wird abgewiesen."
w_spans = [Span("FULLNAME", 19, 37)]
w_res = mask(wrapped, w_spans, PACK)
check(restore(w_res.text, w_res.dictionary) == wrapped,
      "Round-Trip ueber Zeilenumbruch fehlgeschlagen")
print(f"7. Zeilenumbruch in Entitaet: "
      f"{'OK' if restore(w_res.text, w_res.dictionary) == wrapped else 'FEHL'}")

# --- 8. Die Belegung mit `bisect` sagt dasselbe wie der Durchlauf ----------
# ⚠️ `propagate()` fragt nicht fuer jede Fundstelle ALLE bisher belegten
# Stellen ab — das waere quadratisch, bei 62 000 Zeichen ueber eine
# Milliarde Vergleiche. Statt dessen eine verschmolzene, sortierte Liste
# mit `bisect`.
#
# Der Umbau lebt von einer Annahme: verschmolzene Stellen liegen sortiert,
# also sind auch ihre ENDEN sortiert, und eine Suche genuegt. Stimmt das
# Verschmelzen nicht, greift die Suche still daneben — es kaeme kein Fehler,
# sondern eine Maskierung, die eine Stelle uebersieht. Genau die Sorte
# Fehler, die dieses Werkzeug nicht machen darf.
#
# Deshalb hier ein Nachbau der langsamen Antwort — und der Vergleich ueber
# tausend Faelle, ueberlappende Eingaben eingeschlossen.
from core.masking import Belegung  # noqa: E402
import random as _rnd  # noqa: E402

_zufall = _rnd.Random(20260830)          # fest, damit ein Fehler wiederkehrt
_abweichungen = 0
for _lauf in range(200):
    _belegt = Belegung()                  # das, was wirklich laeuft
    _alt: list[tuple[int, int]] = []      # der alte Weg, unveraendert

    def _frei_alt(a: int, b: int) -> bool:
        return not any(a < e and s < b for s, e in _alt)

    # ⚠️ Die Eingabe darf sich UEBERLAPPEN — sonst prueft der Vergleich
    # genau den Fall nicht, wegen dem verschmolzen wird.
    for _ in range(60):
        a = _zufall.randrange(0, 90)
        b = a + _zufall.randrange(1, 12)
        _belegt.belegen(a, b)
        _alt.append((a, b))
        for _ in range(6):
            x = _zufall.randrange(0, 95)
            y = x + _zufall.randrange(1, 10)
            if _belegt.frei(x, y) != _frei_alt(x, y):
                _abweichungen += 1
check(_abweichungen == 0,
      f"{_abweichungen} Abweichung(en) zwischen bisect und Durchlauf")
print(f"8. Belegung: bisect == Durchlauf in 1200 Faellen: "
      f"{'OK' if _abweichungen == 0 else 'FEHL'}")

# --- 9. Jede Nadel wird EINMAL gesucht --------------------------------------
# ⚠️ `_occurrences` laeuft mit einem regulaeren Ausdruck ueber den GANZEN
# Text. Je Fundstelle ein Seed, und derselbe Name kommt zwanzigmal vor —
# ohne Gedaechtnis suchte die Schleife tausendfach, was eine Zeile vorher
# schon gesucht wurde. Ein Woerterbuch je Nadel raeumt das weg.
#
# Diese Pruefung haelt die EIGENSCHAFT fest, nicht die Umsetzung: wer die
# Schleife wieder ohne Gedaechtnis baut, faellt hier auf — und nicht erst
# dem Anwender bei einem langen Dokument.
import core.masking as _M  # noqa: E402

_gesucht: list[str] = []
_echt = _M._occurrences


def _mitzaehlen(text, needle):
    _gesucht.append(needle)
    return _echt(text, needle)


_M._occurrences = _mitzaehlen
try:
    _text = ("Hans Meier wohnt in Bern. Meier arbeitet dort. "
             "Frau Meier ist die Schwester von Hans Meier. ") * 40
    _spans = []
    for _i in range(0, len(_text) - 10, len(_text) // 40):
        _pos = _text.find("Hans Meier", _i)
        if _pos >= 0:
            _spans.append(Span("FULLNAME", _pos, _pos + len("Hans Meier")))
    _M.propagate(_text, _spans)
finally:
    _M._occurrences = _echt

check(len(_gesucht) > 0, "propagate hat gar nicht gesucht")
check(len(_gesucht) == len(set(_gesucht)),
      f"{len(_gesucht)} Suchlaeufe fuer {len(set(_gesucht))} verschiedene "
      f"Nadeln — dieselbe Nadel wird mehrfach durch den ganzen Text gejagt")
print(f"9. Jede Nadel einmal gesucht: {len(_gesucht)} Laeufe, "
      f"{len(set(_gesucht))} Nadeln: "
      f"{'OK' if len(_gesucht) == len(set(_gesucht)) else 'FEHL'}")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)} Problem(e):")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
