"""Test der Stufenzusammenfuehrung (SPEC §3, §4).

    python3 tests/test_inference.py

Ohne Modell: der Scorer ist ein Attrappen-Objekt. Genau so soll es sein — die
Zusammenfuehrung muss ohne ONNX und ohne Gewichte pruefbar bleiben.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.inference import Scored, filter_text, merge  # noqa: E402
from packs import load_pack  # noqa: E402

PACK = load_pack("ch")
failures = []


def check(c, m):
    if not c:
        failures.append(m)


class Mock:
    def __init__(self, spans): self.spans = spans
    def score(self, text): return self.spans


print("1. Schwelle aus dem Fehlerbudget")
text = "Hans Meier wohnt in Zuerich, 8001, bei der Alpin Treuhand AG."
# FULLNAME = Budget R (0.30), CITY = A (0.50), ZIPCODE = P (0.70).
#
# Ein Test, der ein Beispiel fuer eine REGEL nennt, darf keinen Tag nehmen,
# der eine Ausnahme werden kann. Deshalb ZIPCODE fuer P und ORG
# ausdruecklich als Ausnahmefall daneben.
cases = [
    ("FULLNAME", 5, 10, 0.35, True,  "R laesst 0.35 durch"),
    ("CITY",    20, 27, 0.35, False, "A verwirft 0.35"),
    ("CITY",    20, 27, 0.55, True,  "A laesst 0.55 durch"),
    ("ZIPCODE", 29, 33, 0.55, False, "P verwirft 0.55"),
    ("ZIPCODE", 29, 33, 0.75, True,  "P laesst 0.75 durch"),
]

# ⚠️ ORG kann eine Ausnahme tragen, und ihr Wert darf sich mit jeder
# Kalibrierung verschieben. Ein Tag, der eine Ausnahme werden kann, taugt
# weder als Beispiel fuer eine Regel noch als Beispiel mit FESTER ZAHL fuer
# die Ausnahme.
#
# Deshalb steht hier kein Wert, sondern der MECHANISMUS: was immer in
# `taxonomy.yaml` fuer ORG steht — knapp darunter wird verworfen, knapp
# darueber durchgelassen. Der Test ueberlebt jede Neukalibrierung und
# faellt trotzdem, wenn die Ausnahme nicht mehr greift.
org = PACK.get_thresholds()["ORG"]
check(org != PACK.get_thresholds()["ZIPCODE"],
      "ORG traegt denselben Wert wie ein gewoehnliches P-Tag — dann ist "
      "die Ausnahme wirkungslos und gehoert gestrichen")
for p_wert, want, why in ((org - 0.05, False, "knapp unter der Ausnahme"),
                          (org + 0.05, True,  "knapp ueber der Ausnahme")):
    spans, _ = merge(text, [Scored("ORG", 43, 60, p_wert)], PACK)
    got = any(s.tag == "ORG" for s in spans)
    check(got == want, f"ORG {why}: erwartet {want}, erhalten {got}")
    print(f"   {'OK  ' if got == want else 'FEHL'} {'ORG':<10} "
          f"p={p_wert:.2f}  {why} ({org:.2f})")
for tag, a, b, p, want, why in cases:
    spans, dropped = merge(text, [Scored(tag, a, b, p)], PACK)
    got = any(s.tag == tag for s in spans)
    check(got == want, f"{why}: erwartet {want}, erhalten {got}")
    print(f"   {'OK  ' if got == want else 'FEHL'} {tag:<10} p={p:.2f}  {why}")

print("\n2. Stufe-1-Override in beide Richtungen")
gut = "Versichertennummer 756.9217.0769.85"
spans, _ = merge(gut, [], PACK)   # Modell schweigt
found = [s for s in spans if s.tag == "AHVN13"]
check(len(found) == 1, "gueltige AHV-Nummer muss auch ohne Modell maskiert werden")
print(f"   OK   Modell schweigt, Pruefsumme gueltig -> maskiert")

schlecht = "Versichertennummer 756.9217.0769.86"
spans, dropped = merge(schlecht, [Scored("AHVN13", 19, 35, 0.99)], PACK)
found = [s for s in spans if s.tag == "AHVN13"]
check(not found, f"ungueltige Pruefziffer muss verworfen werden, trotz p=0.99")
check(any("Pruefsumme" in d[2] for d in dropped), f"Grund nicht vermerkt: {dropped}")
print(f"   OK   Modell sicher (p=0.99), Pruefsumme ungueltig -> verworfen")
print(f"        Grund: {dropped[0][2]!r}")

print("\n3. Stufenvorrang bei Ueberlappung")
t = "AHV 756.9217.0769.85 hier"
overlapping = [Scored("CASE_ID", 4, 20, 0.99)]
spans, _ = merge(t, overlapping, PACK)
tags = {s.tag for s in spans}
check("AHVN13" in tags and "CASE_ID" not in tags,
      f"Stufe 1 muss Stufe 2 schlagen: {tags}")
print(f"   OK   Stufe 1 (AHVN13) schlaegt Modelltreffer (CASE_ID)")

print("\n4. Vollstaendiger Durchlauf mit Attrappe")
doc = """Einwohnerdienste Bern
Sehr geehrter Herr Meier
Hans Peter Meier, von Hautemorges VD, Marktgasse 12, 3011 Bern
Versichertennummer: 756.9217.0769.85
Die Gebuehr betraegt CHF 50.00.
Meier reichte verspaetet ein."""
model = Mock([
    Scored("FULLNAME", doc.index("Hans Peter Meier"), doc.index("Hans Peter Meier")+16, 0.91),
    Scored("STREET", doc.index("Marktgasse"), doc.index("Marktgasse")+10, 0.88),
    Scored("BUILDINGNUM", doc.index("Marktgasse")+11, doc.index("Marktgasse")+13, 0.80),
    Scored("CITY", doc.index("Einwohnerdienste Bern")+17, doc.index("Einwohnerdienste Bern")+21, 0.75),
])
r = filter_text(doc, PACK, scorer=model)
print()
print(r.masked)
check("Meier" not in r.masked, "nackte Nachnamen muessen propagiert werden")
check("756.9217.0769.85" not in r.masked, "AHV-Nummer nicht maskiert")
check("Hautemorges VD" not in r.masked,
      "Heimatort muss maskiert werden")
check("Gebuehr betraegt CHF 50.00" in r.masked, "Gebuehr-Decoy faelschlich maskiert")
print(f"   {len(r.dictionary)} Woerterbucheintraege, {len(r.dropped)} verworfen")

print("\n5. Ohne Modell laeuft Stufe 1+2 weiter")
r2 = filter_text(doc, PACK, scorer=None)
check("756.9217.0769.85" not in r2.masked, "AHV-Nummer muss auch ohne Modell weg")
check("Meier" in r2.masked, "ohne Modell bleiben Namen im Klartext — erwartet")
print("   OK   AHV-Nummer maskiert, Namen bleiben (erwartet, Stufe 3 fehlt)")

# --- 6. Ein perfektes Modell darf nichts verlieren -------------------------
print("\n6. Zusammenfuehrung mit einem PERFEKTEN Modell")
print("   Gibt das Modell exakt die Wahrheit aus, darf die Zusammenfuehrung")
print("   nichts verschlucken — ein Verlust hier zeigt sich sonst erst,")
print("   wenn ein echtes Modell dieselbe Kette durchlaeuft.\n")

import collections  # noqa: E402
from core import injector as _inj  # noqa: E402
from core.injector import generate  # noqa: E402

# ⚠️⚠️ DIESER PUNKT BRAUCHT DIE GEBAUTE NOMENKLATUR. Ohne
# `packs/ch/nomenclatures/dist/` greift der Notvorrat im Injektor, und der
# ist ein paar Dutzend Werte gross: dieselben Namen stehen dann in jedem
# zweiten Dokument, geraten nebeneinander und ergeben Spannen, die es mit
# echten Daten nicht gibt. Der Punkt meldete dann einen Verlust, der
# keiner ist.
#
# ⚠️ Das ist KEINE Entwarnung, und es wird auch nicht als eine
# geschrieben. Ohne Nomenklatur ist die Zusammenfuehrung hier NICHT
# geprueft — der Satz sagt das.
#
# ⚠️ Die Marke `UEBERSPRUNGEN` traegt er trotzdem nicht: sie meldete dem
# Laeufer die GANZE Datei als ausgelassen, und die uebrigen Punkte laufen.
if not _inj._nomenclatures():
    print("   —    keine Nomenklatur gebaut "
          "(packs/ch/nomenclatures/dist/) — die Zusammenfuehrung ist an "
          "erfundenen Dokumenten HIER NICHT geprueft.")
    print("        `python3 packs/ch/nomenclatures/build.py` baut sie.")
    _ueberspringen_6 = True
else:
    _ueberspringen_6 = False

# ⚠️⚠️ DREI TOEPFE, NICHT ZWEI.
#
# «Deckungsgleich, anderes Tag» ist kein Leck. Ebensowenig dies:
#
#     Gold      ORG  "Office de l'état civil"
#     Ausgabe   ORG  "Office de l'état civil has"
#
# Gleiches Tag, Aktion `mask`, die Goldspanne liegt VOLLSTAENDIG darin —
# es leckt nichts, die Grenze ist nur um ein Wort gewandert. Das ist eine
# Uebermaskierung, und «Uebermaskierung ≠ Leck».
#
# ⚠️ DIE STRENGE BLEIBT. Die Ausweitung zaehlt weiter als Fehlschlag — sie
# bekommt nur einen eigenen Namen und eine eigene Meldung. Faengt `merge`
# eines Tages an, Spannen um ein Wort zu verbreitern, soll die Meldung
# nicht «verliert Spannen» lauten und den Naechsten auf die Suche nach
# einem Leck schicken, das es nicht gibt. Eine Wache, die rot steht und das
# Falsche sagt, kostet dieselbe Runde wie eine, die gruen ist und nichts
# prueft.
ACTIONS = PACK.get_actions()
echt = collections.Counter()
umetikettiert = collections.Counter()
ausgeweitet = collections.Counter()
gesamt = 0
for e in ([] if _ueberspringen_6 else generate(400, seed=999)):
    gesamt += len(e.spans)
    final, _ = merge(e.text, [Scored(s.tag, s.start, s.end, 1.0) for s in e.spans],
                     PACK)
    fertig = {(s.tag, s.start, s.end) for s in final}
    for s in e.spans:
        if (s.tag, s.start, s.end) in fertig:
            continue
        ueber = [x for x in final if x.start < s.end and s.start < x.end]
        gleiche_spanne = (ueber and ueber[0].start == s.start
                          and ueber[0].end == s.end
                          and ACTIONS.get(ueber[0].tag) == "mask")
        # ⚠️ Ueber ALLE Spannen der Ausgabe, nicht nur ueber `ueber[0]`.
        # Welche zuerst kommt, entscheidet die Sortierung; ob der Wert
        # maskiert ist, entscheidet die Ueberdeckung.
        ueberdeckt = any(x.start <= s.start and s.end <= x.end
                         and ACTIONS.get(x.tag) == "mask" for x in final)
        if gleiche_spanne:
            # Identische Spanne, anderes maskiertes Tag: kein Leck. "KL-2023-4471"
            # sieht aus wie eine Dossiernummer, und beide Tags maskieren.
            umetikettiert[(s.tag, ueber[0].tag)] += 1
        elif ueberdeckt:
            # Vollstaendig ueberdeckt, aber nicht deckungsgleich: der Wert
            # ist maskiert, die Grenze ist gewandert.
            ausgeweitet[s.tag] += 1
        else:
            echt[s.tag] += 1

if not _ueberspringen_6:
    check(not echt, f"Zusammenfuehrung verliert Spannen — der Wert steht "
                    f"unmaskiert da: {dict(echt)}")
    # ⚠️ EIGENE Meldung, nicht dieselbe. Sie sagt, was zu suchen ist:
    # nicht ein Leck, sondern eine gewanderte Grenze.
    check(not ausgeweitet,
          f"Zusammenfuehrung weitet Spannen aus — kein Leck, der Wert "
          f"bleibt maskiert, aber die Grenzen wandern und der Platzhalter "
          f"frisst Nachbartext: {dict(ausgeweitet)}")
    _rot = echt or ausgeweitet
    print(f"   {'FEHL' if _rot else 'OK  '} {gesamt} Spannen, "
          f"{sum(echt.values())} echte Verluste, "
          f"{sum(ausgeweitet.values())} ausgeweitet")
    print(f"        {sum(umetikettiert.values())} nur umetikettiert bei "
          f"gleicher Spanne (kein Leck): {dict(umetikettiert) or 'keine'}")

# --- Fensterzahl: angesagt == wirklich gelaufen -----------------------------
# ⚠️ Die Ansage darf nicht `ceil(token / step)` sein: die Schleife bricht
# ab, sobald ein Fenster bis ans Ende reicht, und laeuft deshalb seltener.
# Der Fortschrittsbalken sagte sonst «Fenster 63 von 62».
#
# Ein Balken, der ueber 100 % hinauslaeuft, sagt dem Anwender genau eines:
# dass hier niemand zaehlt. Und er ist die einzige Rueckmeldung waehrend
# eines Laufs, der Minuten dauern kann.
from core.inference import fensterzahl  # noqa: E402


def _wirklich(token: int, nutz: int, step: int) -> int:
    """Die Schleife aus beiden Laeufern, nachgebaut — nur gezaehlt."""
    z = 0
    for begin in range(0, max(1, token), step):
        if token and begin >= token:
            break
        z += 1
        if begin + nutz >= token:
            break
    return z


_daneben = []
for _nutz, _step in ((510, 382), (510, 128), (254, 190), (126, 64)):
    for _n in list(range(0, 2500)) + [11701, 23401, 24000, 46801, 93601]:
        if fensterzahl(_n, _nutz, _step) != _wirklich(_n, _nutz, _step):
            _daneben.append((_n, _nutz, _step))
check(not _daneben,
      f"{len(_daneben)} Faelle, in denen die Ansage nicht der Schleife "
      f"entspricht, z. B. {_daneben[:3]}")
print(f"   {'OK  ' if not _daneben else 'FEHL'} Fensterzahl: Ansage == "
      f"Schleife in 4 Zuschnitten")

# --- Zwei Koepfe (seit 25.11.2026) --------------------------------------------
# Ein Modell mit angehaengten Labels (`train.py --nur-kopf`) traegt `kopf_alt`.
# Die alten Labels entscheiden dann nur untereinander: ihr Ergebnis muss genau
# das eines Modells sein, das nur die alten Zeilen hat. Die neuen kommen in
# einem zweiten Pass dazu und duerfen nur O oder ein neues Label sein.
print("\nZ. Zwei Koepfe: alte Labels wie das Ausgangsmodell, neue nur dazu")
import numpy as _np  # noqa: E402
from core.inference import kopf_paesse  # noqa: E402
_rng = _np.random.default_rng(7)
_logits = _rng.normal(size=(50, 95)) * 4
_alt_allein = kopf_paesse(_logits[:, :91], None)[0]
_zwei = kopf_paesse(_logits, 91)
check(len(_zwei) == 2, "mit kopf_alt muessen es zwei Paesse sein")
check(bool((_zwei[0][0] == _alt_allein[0]).all())
      and _np.allclose(_zwei[0][1], _alt_allein[1]),
      "Pass alt weicht vom Modell mit nur den alten Zeilen ab")
check(set(_zwei[1][0].tolist()) <= {0, 91, 92, 93, 94},
      "Pass neu liefert ein altes Label")
check(len(kopf_paesse(_logits, None)) == 1, "ohne kopf_alt ein Pass")
print("   OK   Pass alt == Ausgangsmodell, Pass neu nur O und neue Labels"
      if not failures else "   FEHL siehe oben")

print("\nZ2. Zerstueckelte Titel werden eine Spanne, Namen und Orte nicht")
from core.inference import Scored as _Sc, _zusammenfuegen  # noqa: E402
_t = "il consigliere federale Rossi, Bern Zürich\nMutter\nVater"
_r = _zusammenfuegen([_Sc("JOBTITLE", 3, 14, .9), _Sc("JOBTITLE", 15, 23, .7),
                      _Sc("CITY", 31, 35, .9), _Sc("CITY", 36, 42, .9),
                      _Sc("FAMILYROLE", 43, 49, .9),
                      _Sc("FAMILYROLE", 50, 55, .9)], _t)
_w = [(x.tag, _t[x.start:x.end]) for x in _r]
check(("JOBTITLE", "consigliere federale") in _w,
      f"Titelteile nicht zusammengefuegt: {_w}")
check(("CITY", "Bern") in _w and ("CITY", "Zürich") in _w,
      f"Orte zusammengefuegt: {_w}")
check(("FAMILYROLE", "Mutter") in _w and ("FAMILYROLE", "Vater") in _w,
      f"ueber einen Zeilenumbruch zusammengefuegt: {_w}")
print("   OK   ein Titel, zwei Orte, keine Verbindung ueber die Zeile"
      if not failures else "   FEHL siehe oben")

print("\nZ3. Satzzeichen am Rand von JOBTITLE/FAMILYROLE fallen weg, alte Tags bleiben")
from core.inference import _rand_saeubern  # noqa: E402
_vorher = len(failures)
_t = "Stand (EGBA) -/UID, avv. Rossi, Leiter (a. i.); Mutter: (Bern) -/"
def _st(teil, tag="JOBTITLE"):
    i = _t.index(teil)
    return _Sc(tag, i, i + len(teil), .9)
_r = _rand_saeubern([_st("(EGBA)"), _st("-/UID,"), _st("avv."),
                     _st("Leiter (a. i.);"), _st("Mutter:", "FAMILYROLE"),
                     _st("(Bern)", "CITY"), _st("-/")], _t)
_w = [(x.tag, _t[x.start:x.end]) for x in _r]
check(("JOBTITLE", "EGBA") in _w, f"Klammern nicht abgeschnitten: {_w}")
check(("JOBTITLE", "UID") in _w, f"«-/» und Komma nicht abgeschnitten: {_w}")
check(("JOBTITLE", "avv.") in _w, f"Abkuerzungspunkt abgeschnitten: {_w}")
check(("JOBTITLE", "Leiter (a. i.)") in _w, f"eigene Klammer abgeschnitten: {_w}")
check(("FAMILYROLE", "Mutter") in _w, f"Doppelpunkt nicht abgeschnitten: {_w}")
check(("CITY", "(Bern)") in _w, f"altes Tag veraendert: {_w}")
check(not any(v == "-/" or v == "" for _, v in _w), f"Spanne ohne Buchstaben blieb: {_w}")
import inspect as _insp  # noqa: E402
from core.inference import spannen_aus_paessen as _sap  # noqa: E402
check("_rand_saeubern(" in _insp.getsource(_sap),
      "spannen_aus_paessen saeubert die Raender nicht (beide Laeufer gehen dort durch)")
print("   OK   EGBA, UID, avv., Leiter (a. i.), Mutter; CITY unveraendert, «-/» weg"
      if len(failures) == _vorher else "   FEHL siehe oben")

print("\nZ4. Alte Tags gewinnen gegen JOBTITLE/FAMILYROLE, auch gegen laengere Spannen")
# Die Zusage aus CHANGELOG und specs/06: die angehaengten Tags maskieren nur
# zusaetzlich. Ohne den Nachrang verdraengte eine lange FAMILYROLE-Spanne
# eine richtige Strasse (Befund 25.11.2026).
_vorher = len(failures)
_t = "Die Mutter wohnt an der Lindenstrasse in Bern."
_i, _j = _t.index("Lindenstrasse"), _t.index("Lindenstrasse") + len("Lindenstrasse")
_m = _t.index("Mutter")
spans, _ = merge(_t, [Scored("STREET", _i, _j, 0.95),
                      Scored("FAMILYROLE", _m, _j, 0.99),
                      Scored("JOBTITLE", _i - 4, _j + 3, 0.99)], PACK)
_w = [(x.tag, _t[x.start:x.end]) for x in spans]
check(("STREET", "Lindenstrasse") in _w,
      f"die laengere neue Spanne verdraengt die Strasse: {_w}")
check(not any(tg in ("FAMILYROLE", "JOBTITLE") for tg, _ in _w),
      f"eine ueberlappende neue Spanne blieb neben der alten stehen: {_w}")
print("   OK   STREET bleibt, die laengeren FAMILYROLE/JOBTITLE fallen weg"
      if len(failures) == _vorher else "   FEHL siehe oben")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures: print(f"  - {f}")
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
