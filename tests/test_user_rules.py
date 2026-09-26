#!/usr/bin/env python3
"""Eigene Regeln des Anwenders — Schritt 11."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import user_rules
from core.inference import filter_text
from packs import load_pack

failures: list[str] = []
def check(ok, msg):
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")

pack = load_pack("ch")
print("1. Etikett, Wortliste, Kollisionen")

# ⚠️ ENGLISCHE Schluessel — und das ist der Punkt dieser Pruefung. Die
# deutschen werden weiter gelesen; eine Pruefung, die auf ihnen fuhre,
# bliebe gruen und pruefte den Rueckfall statt des Formats.
YAML = """
version: 1
rules:
  - id: dossier
    name: Dossier number
    placeholder: Dossier
    type: label
    labels: ["Dossier-Nr.", "Dossier Nr."]
    value_form: digits_grouped
    min: 6
    max: 16
  - id: projekte
    placeholder: Projekt
    type: wordlist
    words: ["Seerose", "Nordwind"]
"""

def schreibe(inhalt):
    f = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False,
                                    encoding="utf-8")
    f.write(inhalt); f.close()
    return f.name

regeln = user_rules.lade(schreibe(YAML), pack)
check(len(regeln) == 2, f"2 Regeln erwartet, {len(regeln)}")

TEXT = ("Betreffend Dossier Nr. 19 047 789 laeuft das Projekt Seerose.\n"
        "Die Dossier-Nr. 12 345 678 wurde korrigiert.\n"
        "Die Gebuehr betraegt CHF 50.00.")
e = filter_text(TEXT, pack, None, rules=regeln)
check("[Dossier_1]" in e.masked, "Dossiernummer nicht maskiert")
check("[Projekt_1]" in e.masked, "Projektname nicht maskiert")
check("19 047 789" not in e.masked, "Nummer blieb im Klartext")
check("CHF 50.00" in e.masked, "Gebuehr faelschlich maskiert")
print(f"   {e.masked.splitlines()[0]}")

print("\n2. Wachen gegen Fehleingaben")
for inhalt, grund in [
    ("rules: [{id: a, type: wordlist, words: ['AG','Wil']}]",
     "zu kurze Woerter"),
    ("rules: [{id: b, type: label, labels: []}]",
     "Etikett fehlt — Wertform traefe jede Zahl"),
    ("rules: [{id: 'Gross', type: wordlist, words: ['Test']}]",
     "Kennung mit Grossbuchstaben"),
    ("rules: [{id: c, placeholder: Name, type: wordlist, words: ['Test']}]",
     "Platzhalter kollidiert mit dem Pack"),
    ("rules: [{id: d, type: regex, pattern: '(('}]",
     "ungueltiges Regex"),
]:
    try:
        user_rules.lade(schreibe(inhalt), pack)
        check(False, f"haette abbrechen muessen: {grund}")
    except SystemExit:
        print(f"   OK   abgelehnt: {grund}")

print("\n2b. Die alten deutschen Schluessel werden gelesen — aber gemeldet")
# ⚠️ Das Format ist englisch. Ein hartes Abweisen der deutschen
# Schluessel legte eine laufende Einrichtung lahm; ein stilles Annehmen
# liesse zwei Formate nebeneinander stehen. Also: lesen und sagen.
ALT = """
version: 1
regeln:
  - id: projekte
    bezeichnung: interne Projektnamen
    platzhalter: Projekt
    art: wortliste
    woerter: ["Seerose", "Nordwind"]
"""
_alt: set = set()
_r = user_rules.lade(schreibe(ALT), pack, _alt)
check(len(_r) == 1, f"die alte Datei wurde nicht gelesen: {len(_r)} Regeln")
check(_r[0].bezeichnung == "interne Projektnamen",
      f"die Bezeichnung ging verloren: {_r[0].bezeichnung!r}")
# ⚠️ Jede Umbenennung wird BEIM NAMEN genannt. Eine Warnung «irgendwas ist
# alt» zwingt den Anwender zum Suchen; die Namen stehen ohnehin schon da.
for _paar in ("regeln → rules", "bezeichnung → name", "art → type",
              "woerter → words", "platzhalter → placeholder",
              "wortliste → wordlist"):
    check(_paar in _alt, f"nicht gemeldet: {_paar} (gemeldet: {sorted(_alt)})")

# Und andersherum: eine englische Datei meldet NICHTS. Sonst stuende die
# Warnung dauerhaft da und waere nach einer Woche unsichtbar.
_sauber: set = set()
user_rules.lade(schreibe(YAML), pack, _sauber)
check(not _sauber, f"die englische Datei meldet Altlasten: {sorted(_sauber)}")
print(f"   OK   {len(_alt)} Umbenennungen gemeldet, englisch meldet nichts")

print("\n3. Benutzertags koennen nie ins Training gelangen")
# `X_<id>` steht in keiner taxonomy.yaml. Geriete ein solcher Tag je in einen
# Trainingssatz, wirft align() KeyError — lauter Fehler statt stillem
# Labelverlust. Das ist die Bauweise, keine Absicht.
#
# Den Beleg dafuer fuehrt `tests/test_alignment.py` Punkt 5: dort wirft
# `align()` auf einem unbekannten Tag wirklich `KeyError`. Hier wird
# geprueft, was hierher gehoert: dass `X_dossier` kein Tag des
# Labelvertrags ist.
tags = {t.tag for t in pack.get_tags()}
check("X_dossier" not in tags, "Benutzertag steht in der Taxonomie")
print("   OK   X_dossier ist kein Tag des Labelvertrags")

print("\n4. MASCHERA_REGELN zeigt auf die Regeln")
import os as _os
from pathlib import Path as _Path
import tempfile as _tempfile

_ordner = _tempfile.TemporaryDirectory()
_datei = _Path(_ordner.name) / "regeln.yaml"
_datei.write_text(
    "version: 1\nregeln:\n  - id: probe\n    platzhalter: Probe\n"
    "    art: wortliste\n    woerter: [\"Testfirma\"]\n",
    encoding="utf-8")

_alt = _os.environ.pop("MASCHERA_REGELN", None)
_os.environ["MASCHERA_REGELN"] = str(_datei)
try:
    _regeln = user_rules.lade(pack=pack)
    check(len(_regeln) == 1 and _regeln[0].id == "probe",
          "MASCHERA_REGELN wurde nicht gelesen — Regeln still weg")
finally:
    _os.environ.pop("MASCHERA_REGELN", None)
    if _alt is not None:
        _os.environ["MASCHERA_REGELN"] = _alt
print("   OK   MASCHERA_REGELN gelesen")

print("\n5. Eigene Regeln: Wettbewerb ueber die Laenge, keine Stufe")
# ⚠️⚠️ WAS WIRKLICH GILT: eine eigene Regel steht gleichrangig neben den
# Packmustern, und die LAENGERE Spanne gewinnt. Bei GLEICHER Laenge gewinnt
# die Regel — getragen von der Rangtabelle in `merge`, nicht von der
# Reihenfolge in einer Liste. Ein Feld `stage`, das dokumentiert ist und
# nichts bewirkt, waere ein Knopf ohne Wirkung.
from core.inference import merge as _merge, Scored as _Scored  # noqa: E402

_R5 = """
version: 1
rules:
  - id: probe
    name: Probe
    placeholder: Probe
    type: label
    labels: ["Dossier-Nr."]
    value_form: digits_grouped
    min: 6
    max: 14
"""
# ⚠️ EIN MEHRWORTIGER WERT, MIT ABSICHT. Trifft die Regel ein einziges
# Wort («123456»), zieht `auf_wortgrenzen` eine kuerzere Modellspanne darin
# («2345») VOR dem Zusammenfuehren auf das ganze Wort auf: aus «kuerzer»
# wird still «gleich lang», und der Fall prueft zweimal dasselbe.
#
# Echt kuerzer geht nur, wenn die Regel mehrere Woerter trifft: die
# Modellspanne liegt dann auf EINEM davon und bleibt kuerzer.
_t5 = "Betreff: Dossier-Nr. 19 047 789 zur Kenntnis."
_u5 = user_rules.erkenne(_t5, user_rules.lade(schreibe(_R5), pack))
check(len(_u5) == 1 and _t5[_u5[0].start:_u5[0].end] == "19 047 789",
      f"die Probe-Regel trifft nicht wie erwartet: "
      f"{[_t5[s.start:s.end] for s in _u5]}")
_w5 = _t5.index("19 047 789")
_m5 = _t5.index("047")
for _name, (_a, _b), _soll in (
        ("laenger", (_t5.index("Dossier-Nr."), _w5 + 10), "model"),
        ("gleich lang", (_w5, _w5 + 10), "benutzer"),
        ("kuerzer", (_m5, _m5 + 3), "benutzer")):
    _s5, _ = _merge(_t5, [_Scored("CASE_ID", _a, _b, 0.99)], pack,
                    user_spans=_u5)
    _ist = [s.source for s in _s5]
    check(_ist == [_soll],
          f"Modellspanne {_name}: gewonnen hat {_ist}, erwartet [{_soll!r}]")

print("\n5b. Ein altes `stage` bricht nichts — und wird gemeldet")
# ⚠️ Nicht abweisen, sonst legt eine bestehende Regeldatei ueber Nacht die
# Einrichtung lahm. Und nicht still: sonst glaubt der Anwender weiter an
# einen Vorrang, den es nie gab. Beides zusammen ist die Zusage.
for _schl in ("stage", "stufe"):
    _alt5: set = set()
    _r5b = user_rules.lade(
        schreibe(_R5.replace("    max: 14\n", f"    max: 14\n    {_schl}: 1\n")),
        pack, _alt5)
    check(len(_r5b) == 1, f"`{_schl}: 1` bricht die Regeldatei")
    check(f"{_schl} → ✕" in _alt5,
          f"`{_schl}` wird nicht gemeldet (gemeldet: {sorted(_alt5)})")
    check(_r5b and _r5b[0].recognizer.stage == 2,
          f"`{_schl}: 1` wirkt noch — die Regel hat Stufe "
          f"{_r5b[0].recognizer.stage if _r5b else '?'}")
if not failures:
    print("   OK   laenger gewinnt, gleich lang und kuerzer die Regel; "
          "`stage` gemeldet und ohne Wirkung")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("Alle Pruefungen bestanden.")
